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
from decision import  State



# External function to call an API such as google search. it can be hard coded for the moment
async def call_external_service(text: str) -> str:
    """
    External function to process text through a service
    """
    try:
        # Example API call - replace with your actual service endpoint
        # response = requests.post(
        #     "http://your-service-endpoint/process",
        #     json={"text": text}
        # )
        # return response.json()
        print(f"Making external Call with data {text}")
        
        # Return comprehensive business data that suggests legitimacy but with some uncertainty
        return {
            "business_name": "ACME Corp",
            "address": "123 Main St, Springfield",
            "business_registration": {
                "status": "Active",
                "registration_date": "2018-03-15",
                "business_id": "BN123456789",
                "state": "Illinois"
            },
            "online_presence": {
                "website": "www.acmecorp.com",
                "social_media": ["LinkedIn", "Facebook"],
                "google_reviews": {
                    "rating": 4.2,
                    "total_reviews": 87,
                    "recent_activity": "Last review 2 weeks ago"
                }
            },
            "financial_indicators": {
                "credit_rating": "B+",
                "years_in_business": 6,
                "estimated_annual_revenue": "$2.5M - $5M"
            },
            "verification_notes": [
                "Business registration verified with state records",
                "Active online presence with regular customer engagement",
                "Moderate credit rating indicates some financial stability",
                "Limited public financial information available",
                "No major legal issues found in public records"
            ],
            "risk_factors": [
                "Relatively young business (6 years)",
                "Limited detailed financial transparency",
                "Some customer complaints about service delays"
            ]
        }
    except Exception as e:
        logging.error(f"External service error: {str(e)}")
        return {"error": str(e)}

# Add new node for external processing
async def external_service_node(state: State) -> State:
    """
    Node that calls external processing service
    """
    # Get the last message content
    # last_message = state["messages"][-1].content
    # last_message = state["messages"]
    ai_messages = [msg for msg in state["messages"] if isinstance(msg, AIMessage)]
    print(f"AI Messages to Make external call: {json.dumps([msg.content for msg in ai_messages], indent=2)}")
    
    
    # Call external service
    result = await call_external_service(ai_messages)
    
    # Create new message with processed result
    processed_message = HumanMessage(
        content=f"External Processing Results: {json.dumps(result, indent=2)}"
    )
    
    return {"messages": [processed_message]}

