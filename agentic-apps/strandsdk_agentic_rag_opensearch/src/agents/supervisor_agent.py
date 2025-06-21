"""Supervisor Agent using Strands SDK patterns with Tavily Web Search integration."""

import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from strands import Agent, tool
from strands_tools import file_read
from mcp.client.streamable_http import streamablehttp_client
from strands.tools.mcp.mcp_client import MCPClient
from ..config import config
from ..utils.logging import log_title
from ..utils.model_providers import get_reasoning_model
from ..utils.strands_langfuse_integration import create_traced_agent, setup_tracing_environment
from ..tools.embedding_retriever import EmbeddingRetriever
from .mcp_agent import file_write  # Use the wrapped file_write from mcp_agent

logger = logging.getLogger(__name__)

# Set up tracing environment
setup_tracing_environment()

# Initialize Tavily MCP client
tavily_mcp_client = None

def get_tavily_mcp_client():
    """Get or create Tavily MCP client"""
    global tavily_mcp_client
    if tavily_mcp_client is None:
        try:
            tavily_mcp_client = MCPClient(lambda: streamablehttp_client("http://localhost:8001/mcp"))
            logger.info("Tavily MCP client initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize Tavily MCP client: {e}")
            tavily_mcp_client = None
    return tavily_mcp_client

def calculate_relevance_score(results: List[Dict]) -> float:
    """
    Calculate average relevance score from search results.
    
    Args:
        results: List of search results with scores
        
    Returns:
        float: Average relevance score (0.0 to 1.0)
    """
    if not results:
        return 0.0
    
    # Extract scores from results (assuming they're in metadata or have a score field)
    scores = []
    for result in results:
        # Try different ways to get the score
        score = None
        if isinstance(result, dict):
            score = result.get('score') or result.get('_score')
            if score is None and 'metadata' in result:
                score = result['metadata'].get('score')
        
        if score is not None:
            scores.append(float(score))
    
    if not scores:
        # If no scores available, use content length as a proxy
        # Longer, more detailed results might be more relevant
        content_lengths = []
        for result in results:
            content = result.get('content', '') if isinstance(result, dict) else str(result)
            content_lengths.append(len(content))
        
        if content_lengths:
            avg_length = sum(content_lengths) / len(content_lengths)
            # Normalize to 0-1 scale (assuming 500 chars is good relevance)
            return min(avg_length / 500.0, 1.0)
        else:
            return 0.0
    
    return sum(scores) / len(scores)

# Create tools for the supervisor agent
@tool
def search_knowledge_base(query: str, top_k: int = 3) -> str:
    """
    Search the knowledge base for relevant information.
    
    Args:
        query (str): The search query - REQUIRED
        top_k (int): Number of top results to return (default: 3)
        
    Returns:
        str: JSON string with search results and relevance metadata
    """
    if not query or not isinstance(query, str):
        return '{"error": "Query parameter is required and must be a non-empty string", "results": [], "relevance_score": 0.0}'
    
    try:
        retriever = EmbeddingRetriever()
        results = retriever.search(query, top_k=top_k)
        
        # Calculate relevance score
        relevance_score = calculate_relevance_score(results)
        
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
                "score": result.get('score', result.get('_score', 0.0))
            })
        
        # Create response with relevance metadata
        response_data = {
            "results": formatted_results,
            "relevance_score": relevance_score,
            "total_results": len(results),
            "query": query
        }
        
        # Convert to JSON string
        response = json.dumps(response_data, indent=2)
        
        # Log successful search
        logger.info(f"Knowledge base search completed: {len(results)} results, relevance: {relevance_score:.2f}")
        
        return f"<search_results>\n{response}\n</search_results>"
        
    except Exception as e:
        logger.error(f"Error searching knowledge base: {e}")
        error_response = {
            "error": f"Error searching knowledge base: {str(e)}",
            "results": [],
            "relevance_score": 0.0,
            "query": query
        }
        return json.dumps(error_response)

@tool
def web_search_when_needed(query: str, rag_relevance_score: float = 0.0, max_results: int = 5) -> str:
    """
    Perform web search using Tavily API when RAG relevance is low.
    This tool automatically determines if web search is needed based on RAG relevance.
    
    Args:
        query (str): The search query
        rag_relevance_score (float): Relevance score from RAG search (0.0 to 1.0)
        max_results (int): Maximum number of results to return
        
    Returns:
        str: JSON string with web search results or explanation why not needed
    """
    # Define relevance threshold - if RAG score is below this, use web search
    RELEVANCE_THRESHOLD = 0.3
    
    if rag_relevance_score >= RELEVANCE_THRESHOLD:
        return json.dumps({
            "web_search_performed": False,
            "reason": f"RAG relevance score ({rag_relevance_score:.2f}) is above threshold ({RELEVANCE_THRESHOLD})",
            "recommendation": "Use RAG results instead of web search"
        })
    
    # Get Tavily MCP client
    mcp_client = get_tavily_mcp_client()
    if not mcp_client:
        return json.dumps({
            "error": "Tavily MCP client not available",
            "web_search_performed": False,
            "fallback": "Using available RAG results"
        })
    
    try:
        with mcp_client:
            # Get available tools from Tavily MCP server
            tools = mcp_client.list_tools_sync()
            web_search_tool = None
            
            for tool_info in tools:
                if tool_info.name == "web_search":
                    web_search_tool = tool_info
                    break
            
            if not web_search_tool:
                return json.dumps({
                    "error": "Web search tool not found in Tavily MCP server",
                    "web_search_performed": False
                })
            
            # Call the web search tool
            search_result = mcp_client.call_tool_sync(
                "web_search",
                {
                    "query": query,
                    "max_results": max_results,
                    "include_answer": True
                }
            )
            
            # Parse the result
            if hasattr(search_result, 'content') and search_result.content:
                web_data = json.loads(search_result.content[0].text)
                web_data["web_search_performed"] = True
                web_data["rag_relevance_score"] = rag_relevance_score
                web_data["search_reason"] = f"RAG relevance ({rag_relevance_score:.2f}) below threshold ({RELEVANCE_THRESHOLD})"
                
                logger.info(f"Web search completed for query: {query}")
                return json.dumps(web_data, indent=2)
            else:
                return json.dumps({
                    "error": "No content returned from web search",
                    "web_search_performed": False
                })
                
    except Exception as e:
        logger.error(f"Error performing web search: {e}")
        return json.dumps({
            "error": f"Web search failed: {str(e)}",
            "web_search_performed": False,
            "query": query
        })

@tool
def search_recent_news(query: str, days_back: int = 7, max_results: int = 5) -> str:
    """
    Search for recent news and current events using Tavily API.
    
    Args:
        query (str): The news search query
        days_back (int): How many days back to search
        max_results (int): Maximum number of results
        
    Returns:
        str: JSON string with recent news results
    """
    mcp_client = get_tavily_mcp_client()
    if not mcp_client:
        return json.dumps({
            "error": "Tavily MCP client not available",
            "news_search_performed": False
        })
    
    try:
        with mcp_client:
            # Call the news search tool
            search_result = mcp_client.call_tool_sync(
                "news_search",
                {
                    "query": query,
                    "max_results": max_results,
                    "days_back": days_back
                }
            )
            
            if hasattr(search_result, 'content') and search_result.content:
                news_data = json.loads(search_result.content[0].text)
                logger.info(f"News search completed for query: {query}")
                return json.dumps(news_data, indent=2)
            else:
                return json.dumps({
                    "error": "No content returned from news search",
                    "news_search_performed": False
                })
                
    except Exception as e:
        logger.error(f"Error performing news search: {e}")
        return json.dumps({
            "error": f"News search failed: {str(e)}",
            "news_search_performed": False,
            "query": query
        })

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

# Create the supervisor agent with tracing and enhanced tools
supervisor_agent = create_traced_agent(
    Agent,
    model=get_reasoning_model(),
    tools=[
        search_knowledge_base, 
        web_search_when_needed,
        search_recent_news,
        check_knowledge_status, 
        file_read, 
        file_write
    ],
    system_prompt="""
You are an intelligent RAG system with web search capabilities that answers questions using retrieved information and real-time web data when needed.

WORKFLOW:
1. ALWAYS start with check_knowledge_status to verify the knowledge base
2. Use search_knowledge_base with a proper query string to find information
3. ANALYZE the relevance_score in the search results:
   - If relevance_score < 0.3, automatically use web_search_when_needed for real-time information
   - If relevance_score >= 0.3, use the RAG results
4. For current events or recent news, use search_recent_news
5. Combine information from multiple sources when appropriate
6. Always cite your sources clearly

TOOLS AVAILABLE:
- check_knowledge_status(): Verify knowledge base status
- search_knowledge_base(query="search terms"): Search internal knowledge base (returns relevance_score)
- web_search_when_needed(query="search terms", rag_relevance_score=0.0): Automatic web search when RAG relevance is low
- search_recent_news(query="news topic", days_back=7): Search for recent news and current events
- file_read(path="file_path"): Read files when needed
- file_write(content="content", path="file_path"): Write files when needed

RELEVANCE SCORING:
- The search_knowledge_base tool returns a relevance_score (0.0 to 1.0)
- Scores < 0.3 indicate low relevance - use web search for better information
- Scores >= 0.3 indicate good relevance - use RAG results
- Always pass the rag_relevance_score to web_search_when_needed

RESPONSE FORMAT:
- Be comprehensive but concise
- Clearly indicate information sources (Knowledge Base, Web Search, News)
- Use bullet points for clarity
- Include URLs when available from web searches
- Mention when information is recent/current vs. from knowledge base

EXAMPLE WORKFLOW:
1. search_knowledge_base(query="your topic")
2. Check the relevance_score in results
3. If score < 0.3: web_search_when_needed(query="your topic", rag_relevance_score=score)
4. Combine and present information with clear source attribution
""",
    session_id="supervisor-session",
    user_id="system"
)

def create_fresh_supervisor_agent():
    """
    Create a fresh supervisor agent instance with no conversation history.
    This ensures each query starts with a clean context window.
    """
    import uuid
    
    # Create a unique session ID for each fresh agent
    fresh_session_id = f"supervisor-{uuid.uuid4().hex[:8]}"
    
    return create_traced_agent(
        Agent,
        model=get_reasoning_model(),
        tools=[
            search_knowledge_base, 
            web_search_when_needed,
            search_recent_news,
            check_knowledge_status, 
            file_read, 
            file_write
        ],
        system_prompt="""
You are an intelligent RAG system with web search capabilities that answers questions using retrieved information and real-time web data when needed.

WORKFLOW:
1. ALWAYS start with check_knowledge_status to verify the knowledge base
2. Use search_knowledge_base with a proper query string to find information
3. ANALYZE the relevance_score in the search results:
   - If relevance_score < 0.3, automatically use web_search_when_needed for real-time information
   - If relevance_score >= 0.3, use the RAG results
4. For current events or recent news, use search_recent_news
5. Combine information from multiple sources when appropriate
6. Always cite your sources clearly

TOOLS AVAILABLE:
- check_knowledge_status(): Verify knowledge base status
- search_knowledge_base(query="search terms"): Search internal knowledge base (returns relevance_score)
- web_search_when_needed(query="search terms", rag_relevance_score=0.0): Automatic web search when RAG relevance is low
- search_recent_news(query="news topic", days_back=7): Search for recent news and current events
- file_read(path="file_path"): Read files when needed
- file_write(content="content", path="file_path"): Write files when needed

RELEVANCE SCORING:
- The search_knowledge_base tool returns a relevance_score (0.0 to 1.0)
- Scores < 0.3 indicate low relevance - use web search for better information
- Scores >= 0.3 indicate good relevance - use RAG results
- Always pass the rag_relevance_score to web_search_when_needed

RESPONSE FORMAT:
- Be comprehensive but concise
- Clearly indicate information sources (Knowledge Base, Web Search, News)
- Use bullet points for clarity
- Include URLs when available from web searches
- Mention when information is recent/current vs. from knowledge base

EXAMPLE WORKFLOW:
1. search_knowledge_base(query="your topic")
2. Check the relevance_score in results
3. If score < 0.3: web_search_when_needed(query="your topic", rag_relevance_score=score)
4. Combine and present information with clear source attribution
""",
        session_id=fresh_session_id,
        user_id="system"
    )

# The supervisor_agent now has built-in tracing via Strands SDK and web search capabilities
# Export the agent and the fresh agent creator
__all__ = ["supervisor_agent", "create_fresh_supervisor_agent"]
