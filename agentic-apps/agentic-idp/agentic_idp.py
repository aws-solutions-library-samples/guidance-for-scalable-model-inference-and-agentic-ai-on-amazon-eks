from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import SystemMessage, HumanMessage

from typing import Annotated, List
from langchain.prompts.chat import HumanMessagePromptTemplate


from typing_extensions import TypedDict

import requests 
import json
import base64

import logging

from langfuse import Langfuse
from datetime import datetime, timedelta
import os
import math
import openai

from PyPDF2 import PdfReader

from pathlib import Path

from langgraph.pregel import RetryPolicy

from doc_reader import encode_image

from exteral_service import external_service_node 
from storage import external_storage_node
from decision import external_automation_node, external_human_node, State

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()



local_public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
local_secret_key = os.getenv("LANGFUSE_SECRET_KEY")
langfuse_host = os.getenv("LANGFUSE_HOST")
if local_public_key is None or local_secret_key is None or langfuse_host is None:
    raise ValueError("Please set the LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, and LANGFUSE_HOST environment variables.")

langfuse = Langfuse(
    secret_key=local_secret_key,
    public_key=local_public_key,
    host=langfuse_host
)


generation_model_key_var = os.getenv("LLAMA_VISION_MODEL_KEY")
api_gateway_url = os.getenv("API_GATEWAY_URL")
if generation_model_key_var is None or api_gateway_url is None:
    raise ValueError("Please set the LLAMA_VISION_MODEL_KEY and API_GATEWAY_URL environment variables.")
generation_model_url = api_gateway_url
generation_model_key = generation_model_key_var

reflection_model_key_var = os.getenv("LLAMA_VISION_MODEL_KEY")
if reflection_model_key_var is None:
    raise ValueError("Please set the LLAMA_VISION_MODEL_KEY environment variable.")
reflection_model_url = api_gateway_url
reflection_model_key = reflection_model_key_var

desired_iterations = 2

reflection_model = "Qwen/QwQ-32B-AWQ"
generation_model = "vllm-server-qwen-vision"





    

# Prompt for ocr Generation
generation_llm = ChatOpenAI(model=generation_model, temperature=0.7, max_tokens=1500, api_key=generation_model_key, base_url=generation_model_url)

client = openai.OpenAI(
    api_key=generation_model_key,             # pass litellm proxy key, if you're using virtual keys
    base_url=api_gateway_url # litellm-proxy-base url
)



# Path to your image
image_path = "birth_cert.png"
base64_image = encode_image(image_path)



generation_prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content="You are an expert birth certificate verifier"),
    MessagesPlaceholder(variable_name="messages"),
    ])


# Bind the prompt to the LLM
generate_report = generation_prompt | generation_llm

async def generation_node(state: State) -> State:

    # combined_content = f"{state['messages'][0].content}\n Birth Certificate Image Content:\n {base64_image}"
    # state["messages"][0].content = combined_content    
    response = client.chat.completions.create(
        model="vllm-server-qwen-vision",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "This is my birth certificate. Extract all the fields from this image and provide the information in a structured json only format, no other text or wrapper around josn. The json will be read by machine. The fields include name, date of birth, place of birth. Make sure the output only contains JSON and nothing else. Be stricit about it."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}"
                        }
                    }
                ]
            }
        ]
    )    
    combined_content = f"{state['messages'][0].content}\n Birth Certificate Content in json:\n f{response.choices[0].message.content}"
    state["messages"][0].content = combined_content    
    
    return {"messages": [await generate_report.ainvoke(state["messages"])]}





reflection_llm = ChatOpenAI(model=reflection_model, temperature=0, max_tokens=1000, api_key=reflection_model_key, base_url=reflection_model_url)

# Prompt for Reflection
reflection_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an expert business legitimacy assessor. Based on the comprehensive business data provided, assess if this is a legitimate business. Consider factors like business registration, online presence, financial indicators, and verification notes. Return a JSON response with 'confidence_score' (0.0-1.0) and 'message' fields. For businesses with verified registration, active online presence, and positive indicators but some risk factors or limited history, use confidence scores between 0.6-0.79 to indicate legitimate but requires monitoring. Your response must be strictly JSON format only, machine parseable, with no additional text or wrappers."
        ),
        MessagesPlaceholder(variable_name="messages"),
    ]
)

# Bind the prompt to the LLM
reflect_on_report = reflection_prompt | reflection_llm

# Reflection Node
async def reflection_node(state: State) -> State:
    # Swap message roles for reflection
    cls_map = {"ai": HumanMessage, "human": AIMessage}
    print("***********************")
    print(state["messages"])
    # print("***********************")
    # print(cls_map)
    # print("***********************")
    
    translated = [state["messages"][0]] + [
        cls_map[msg.type](content=msg.content) for msg in state["messages"][1:]
    ]
    res = await reflect_on_report.ainvoke(translated)
    # Treat reflection as human feedback
    return {"messages": [HumanMessage(content=res.content)]}

# Build the graph
builder = StateGraph(State)

# Add all nodes
builder.add_node("generate", generation_node)
builder.add_node("store", external_storage_node, retry=RetryPolicy(max_attempts=3))
builder.add_node("external_process", external_service_node, retry=RetryPolicy(max_attempts=3))
builder.add_node("reflect", reflection_node)
builder.add_node("automatic_approval", external_automation_node)
builder.add_node("human_approval", external_human_node)


# Define the edges
builder.add_edge(START, "generate")
builder.add_edge("generate", "store")
builder.add_edge("store", "external_process")
builder.add_edge("external_process", "reflect")
# Add edges from approval nodes to END
builder.add_edge("automatic_approval", END)
builder.add_edge("human_approval", END)

async def route_after_reflection(state: State) -> str:
    """
    Dynamic router to decide between automatic or human approval
    based on reflection output
    """
    last_message = state["messages"][-1].content
    
    # Convert the message to lowercase for case-insensitive matching
    message_lower = last_message.lower()
    
    print("***********************")
    print(f"Message Lower is ==> {message_lower}")
    print("***********************")
    print(f"state is {state}")
    
    try:
        # Clean up the message to extract JSON
        message_lower = message_lower.replace("```json", "").replace("```", "").replace("external processing results:", "")
        
        # Handle thinking tags from qwen3-vllm model
        if "<think>" in message_lower and "</think>" in message_lower:
            # Extract content after </think>
            message_lower = message_lower.split("</think>")[-1].strip()
        
        # Try to find JSON in the message
        import re
        json_match = re.search(r'\{[^}]*"confidence_score"[^}]*\}', message_lower)
        if json_match:
            json_str = json_match.group()
            j = json.loads(json_str)
            print(f"Message is JSON {j.get('confidence_score', 0)}")
            requires_human_review = j.get("confidence_score", 0) < 0.8
        else:
            print("No JSON with confidence_score found, defaulting to human review")
            requires_human_review = True
            
    except Exception as e:
        print(f"Error parsing JSON: {e}")
        print("Message is not valid JSON, defaulting to human review")
        requires_human_review = True

    if requires_human_review:
        return "human_approval"
    else:
        return "automatic_approval"

builder.add_conditional_edges(
    "reflect",
    route_after_reflection
)


# Compile the graph with memory checkpointing
memory = MemorySaver()
graph = builder.compile(checkpointer=memory)


# from langgraph.visualize import visualize
# # Generate the visualization
# viz_graph = visualize(graph)







# Use environment variables for Langfuse configuration
os.environ["LANGFUSE_SECRET_KEY"] = local_secret_key
os.environ["LANGFUSE_HOST"] = langfuse_host
os.environ["LANGFUSE_PUBLIC_KEY"] = local_public_key

from langfuse.langchain import CallbackHandler
 
# Initialize Langfuse CallbackHandler for Langchain (tracing)
langfuse_handler = CallbackHandler()

config = {"configurable": {"thread_id": "1"}, "callbacks": [langfuse_handler]}
topic = "Plan to start working with a person. Need to verify how legitimate is this person."


async def run_agent():
    
    async for event in graph.astream(
        {
            "messages": [
                HumanMessage(content=topic)
            ],
        },
        config,
    ):
        if "generate" in event:
            print("=== Generated Report ===")
            print(event["generate"]["messages"][-1].content)
            print("\n")
        elif "reflect" in event:
            print("=== Reflection ===")
            print(event["reflect"]["messages"][-1].content)
            print("\n")

import asyncio
asyncio.run(run_agent())
