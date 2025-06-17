"""Supervisor Agent using Strands SDK patterns."""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from strands import Agent, tool
from strands_tools import file_read, file_write
from ..config import config
from ..utils.logging import log_title
from ..utils.langfuse_config import langfuse_config
from ..utils.model_providers import get_reasoning_model
from ..tools.embedding_retriever import EmbeddingRetriever

logger = logging.getLogger(__name__)

# Create tools for the supervisor agent
@tool
def search_knowledge_base(query: str, top_k: int = 5) -> str:
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
        
        context_parts = []
        for i, result in enumerate(results, 1):
            context_parts.append(f"Document {i}:\nSource: {result['metadata'].get('source', 'Unknown')}\nContent: {result['content'][:500]}...")
        
        context = "\n\n".join(context_parts)
        response = f"Found {len(results)} relevant documents:\n\n{context}"
        
        # Log successful search
        if langfuse_config.is_enabled:
            try:
                langfuse_config.client.create_event(
                    name="knowledge-search-result",
                    output={"documents_found": len(results), "response_length": len(response)}
                )
            except Exception as e:
                print(f"Langfuse result logging failed: {e}")
        
        return response
        
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
        response = f"Knowledge base contains {count} documents and is ready for queries."
        
        # Log successful status check
        if langfuse_config.is_enabled:
            try:
                langfuse_config.client.create_event(
                    name="knowledge-status-result",
                    output={"document_count": count, "status": "ready"}
                )
            except Exception as e:
                print(f"Langfuse result logging failed: {e}")
        
        return response
        
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
You are SupervisorMaster, an intelligent orchestrating agent for a sophisticated multi-agent RAG system. Your role is to:

1. **Query Processing**: Analyze user queries and determine the best approach to answer them
2. **Knowledge Retrieval**: Use the search_knowledge_base tool to find relevant information
3. **Response Generation**: Synthesize information from multiple sources into comprehensive answers
4. **File Operations**: Create, read, and write files when needed using the available tools
5. **Status Monitoring**: Check system status and provide helpful feedback

**Available Tools:**
- search_knowledge_base: Search for relevant information in the knowledge base
- check_knowledge_status: Check if the knowledge base is ready and how many documents it contains
- file_read: Read content from files
- file_write: Write content to files

**Instructions:**
- Always start by checking the knowledge base status if this is the first interaction
- Use search_knowledge_base to find relevant information for user queries
- Provide comprehensive, well-structured responses
- Include source information when available
- If asked to create files or summaries, use the file_write tool
- Be helpful, accurate, and thorough in your responses

Focus on delivering high-quality, well-researched responses using the available knowledge and tools.
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
            trace_id = langfuse_config.client.create_trace_id()
            trace = langfuse_config.client.start_span(
                name="supervisor-agent-query",
                input={"query": query},
                metadata={
                    "agent_type": "supervisor",
                    "model": str(get_reasoning_model()),
                    "timestamp": datetime.now().isoformat()
                },
                trace_id=trace_id
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
