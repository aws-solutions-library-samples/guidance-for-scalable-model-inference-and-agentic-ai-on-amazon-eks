import logging
import asyncio
import os
import base64
from dotenv import load_dotenv
from strands import Agent
from strands.models.openai import OpenAIModel
from strands.tools.mcp import MCPClient
from strands.telemetry import StrandsTelemetry
from mcp.client.streamable_http import streamablehttp_client

# Load environment variables from .env file
load_dotenv()

# Configure logging for debug information
logging.getLogger("strands").setLevel(logging.INFO)
logging.basicConfig(
    format="%(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler()]
)


def setup_langfuse_tracing():
    """Configure Langfuse tracing with OpenTelemetry"""
    # Set default values if environment variables are not set
    langfuse_public_key = os.environ.get("LANGFUSE_PUBLIC_KEY", "")
    langfuse_secret_key = os.environ.get("LANGFUSE_SECRET_KEY", "")
    langfuse_host = os.environ.get("LANGFUSE_HOST", "")


    if not langfuse_public_key or not langfuse_secret_key:
        print("⚠️  Langfuse credentials not found. Tracing will be disabled.")
        print("   Set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY environment variables to enable tracing.")
        return None
    
    try:
        # Build Basic Auth header
        langfuse_auth = base64.b64encode(
            f"{langfuse_public_key}:{langfuse_secret_key}".encode()
        ).decode()
        
        # Configure OpenTelemetry endpoint & headers
        os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = langfuse_host + "/api/public/otel"
        os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = f"Authorization=Basic {langfuse_auth}"
        
        # Configure the telemetry (creates new tracer provider and sets it as global)
        strands_telemetry = StrandsTelemetry().setup_otlp_exporter()
        print("✅ Langfuse tracing enabled successfully!")
        return strands_telemetry
        
    except Exception as e:
        print(f"⚠️  Failed to setup Langfuse tracing: {e}")
        print("   Continuing without tracing...")
        return None

openai_model = OpenAIModel(
    client_args={
        #"base_url": "http://localhost:4000/v1",
        "base_url": os.environ.get("LITELLM_HOST", ""), 
        "api_key": "your-secret-key"  # Required but can be dummy for local servers
    },
    model_id="my-model",  # Model identifier
    temperature=0.3,  # Lower temperature for more consistent medical advice
    max_tokens=2048
)

def create_health_agent(session_id=None, provider_id=None):
    """Create the health agent with MCP healthcare data server connection and Langfuse tracing"""
    
    mcp_host = os.environ.get("MCP_HOST", "")
    
    # Setup Langfuse tracing
    strands_telemetry = setup_langfuse_tracing()
    
    # Connect to the MCP healthcare server using streamable HTTP client
    mcp_client = MCPClient(lambda: streamablehttp_client(mcp_host))
    
    # Get tools from the MCP server
    with mcp_client:
        tools = mcp_client.list_tools_sync()
        
        # Configure tracing attributes for clinical context
        trace_attributes = {
            "session.id": session_id or f"clinical-session-{os.getpid()}",
            "user.id": provider_id or "healthcare-provider@clinical-assistant.local",
            "langfuse.tags": [
                "Clinical-Assistant",
                "Healthcare-AI", 
                "Patient-Analysis",
                "Medical-Records",
                "MCP-Healthcare-Server"
            ]
        }
        
        # Create the health agent with MCP tools and tracing
        health_agent = Agent(
            model=openai_model,
            tools=tools,  # Use the MCP server tools
            trace_attributes=trace_attributes,  # Add Langfuse tracing attributes
            system_prompt="""You are a Clinical Decision Support AI Assistant with access to patient data through an MCP healthcare data server. You help healthcare professionals with diagnostic reasoning and clinical decision-making.

Your role is to:
- Provide evidence-based clinical insights and differential diagnoses
- Assist with symptom analysis and pattern recognition using patient data
- Offer treatment recommendations based on current medical guidelines and patient history
- Help interpret clinical findings and laboratory results
- Support clinical reasoning with relevant medical knowledge and patient-specific data
- Retrieve and analyze patient histories, lab results, and demographic information

Available Healthcare Data Tools (via MCP server at http://localhost:8000):
- get_patient_info: Retrieve patient demographics (use patient IDs: PAT001, PAT002, PAT003)
- get_patient_history: Get complete medical history including conditions and diagnoses
- get_lab_results: Retrieve lab results within specified timeframes
- search_patients: Find patients by name or ID
- get_patient_summary: Get comprehensive patient overview with risk assessment

Important Guidelines:
- Always emphasize that your recommendations are for clinical decision support only
- Remind users that final diagnostic and treatment decisions must be made by qualified healthcare professionals
- Base recommendations on established medical guidelines and evidence-based practices
- Consider patient safety as the highest priority
- Use the MCP healthcare data tools to provide personalized clinical insights
- Acknowledge limitations and recommend specialist consultation when appropriate
- Maintain patient confidentiality and HIPAA compliance principles

You should provide structured, clear responses that include:
1. Clinical assessment of presented information
2. Patient-specific data analysis when relevant (using MCP tools)
3. Differential diagnosis considerations
4. Recommended diagnostic workup or tests
5. Treatment considerations based on patient history
6. Recommmended medication
7. Red flags or urgent concerns to monitor

Remember: You are a support tool for healthcare professionals, not a replacement for clinical judgment. Use the MCP healthcare data server tools to access patient information when needed."""
        )
        
        return health_agent, mcp_client


def run_health_agent(question, st):
    message_placeholder = st.empty()
    full_response = ""

    async def process_streaming_response():
        nonlocal full_response
        
        # Get optional session and provider information for tracing
        session_id = os.environ.get("CLINICAL_SESSION_ID")
        provider_id = os.environ.get("HEALTHCARE_PROVIDER_ID")
        
        try:
            # Create the health agent with MCP connection and tracing
            health_agent, mcp_client = create_health_agent(session_id=session_id, provider_id=provider_id)

            
            # Keep the MCP client connection alive during the session
            with mcp_client:
                try:
                    # Stream the response
                    agent_stream = health_agent.stream_async(question)
                    async for event in agent_stream:
                        if "data" in event:
                            full_response += event["data"]
                            message_placeholder.markdown(full_response)
                except Exception as e:
                    print(f"Error processing request: {e}")
        except Exception as e:
            print(f"Error processing request: {e}")
            message_placeholder.markdown(
                "Sorry, an error occurred while generating the response."
            )
            print(f"Error processing request: {e}")  # Detailed error logging

    asyncio.run(process_streaming_response())

    return full_response


