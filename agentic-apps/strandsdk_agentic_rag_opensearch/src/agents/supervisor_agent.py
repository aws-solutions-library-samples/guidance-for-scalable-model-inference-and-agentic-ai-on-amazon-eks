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

def calculate_relevance_score(results: List[Dict], query: str) -> float:
    """
    Calculate relevance score with content validation to prevent false positives.
    
    Args:
        results: List of search results with scores
        query: Original search query for semantic validation
        
    Returns:
        float: Validated relevance score (0.0 to 1.0)
    """
    if not results:
        return 0.0
    
    # Extract scores and validate content relevance
    scores = []
    query_lower = query.lower()
    query_keywords = set(query_lower.split())
    
    for result in results:
        # Get the similarity score
        score = None
        if isinstance(result, dict):
            score = result.get('score') or result.get('_score')
            if score is None and 'metadata' in result:
                score = result['metadata'].get('score')
        
        if score is not None:
            # Validate content relevance by checking keyword overlap
            content = result.get('content', '').lower()
            content_keywords = set(content.split())
            
            # Calculate keyword overlap ratio
            overlap = len(query_keywords.intersection(content_keywords))
            overlap_ratio = overlap / len(query_keywords) if query_keywords else 0
            
            # Penalize results with very low keyword overlap
            if overlap_ratio < 0.1:  # Less than 10% keyword overlap
                score = score * 0.2  # Heavily penalize
            elif overlap_ratio < 0.3:  # Less than 30% keyword overlap
                score = score * 0.5  # Moderately penalize
            
            scores.append(float(score))
    
    if not scores:
        return 0.0
    
    # Calculate average and apply additional validation
    avg_score = sum(scores) / len(scores)
    
    # Additional semantic validation for common mismatches
    if any(keyword in query_lower for keyword in ['weather', 'temperature', 'forecast']):
        # For weather queries, check if results contain weather-related terms
        weather_terms = ['weather', 'temperature', 'rain', 'sunny', 'cloudy', 'forecast', 'celsius', 'fahrenheit']
        has_weather_content = False
        
        for result in results:
            content = result.get('content', '').lower()
            if any(term in content for term in weather_terms):
                has_weather_content = True
                break
        
        if not has_weather_content:
            avg_score = avg_score * 0.1  # Heavily penalize non-weather content for weather queries
    
    return min(avg_score, 1.0)

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
        
        # Calculate relevance score with content validation
        relevance_score = calculate_relevance_score(results, query)
        
        # Remove duplicate results
        seen_content = set()
        unique_results = []
        for result in results:
            content_hash = hash(result['content'][:100])  # Use first 100 chars as hash
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                unique_results.append(result)
        
        # Format results as compact JSON 
        formatted_results = []
        for result in unique_results[:top_k]:  # Ensure we don't exceed top_k after deduplication
            # Limit content length to reduce tokens
            content = result['content']
            if len(content) > 200:  
                content = content[:200] + "..."
                
            formatted_results.append({
                "source": result['metadata'].get('source', 'Unknown'),
                "content": content,
                "score": result.get('score', result.get('_score', 0.0))
            })
        
        # Create response with relevance metadata and validation info
        response_data = {
            "results": formatted_results,
            "relevance_score": relevance_score,
            "total_results": len(unique_results),
            "duplicates_removed": len(results) - len(unique_results),
            "query": query,
            "validation_note": "Relevance score includes content validation to prevent false positives"
        }
        
        # Convert to JSON string
        response = json.dumps(response_data, indent=2)
        
        # Log successful search with debug info
        logger.info(f"Knowledge base search completed: {len(unique_results)} unique results (removed {len(results) - len(unique_results)} duplicates), relevance: {relevance_score:.2f}")
        
        # Debug logging for relevance issues
        if relevance_score < 0.3:
            logger.debug(f"Low relevance detected for query '{query}': {relevance_score:.2f}")
            for i, result in enumerate(formatted_results[:2]):  # Log first 2 results for debugging
                logger.debug(f"Result {i+1}: {result['content'][:50]}... (score: {result['score']:.2f})")
        
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

# Create the supervisor agent with tracing and enhanced tools including MCP tools
def create_supervisor_agent_with_mcp():
    """Create supervisor agent with MCP tools integrated using proper context manager"""
    
    # Get MCP client
    mcp_client = get_tavily_mcp_client()
    
    if mcp_client:
        # Use the MCP client context manager as per Strands SDK documentation
        with mcp_client:
            # Get the tools from the MCP server
            mcp_tools = mcp_client.list_tools_sync()
            logger.info(f"Loaded {len(mcp_tools)} MCP tools from Tavily server")
            
            # Combine local tools with MCP tools
            all_tools = [
                search_knowledge_base, 
                check_knowledge_status, 
                file_read, 
                file_write
            ] + mcp_tools
            
            # Create agent within the MCP context
            return create_traced_agent(
                Agent,
                model=get_reasoning_model(),
                tools=all_tools,
                system_prompt="""
You are a RAG system with web search capabilities. Answer questions using retrieved info and real-time web data.

WORKFLOW:
1. ALWAYS start with check_knowledge_status() - verify knowledge base first
2. search_knowledge_base(query="terms") - search internal data (returns JSON with relevance_score)
3. Check the relevance_score: if < 0.3 OR for time-sensitive queries (weather, news, "today", "current"): use web_search
4. If relevance_score >= 0.3 and not time-sensitive: use RAG results
5. When writing files, ALWAYS use the output directory - call file_write with filename parameter only
6. Cite sources clearly

TOOLS AVAILABLE:
- check_knowledge_status(): Check KB status - ALWAYS CALL THIS FIRST
- search_knowledge_base(query): Search KB (returns JSON with relevance_score)
- web_search(query, max_results, search_depth, include_answer): MCP tool for web search
- news_search(query, max_results, days_back): MCP tool for news search
- health_check(): MCP tool to check Tavily service status
- file_read(path): Read files
- file_write(content, filename): Write files to output directory (use filename parameter, not path)

DECISION LOGIC:
1. FIRST: Always call check_knowledge_status()
2. For weather/news/current events: use web_search directly
3. For other queries: search knowledge base first, check relevance_score
4. If relevance_score < 0.3: use web_search for better results
5. If relevance_score >= 0.3: use RAG results
6. FINAL: When saving files, use file_write(content, filename) - files go to output directory automatically

FORMAT: Be concise, cite sources, use bullets when helpful

IMPORTANT: 
- ALWAYS start with check_knowledge_status()
- ALWAYS use filename parameter (not path) for file_write to save to output directory
""",
                session_id="supervisor-session",
                user_id="system"
            )
    else:
        # Fallback: create agent without MCP tools
        logger.warning("Creating agent without MCP tools due to client unavailability")
        return create_traced_agent(
            Agent,
            model=get_reasoning_model(),
            tools=[
                search_knowledge_base, 
                check_knowledge_status, 
                file_read, 
                file_write
            ],
            system_prompt="""
You are a RAG system. Answer questions using retrieved information from the knowledge base.

WORKFLOW:
1. ALWAYS start with check_knowledge_status() - verify knowledge base first
2. search_knowledge_base(query="terms") - search internal data
3. Use the retrieved information to answer questions
4. When writing files, ALWAYS use the output directory - call file_write with filename parameter only
5. Cite sources clearly

TOOLS AVAILABLE:
- check_knowledge_status(): Check KB status - ALWAYS CALL THIS FIRST
- search_knowledge_base(query): Search KB (returns relevance_score)
- file_read(path): Read files
- file_write(content, filename): Write files to output directory (use filename parameter, not path)

IMPORTANT: 
- ALWAYS start with check_knowledge_status()
- ALWAYS use filename parameter (not path) for file_write to save to output directory

FORMAT: Be concise, cite sources, use bullets when helpful
""",
            session_id="supervisor-session",
            user_id="system"
        )

# Create a wrapper class to handle MCP context properly
class SupervisorAgentWrapper:
    """Wrapper to handle MCP client context for supervisor agent"""
    
    def __init__(self):
        self.mcp_client = get_tavily_mcp_client()
        self.agent = None
        self._create_agent()
    
    def _create_agent(self):
        """Create the agent with proper MCP context"""
        if self.mcp_client:
            with self.mcp_client:
                # Get the tools from the MCP server
                mcp_tools = self.mcp_client.list_tools_sync()
                logger.info(f"Loaded {len(mcp_tools)} MCP tools from Tavily server")
                
                # Combine local tools with MCP tools
                all_tools = [
                    search_knowledge_base, 
                    check_knowledge_status, 
                    file_read, 
                    file_write
                ] + mcp_tools
                
                # Create agent within the MCP context
                self.agent = create_traced_agent(
                    Agent,
                    model=get_reasoning_model(),
                    tools=all_tools,
                    system_prompt="""
You are a RAG system with web search capabilities. Answer questions using retrieved info and real-time web data.

WORKFLOW:
1. check_knowledge_status() - verify knowledge base
2. search_knowledge_base(query="terms") - search internal data
4. If recommendation is "USE_WEB_SEARCH": use web_search or news_search MCP tools
5. If recommendation is "USE_RAG_RESULTS": use the RAG results
6. Cite sources clearly

TOOLS AVAILABLE:
- check_knowledge_status(): Check KB status
- search_knowledge_base(query): Search KB (returns relevance_score)
- web_search(query, max_results, search_depth, include_answer): MCP tool for web search
- news_search(query, max_results, days_back): MCP tool for news search
- health_check(): MCP tool to check Tavily service status
- file_read(path): Read files
- file_write(content, path): Write files

DECISION LOGIC:
1. Always search knowledge base first
3. Follow the recommendation (USE_WEB_SEARCH or USE_RAG_RESULTS)
4. For weather, news, or current events: prefer web search
5. For established knowledge: prefer RAG results

FORMAT: Be concise, cite sources, use bullets when helpful
""",
                    session_id="supervisor-session",
                    user_id="system"
                )
        else:
            # Fallback: create agent without MCP tools
            logger.warning("Creating agent without MCP tools due to client unavailability")
            self.agent = create_traced_agent(
                Agent,
                model=get_reasoning_model(),
                tools=[
                    search_knowledge_base, 
                    check_knowledge_status, 
                    file_read, 
                    file_write
                ],
                system_prompt="""
You are a RAG system. Answer questions using retrieved information from the knowledge base.

WORKFLOW:
1. ALWAYS start with check_knowledge_status() - verify knowledge base first
2. search_knowledge_base(query="terms") - search internal data
3. Use the retrieved information to answer questions
4. When writing files, ALWAYS use the output directory - call file_write with filename parameter only
5. Cite sources clearly

TOOLS AVAILABLE:
- check_knowledge_status(): Check KB status - ALWAYS CALL THIS FIRST
- search_knowledge_base(query): Search KB (returns relevance_score)
- file_read(path): Read files
- file_write(content, filename): Write files to output directory (use filename parameter, not path)

IMPORTANT: 
- ALWAYS start with check_knowledge_status()
- ALWAYS use filename parameter (not path) for file_write to save to output directory

FORMAT: Be concise, cite sources, use bullets when helpful
""",
                session_id="supervisor-session",
                user_id="system"
            )
    
    def __call__(self, query: str):
        """Call the agent with proper MCP context"""
        if self.mcp_client:
            with self.mcp_client:
                return self.agent(query)
        else:
            return self.agent(query)

# Create the default supervisor agent
supervisor_agent = SupervisorAgentWrapper()

def create_fresh_supervisor_agent():
    """
    Create a fresh supervisor agent instance with no conversation history.
    This ensures each query starts with a clean context window.
    """
    import uuid
    
    # Create a unique session ID for each fresh agent
    fresh_session_id = f"supervisor-{uuid.uuid4().hex[:8]}"
    
    # Return a fresh wrapper instance
    class FreshSupervisorAgentWrapper:
        """Fresh wrapper to handle MCP client context for supervisor agent"""
        
        def __init__(self, session_id):
            self.mcp_client = get_tavily_mcp_client()
            self.agent = None
            self.session_id = session_id
            self._create_agent()
        
        def _create_agent(self):
            """Create the agent with proper MCP context"""
            if self.mcp_client:
                with self.mcp_client:
                    # Get the tools from the MCP server
                    mcp_tools = self.mcp_client.list_tools_sync()
                    logger.info(f"Loaded {len(mcp_tools)} MCP tools from Tavily server for fresh agent")
                    
                    # Combine local tools with MCP tools
                    all_tools = [
                        search_knowledge_base, 
                        check_knowledge_status, 
                        file_read, 
                        file_write
                    ] + mcp_tools
                    
                    # Create agent within the MCP context
                    self.agent = create_traced_agent(
                        Agent,
                        model=get_reasoning_model(),
                        tools=all_tools,
                        system_prompt="""
You are a RAG system with web search capabilities. Answer questions using retrieved info and real-time web data.

WORKFLOW:
1. ALWAYS start with check_knowledge_status() - verify knowledge base first
2. search_knowledge_base(query="terms") - search internal data (returns JSON with relevance_score)
3. Check the relevance_score: if < 0.3 OR for time-sensitive queries (weather, news, "today", "current"): use web_search
4. If relevance_score >= 0.3 and not time-sensitive: use RAG results
5. When writing files, ALWAYS use the output directory - call file_write with filename parameter only
6. Cite sources clearly

TOOLS AVAILABLE:
- check_knowledge_status(): Check KB status - ALWAYS CALL THIS FIRST
- search_knowledge_base(query): Search KB (returns JSON with relevance_score)
- web_search(query, max_results, search_depth, include_answer): MCP tool for web search
- news_search(query, max_results, days_back): MCP tool for news search
- health_check(): MCP tool to check Tavily service status
- file_read(path): Read files
- file_write(content, filename): Write files to output directory (use filename parameter, not path)

DECISION LOGIC:
1. FIRST: Always call check_knowledge_status()
2. For weather/news/current events: use web_search directly
3. For other queries: search knowledge base first, check relevance_score
4. If relevance_score < 0.3: use web_search for better results
5. If relevance_score >= 0.3: use RAG results
6. FINAL: When saving files, use file_write(content, filename) - files go to output directory automatically

FORMAT: Be concise, cite sources, use bullets when helpful

IMPORTANT: 
- ALWAYS start with check_knowledge_status()
- ALWAYS use filename parameter (not path) for file_write to save to output directory
""",
                        session_id=self.session_id,
                        user_id="system"
                    )
            else:
                # Fallback: create agent without MCP tools
                logger.warning("Creating fresh agent without MCP tools due to client unavailability")
                self.agent = create_traced_agent(
                    Agent,
                    model=get_reasoning_model(),
                    tools=[
                        search_knowledge_base, 
                        check_knowledge_status, 
                        file_read, 
                        file_write
                    ],
                    system_prompt="""
You are a RAG system. Answer questions using retrieved information from the knowledge base.

WORKFLOW:
1. ALWAYS start with check_knowledge_status() - verify knowledge base first
2. search_knowledge_base(query="terms") - search internal data
3. Use the retrieved information to answer questions
4. When writing files, ALWAYS use the output directory - call file_write with filename parameter only
5. Cite sources clearly

TOOLS AVAILABLE:
- check_knowledge_status(): Check KB status - ALWAYS CALL THIS FIRST
- search_knowledge_base(query): Search KB (returns relevance_score)
- file_read(path): Read files
- file_write(content, filename): Write files to output directory (use filename parameter, not path)

IMPORTANT: 
- ALWAYS start with check_knowledge_status()
- ALWAYS use filename parameter (not path) for file_write to save to output directory

FORMAT: Be concise, cite sources, use bullets when helpful
""",
                    session_id=self.session_id,
                    user_id="system"
                )
        
        def __call__(self, query: str):
            """Call the agent with proper MCP context"""
            if self.mcp_client:
                with self.mcp_client:
                    return self.agent(query)
            else:
                return self.agent(query)
    
    return FreshSupervisorAgentWrapper(fresh_session_id)

# The supervisor_agent now has built-in tracing via Strands SDK and proper MCP integration
# Export the agent and the fresh agent creator
__all__ = ["supervisor_agent", "create_fresh_supervisor_agent"]
