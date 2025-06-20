"""Enhanced Supervisor Agent with integrated Strands SDK and Langfuse tracing."""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from strands import Agent, tool
from strands_tools import file_read
from ..config import config
from ..utils.logging import log_title
from ..utils.model_providers import get_reasoning_model
from ..utils.strands_langfuse_integration import strands_langfuse, trace_agent_call
from ..tools.embedding_retriever import EmbeddingRetriever
from .mcp_agent import file_write  # Use the wrapped file_write from mcp_agent

logger = logging.getLogger(__name__)

# Enhanced tools with better Langfuse integration
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
    logger.info(f"Searching knowledge base for: {query[:100]}...")
    
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
                "content": content,
                "score": result.get('score', 0.0)
            })
        
        # Convert to JSON string
        import json
        response = json.dumps(formatted_results, indent=2)
        
        logger.info(f"Found {len(results)} relevant documents")
        return f"<search_results>\n{response}\n</search_results>"
        
    except Exception as e:
        logger.error(f"Error searching knowledge base: {e}")
        return f"Error searching knowledge base: {str(e)}"

@tool
def check_knowledge_status() -> str:
    """
    Check the status of the knowledge base.
    
    Returns:
        JSON string with knowledge base status
    """
    logger.info("Checking knowledge base status...")
    
    try:
        retriever = EmbeddingRetriever()
        count = retriever.get_document_count()
        
        # Format as compact JSON to reduce token usage
        import json
        status_data = {
            "status": "ready" if count > 0 else "empty",
            "document_count": count,
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "index_name": retriever.index_name
        }
        response = json.dumps(status_data)
        
        logger.info(f"Knowledge base status: {count} documents available")
        return f"<status>\n{response}\n</status>"
        
    except Exception as e:
        logger.error(f"Error checking knowledge status: {e}")
        return f"Knowledge base status unknown: {str(e)}"

@tool
def analyze_query_intent(query: str) -> str:
    """
    Analyze the user's query to determine intent and required actions.
    
    Args:
        query: User query to analyze
        
    Returns:
        JSON string with intent analysis
    """
    logger.info(f"Analyzing query intent: {query[:50]}...")
    
    try:
        import json
        
        # Simple intent analysis based on keywords and patterns
        intent_data = {
            "query": query,
            "length": len(query),
            "requires_search": any(word in query.lower() for word in [
                "what", "how", "why", "when", "where", "explain", "tell me", "describe"
            ]),
            "requires_file_ops": any(word in query.lower() for word in [
                "write", "save", "create", "file", "document"
            ]),
            "is_greeting": any(word in query.lower() for word in [
                "hello", "hi", "hey", "good morning", "good afternoon"
            ]),
            "complexity": "high" if len(query) > 100 else "medium" if len(query) > 50 else "low"
        }
        
        response = json.dumps(intent_data, indent=2)
        return f"<intent_analysis>\n{response}\n</intent_analysis>"
        
    except Exception as e:
        logger.error(f"Error analyzing query intent: {e}")
        return f"Error analyzing intent: {str(e)}"

# Create the enhanced supervisor agent with callback handler
def create_enhanced_supervisor_agent(session_id: Optional[str] = None, 
                                   user_id: Optional[str] = None) -> Agent:
    """
    Create an enhanced supervisor agent with Langfuse tracing.
    
    Args:
        session_id: Optional session identifier for tracing
        user_id: Optional user identifier for tracing
        
    Returns:
        Agent instance with tracing enabled
    """
    # Create callback handler for Langfuse integration
    callback_handler = None
    if strands_langfuse.is_enabled:
        callback_handler = strands_langfuse.create_strands_callback_handler(
            trace_name="enhanced-supervisor-agent",
            session_id=session_id,
            user_id=user_id,
            metadata={
                "agent_type": "enhanced_supervisor",
                "model": str(get_reasoning_model()),
                "tools": ["search_knowledge_base", "check_knowledge_status", "analyze_query_intent", "file_read", "file_write"]
            }
        )
    
    # Create the agent with enhanced system prompt
    agent = Agent(
        model=get_reasoning_model(),
        tools=[search_knowledge_base, check_knowledge_status, analyze_query_intent, file_read, file_write],
        callback_handler=callback_handler,
        system_prompt="""
You are an intelligent RAG (Retrieval Augmented Generation) system supervisor that answers questions using retrieved information and coordinates various tasks.

CORE WORKFLOW:
1. ALWAYS start by analyzing the query intent using analyze_query_intent
2. Check knowledge base status with check_knowledge_status if information retrieval is needed
3. Use search_knowledge_base to find relevant information for knowledge-based queries
4. Use file operations (file_read, file_write) when document management is required
5. Provide comprehensive, well-structured responses based on retrieved information

IMPORTANT RULES:
- NEVER provide information without first searching the knowledge base for relevant queries
- Always cite sources when available in your responses
- If no relevant information is found, clearly state this limitation
- Be transparent about what information comes from the knowledge base vs. general reasoning
- Use structured formatting (bullet points, numbered lists) for clarity
- Keep responses concise but comprehensive

RESPONSE FORMAT:
- Start with a brief summary of what you found
- Provide detailed information with clear structure
- Include source references when available
- End with any relevant follow-up suggestions

TOOLS AVAILABLE:
- analyze_query_intent: Understand what the user is asking for
- check_knowledge_status: Verify knowledge base availability
- search_knowledge_base: Find relevant information from documents
- file_read: Read files when needed
- file_write: Create or update files when requested

Remember: You are a supervisor coordinating multiple capabilities to provide the best possible response to user queries.
"""
    )
    
    return agent

# Create the default enhanced supervisor agent
enhanced_supervisor_agent = create_enhanced_supervisor_agent()

@trace_agent_call
def enhanced_supervisor_agent_with_tracing(query: str, session_id: Optional[str] = None, 
                                         user_id: Optional[str] = None) -> str:
    """
    Execute the enhanced supervisor agent with comprehensive Langfuse tracing.
    
    Args:
        query: User query to process
        session_id: Optional session identifier
        user_id: Optional user identifier
        
    Returns:
        Agent response as string
    """
    logger.info(f"Processing query with enhanced supervisor agent: {query[:100]}...")
    
    try:
        # Create agent with session-specific tracing if needed
        if session_id or user_id:
            agent = create_enhanced_supervisor_agent(session_id=session_id, user_id=user_id)
        else:
            agent = enhanced_supervisor_agent
        
        # Execute the agent
        start_time = datetime.now()
        response = agent(query)
        end_time = datetime.now()
        
        duration = (end_time - start_time).total_seconds()
        logger.info(f"Enhanced supervisor agent completed in {duration:.2f} seconds")
        
        return str(response)
        
    except Exception as e:
        logger.error(f"Error in enhanced supervisor agent: {e}")
        return f"I apologize, but I encountered an error while processing your request: {str(e)}"

# Async version for streaming applications
async def enhanced_supervisor_agent_async(query: str, session_id: Optional[str] = None,
                                        user_id: Optional[str] = None):
    """
    Async version of the enhanced supervisor agent with streaming support.
    
    Args:
        query: User query to process
        session_id: Optional session identifier
        user_id: Optional user identifier
        
    Yields:
        Streaming events from the agent
    """
    logger.info(f"Starting async processing: {query[:100]}...")
    
    try:
        # Create agent with session-specific tracing
        agent = create_enhanced_supervisor_agent(session_id=session_id, user_id=user_id)
        
        # Use async streaming if available
        if hasattr(agent, 'stream_async'):
            async for event in agent.stream_async(query):
                yield event
        else:
            # Fallback to synchronous execution
            response = agent(query)
            yield {"data": str(response), "type": "final_response"}
            
    except Exception as e:
        logger.error(f"Error in async enhanced supervisor agent: {e}")
        yield {"error": str(e), "type": "error"}

# Convenience function for simple usage
def ask_enhanced_supervisor(query: str, **kwargs) -> str:
    """
    Simple interface to ask the enhanced supervisor agent a question.
    
    Args:
        query: Question to ask
        **kwargs: Additional arguments (session_id, user_id, etc.)
        
    Returns:
        Agent response
    """
    return enhanced_supervisor_agent_with_tracing(query, **kwargs)

# Export all components
__all__ = [
    "enhanced_supervisor_agent",
    "enhanced_supervisor_agent_with_tracing", 
    "enhanced_supervisor_agent_async",
    "create_enhanced_supervisor_agent",
    "ask_enhanced_supervisor"
]
