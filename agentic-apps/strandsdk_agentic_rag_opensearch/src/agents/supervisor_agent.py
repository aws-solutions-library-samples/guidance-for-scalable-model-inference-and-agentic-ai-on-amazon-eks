"""Supervisor Agent using Strands SDK patterns."""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from strands import Agent, tool
from strands_tools import file_read
from ..config import config
from ..utils.logging import log_title
from ..utils.model_providers import get_reasoning_model
from ..utils.strands_langfuse_integration import create_traced_agent, setup_tracing_environment
from ..tools.embedding_retriever import EmbeddingRetriever
from .mcp_agent import file_write  # Use the wrapped file_write from mcp_agent

logger = logging.getLogger(__name__)

# Set up tracing environment
setup_tracing_environment()

# Create tools for the supervisor agent
@tool
def search_knowledge_base(query: str, top_k: int = 3) -> str:
    """
    Search the knowledge base for relevant information.
    
    Args:
        query (str): The search query - REQUIRED
        top_k (int): Number of top results to return (default: 3)
        
    Returns:
        str: JSON string with search results
    """
    if not query or not isinstance(query, str):
        return '{"error": "Query parameter is required and must be a non-empty string", "results": []}'
    
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
        logger.info(f"Knowledge base search completed: {len(results)} results")
        
        return f"<search_results>\n{response}\n</search_results>"
        
    except Exception as e:
        logger.error(f"Error searching knowledge base: {e}")
        error_msg = f"Error searching knowledge base: {str(e)}"
        return error_msg

@tool
def check_knowledge_status() -> str:
    """
    Check the status of the knowledge base.
    
    Returns:
        str: JSON string with knowledge base status
    """
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
        logger.info(f"Knowledge base status checked: {count} documents")
        
        return response
        
    except Exception as e:
        logger.error(f"Error checking knowledge status: {e}")
        error_msg = f'{{"error": "Failed to check knowledge status: {str(e)}", "status": "error"}}'
        return error_msg
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

# Create the supervisor agent with tracing
supervisor_agent = create_traced_agent(
    Agent,
    model=get_reasoning_model(),
    tools=[search_knowledge_base, check_knowledge_status, file_read, file_write],
    system_prompt="""
You are a RAG system that answers questions using only retrieved information.

WORKFLOW:
1. ALWAYS start with check_knowledge_status to verify the knowledge base
2. ALWAYS use search_knowledge_base with a proper query string to find information
3. NEVER use your own knowledge without searching first
4. Only provide information from retrieved documents
5. If no relevant information is found, say so clearly

TOOLS:
- check_knowledge_status(): Verify knowledge base status (no parameters needed)
- search_knowledge_base(query="your search query"): Find relevant information (query parameter is REQUIRED)
- file_read(path="file_path"): Read files when needed
- file_write(content="content", path="file_path"): Write files when needed

IMPORTANT TOOL USAGE:
- When using search_knowledge_base, ALWAYS provide a query parameter with the search terms
- Example: search_knowledge_base(query="Bell's palsy symptoms")
- Never call search_knowledge_base without a query parameter

FORMAT RESPONSES:
- Be concise and direct
- Include sources when available
- Use bullet points for clarity
- Focus only on answering the query with retrieved information
""",
    session_id="supervisor-session",
    user_id="system"
)

# The supervisor_agent now has built-in tracing via Strands SDK
# Export the agent
__all__ = ["supervisor_agent"]
