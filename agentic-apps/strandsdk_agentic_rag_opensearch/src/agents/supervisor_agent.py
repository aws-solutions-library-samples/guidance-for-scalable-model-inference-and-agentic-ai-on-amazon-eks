"""Supervisor Agent using Strands SDK patterns."""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from strands import Agent, tool
from strands_tools import file_read
from ..config import config
from ..utils.logging import log_title
from ..utils.langfuse_config import langfuse_config
from ..utils.model_providers import get_reasoning_model
from ..tools.embedding_retriever import EmbeddingRetriever
from .mcp_agent import file_write  # Use the wrapped file_write from mcp_agent

logger = logging.getLogger(__name__)

# Create tools for the supervisor agent
@tool
def search_knowledge_base(query: str, top_k: int = 3) -> str:
    """
    Search the knowledge base for relevant information.
    
    Args:
        query: The search query
        top_k: Number of top results to return
        
    Returns:
        JSON string with search results
    """
    # Simple Langfuse event logging
    if langfuse_config.is_enabled:
        try:
            langfuse_config.client.create_event(
                name="knowledge-base-search",
                input={"query": query, "top_k": top_k}
            )
        except Exception as e:
            print(f"Langfuse event logging failed: {e}")
    
    try:
        retriever = EmbeddingRetriever()
        results = retriever.search(query, top_k=top_k)
        
        # Format results as compact JSON to reduce token usage
        formatted_results = []
        for result in results:
            # Limit content length to reduce tokens
            content = result['content']
            if len(content) > 300:
                content = content[:300] + "..."
                
            formatted_results.append({
                "source": result['metadata'].get('source', 'Unknown'),
                "content": content
            })
        
        # Convert to JSON string
        import json
        response = json.dumps(formatted_results, indent=2)
        
        # Log successful search
        if langfuse_config.is_enabled:
            try:
                langfuse_config.client.create_event(
                    name="knowledge-search-result",
                    output={"documents_found": len(results), "response_length": len(response)}
                )
            except Exception as e:
                print(f"Langfuse result logging failed: {e}")
        
        return f"<search_results>\n{response}\n</search_results>"
        
    except Exception as e:
        logger.error(f"Error searching knowledge base: {e}")
        error_msg = f"Error searching knowledge base: {str(e)}"
        
        # Log error
        if langfuse_config.is_enabled:
            try:
                langfuse_config.client.create_event(
                    name="knowledge-search-error",
                    output={"error": str(e)}
                )
            except Exception as log_error:
                print(f"Langfuse error logging failed: {log_error}")
        
        return error_msg

@tool
def check_knowledge_status() -> str:
    """
    Check the status of the knowledge base.
    
    Returns:
        JSON string with knowledge base status
    """
    # Simple Langfuse event logging
    if langfuse_config.is_enabled:
        try:
            langfuse_config.client.create_event(
                name="knowledge-status-check",
                input={}
            )
        except Exception as e:
            print(f"Langfuse event logging failed: {e}")
    
    try:
        retriever = EmbeddingRetriever()
        count = retriever.get_document_count()
        
        # Format as compact JSON to reduce token usage
        import json
        status_data = {
            "status": "ready" if count > 0 else "empty",
            "document_count": count,
            "last_updated": datetime.now().strftime("%Y-%m-%d")
        }
        response = json.dumps(status_data)
        
        # Log successful status check
        if langfuse_config.is_enabled:
            try:
                langfuse_config.client.create_event(
                    name="knowledge-status-result",
                    output={"document_count": count, "status": "ready"}
                )
            except Exception as e:
                print(f"Langfuse result logging failed: {e}")
        
        return f"<status>\n{response}\n</status>"
        
    except Exception as e:
        logger.error(f"Error checking knowledge status: {e}")
        error_msg = f"Knowledge base status unknown: {str(e)}"
        
        # Log error
        if langfuse_config.is_enabled:
            try:
                langfuse_config.client.create_event(
                    name="knowledge-status-error",
                    output={"error": str(e)}
                )
            except Exception as log_error:
                print(f"Langfuse error logging failed: {log_error}")
        
        return error_msg

# Create the supervisor agent
supervisor_agent = Agent(
    model=get_reasoning_model(),
    tools=[search_knowledge_base, check_knowledge_status, file_read, file_write],
    system_prompt="""
You are a RAG system that answers questions using only retrieved information.

WORKFLOW:
1. ALWAYS start with check_knowledge_status to verify the knowledge base
2. ALWAYS use search_knowledge_base to find information
3. NEVER use your own knowledge without searching first
4. Only provide information from retrieved documents
5. If no relevant information is found, say so clearly

TOOLS:
- check_knowledge_status: Verify knowledge base status
- search_knowledge_base: Find relevant information
- file_read: Read files when needed
- file_write: Write files when needed

FORMAT RESPONSES:
- Be concise and direct
- Include sources when available
- Use bullet points for clarity
- Focus only on answering the query with retrieved information
"""
)

def supervisor_agent_with_langfuse(query: str) -> str:
    """
    Wrapper for supervisor agent with Langfuse tracing.
    
    Args:
        query: User query to process
        
    Returns:
        Agent response as string
    """
    # Create Langfuse trace for the entire conversation
    trace = None
    if langfuse_config.is_enabled:
        try:
            # Use the wrapper function instead of direct client access
            trace = langfuse_config.create_trace(
                name="supervisor-agent-query",
                input_data={"query": query},
                metadata={
                    "agent_type": "supervisor",
                    "model": str(get_reasoning_model()),
                    "timestamp": datetime.now().isoformat()
                }
            )
        except Exception as e:
            print(f"Failed to create Langfuse trace: {e}")
            trace = None
    
    try:
        start_time = datetime.now()
        
        # Call the Strands agent
        response = supervisor_agent(query)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Update trace with successful completion
        if trace and langfuse_config.is_enabled:
            try:
                trace.end(
                    output={
                        "response": str(response),
                        "success": True,
                        "duration_seconds": duration,
                        "response_length": len(str(response))
                    }
                )
            except Exception as e:
                print(f"Failed to update Langfuse trace: {e}")
        
        logger.info(f"Supervisor agent completed query in {duration:.2f} seconds")
        return str(response)
        
    except Exception as e:
        logger.error(f"Error in supervisor agent: {e}")
        
        # Update trace with error
        if trace and langfuse_config.is_enabled:
            try:
                trace.end(
                    output={
                        "error": str(e),
                        "success": False,
                        "error_type": type(e).__name__
                    }
                )
            except Exception as trace_error:
                print(f"Failed to update Langfuse trace with error: {trace_error}")
        
        return f"I apologize, but I encountered an error while processing your request: {str(e)}"
    
    finally:
        # Flush Langfuse traces
        if langfuse_config.is_enabled:
            langfuse_config.flush()

# Export both the original agent and the wrapped version
__all__ = ["supervisor_agent", "supervisor_agent_with_langfuse"]
