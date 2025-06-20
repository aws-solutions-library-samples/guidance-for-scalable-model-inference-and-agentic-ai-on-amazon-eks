#!/usr/bin/env python3
"""
Enhanced Multi-Agent RAG System with Strands SDK and Langfuse Integration

This enhanced version provides:
- Native Strands SDK callback integration with Langfuse
- Comprehensive tracing of agent execution, tool calls, and streaming
- Session and user tracking for better observability
- Async streaming support for real-time applications
- Better error handling and recovery
"""

import sys
import logging
import asyncio
import uuid
from typing import Optional
from datetime import datetime
from .config import config
from .utils.logging import setup_logging, log_title
from .utils.strands_langfuse_integration import strands_langfuse
from .agents.enhanced_supervisor_agent import (
    enhanced_supervisor_agent_with_tracing,
    enhanced_supervisor_agent_async,
    ask_enhanced_supervisor
)

def main():
    """Enhanced main application entry point."""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Validate configuration
        config.validate_config()
        
        log_title("ENHANCED MULTI-AGENT RAG SYSTEM STARTUP")
        logger.info("Starting Enhanced Multi-Agent RAG System with Strands SDK")
        logger.info(f"OpenSearch Endpoint: {config.OPENSEARCH_ENDPOINT}")
        logger.info(f"Knowledge Directory: {config.KNOWLEDGE_DIR}")
        logger.info(f"Reasoning Model: {config.REASONING_MODEL}")
        logger.info(f"Embedding Model: {config.EMBEDDING_MODEL}")
        logger.info(f"LiteLLM Endpoint: {config.LITELLM_BASE_URL}")
        logger.info(f"Langfuse Enabled: {config.is_langfuse_enabled()}")
        logger.info(f"Strands-Langfuse Integration: {strands_langfuse.is_enabled}")
        
        # Check if we should run in async mode
        if len(sys.argv) > 1 and sys.argv[1] == "--async":
            asyncio.run(run_async_interactive_mode())
        else:
            run_enhanced_interactive_mode()
        
    except KeyboardInterrupt:
        print("\n\nExiting gracefully...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        sys.exit(1)

def run_enhanced_interactive_mode():
    """Run the enhanced application in interactive mode with session tracking."""
    log_title("ENHANCED INTERACTIVE MODE")
    
    # Generate session ID for this conversation
    session_id = str(uuid.uuid4())
    user_id = "interactive_user"  # Could be made configurable
    
    print("🚀 Enhanced Multi-Agent RAG System Ready!")
    print("✨ Features: Strands SDK + Langfuse Tracing + Session Tracking")
    print("Ask questions and I'll use my specialized agents with full observability.")
    print("Type 'exit', 'quit', or press Ctrl+C to exit.")
    print(f"📊 Session ID: {session_id}")
    if strands_langfuse.is_enabled:
        print("🔍 Langfuse tracing: ENABLED")
    else:
        print("⚠️ Langfuse tracing: DISABLED")
    print()
    
    conversation_count = 0
    
    while True:
        try:
            # Get user input
            user_input = input("❓ Your question: ").strip()
            
            # Check for exit commands
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("\n👋 Goodbye!")
                break
            
            # Check for special commands
            if user_input.lower() == 'session':
                print(f"📊 Current session ID: {session_id}")
                print(f"💬 Conversation count: {conversation_count}")
                continue
            
            if user_input.lower() == 'trace':
                if strands_langfuse.is_enabled:
                    print("🔍 Langfuse tracing is ENABLED")
                    print(f"🌐 Langfuse host: {config.LANGFUSE_HOST}")
                else:
                    print("⚠️ Langfuse tracing is DISABLED")
                continue
            
            if not user_input:
                print("Please enter a question or type 'exit' to quit.")
                continue
            
            # Process the query
            conversation_count += 1
            print(f"\n🔄 Processing request #{conversation_count}...")
            
            try:
                # Limit query length to avoid context window issues
                if len(user_input) > 1000:
                    print("⚠️ Query is too long, truncating to 1000 characters...")
                    user_input = user_input[:1000]
                
                # Use the enhanced supervisor agent with session tracking
                start_time = datetime.now()
                response = enhanced_supervisor_agent_with_tracing(
                    user_input, 
                    session_id=session_id,
                    user_id=user_id
                )
                end_time = datetime.now()
                
                duration = (end_time - start_time).total_seconds()
                
                print(f"\n🤖 Response (processed in {duration:.2f}s):")
                print("=" * 60)
                print(response)
                print("=" * 60)
                
                if strands_langfuse.is_enabled:
                    print("📊 Trace logged to Langfuse")
                
            except Exception as e:
                print(f"\n❌ Error: {e}")
                logging.error(f"Error processing query #{conversation_count}: {e}")
            
            print("\n" + "="*80 + "\n")
            
        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except Exception as e:
            print(f"\n❌ An error occurred: {e}")
            print("Please try again with a different question.\n")
    
    # Final session summary
    print(f"\n📊 Session Summary:")
    print(f"   Session ID: {session_id}")
    print(f"   Total conversations: {conversation_count}")
    print(f"   Langfuse tracing: {'ENABLED' if strands_langfuse.is_enabled else 'DISABLED'}")

async def run_async_interactive_mode():
    """Run the application in async interactive mode with streaming."""
    log_title("ASYNC STREAMING MODE")
    
    # Generate session ID for this conversation
    session_id = str(uuid.uuid4())
    user_id = "async_user"
    
    print("🚀 Enhanced Multi-Agent RAG System (Async Streaming Mode)")
    print("✨ Features: Real-time streaming + Langfuse Tracing")
    print("Ask questions and see responses stream in real-time.")
    print("Type 'exit', 'quit', or press Ctrl+C to exit.")
    print(f"📊 Session ID: {session_id}")
    print()
    
    conversation_count = 0
    
    while True:
        try:
            # Get user input (note: input() is blocking, but this is just a demo)
            user_input = input("❓ Your question: ").strip()
            
            # Check for exit commands
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("\n👋 Goodbye!")
                break
            
            if not user_input:
                print("Please enter a question or type 'exit' to quit.")
                continue
            
            # Process the query with streaming
            conversation_count += 1
            print(f"\n🔄 Streaming response #{conversation_count}...")
            print("=" * 60)
            
            try:
                # Stream the response
                async for event in enhanced_supervisor_agent_async(
                    user_input,
                    session_id=session_id,
                    user_id=user_id
                ):
                    if event.get("type") == "error":
                        print(f"\n❌ Error: {event['error']}")
                        break
                    elif "data" in event:
                        print(event["data"], end="", flush=True)
                
                print("\n" + "=" * 60)
                
                if strands_langfuse.is_enabled:
                    print("📊 Streaming trace logged to Langfuse")
                
            except Exception as e:
                print(f"\n❌ Error: {e}")
                logging.error(f"Error in async processing #{conversation_count}: {e}")
            
            print("\n" + "="*80 + "\n")
            
        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except Exception as e:
            print(f"\n❌ An error occurred: {e}")
            print("Please try again with a different question.\n")

def run_single_query(query: str, session_id: Optional[str] = None, 
                    user_id: Optional[str] = None) -> Optional[str]:
    """
    Run a single query with enhanced tracing and return the result.
    
    Args:
        query: User query to process
        session_id: Optional session identifier
        user_id: Optional user identifier
        
    Returns:
        Agent response or error message
    """
    try:
        config.validate_config()
        
        # Generate session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Limit query length to avoid context window issues
        if len(query) > 1000:
            logging.warning("Query too long, truncating to 1000 characters")
            query = query[:1000]
        
        # Use the enhanced supervisor agent
        response = enhanced_supervisor_agent_with_tracing(
            query,
            session_id=session_id,
            user_id=user_id or "api_user"
        )
        
        # Limit response length if needed
        response_str = str(response)
        if len(response_str) > 5000:
            logging.warning("Response too long, truncating to 5000 characters")
            response_str = response_str[:5000] + "... [Response truncated due to length]"
            
        return response_str
        
    except Exception as e:
        logging.error(f"Single query execution failed: {e}")
        return f"Error processing query: {str(e)}"

def run_batch_queries(queries: list, session_id: Optional[str] = None) -> list:
    """
    Run multiple queries in batch with shared session tracking.
    
    Args:
        queries: List of queries to process
        session_id: Optional session identifier for the batch
        
    Returns:
        List of responses
    """
    if not session_id:
        session_id = str(uuid.uuid4())
    
    results = []
    for i, query in enumerate(queries):
        try:
            print(f"Processing query {i+1}/{len(queries)}...")
            response = run_single_query(
                query, 
                session_id=session_id, 
                user_id=f"batch_user_{i}"
            )
            results.append(response)
        except Exception as e:
            logging.error(f"Error processing batch query {i+1}: {e}")
            results.append(f"Error: {str(e)}")
    
    return results

# CLI interface
if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--help":
            print("Enhanced Multi-Agent RAG System")
            print("Usage:")
            print("  python enhanced_main.py                 # Interactive mode")
            print("  python enhanced_main.py --async         # Async streaming mode")
            print("  python enhanced_main.py --query 'text'  # Single query mode")
            print("  python enhanced_main.py --help          # Show this help")
        elif sys.argv[1] == "--query" and len(sys.argv) > 2:
            # Single query mode
            query = " ".join(sys.argv[2:])
            result = run_single_query(query)
            print(result)
        else:
            main()
    else:
        main()
