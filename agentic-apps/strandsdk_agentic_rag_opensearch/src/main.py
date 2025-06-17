#!/usr/bin/env python3
"""
Multi-Agent RAG System with MCP and OpenSearch using Strands SDK

A sophisticated multi-agent system that combines:
- Knowledge management with change detection
- RAG (Retrieval Augmented Generation) with OpenSearch
- MCP (Model Context Protocol) tool integration
- Strands SDK agent orchestration
- Langfuse observability integration
"""

import sys
import logging
from typing import Optional
from .config import config
from .utils.logging import setup_logging, log_title
from .agents.supervisor_agent import supervisor_agent, supervisor_agent_with_langfuse
from .agents.knowledge_agent import knowledge_agent, knowledge_agent_with_langfuse
from .agents.mcp_agent import mcp_agent, mcp_agent_with_langfuse

def main():
    """Main application entry point."""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Validate configuration
        config.validate_config()
        
        log_title("MULTI-AGENT RAG SYSTEM STARTUP")
        logger.info("Starting Multi-Agent RAG System with Strands SDK")
        logger.info(f"OpenSearch Endpoint: {config.OPENSEARCH_ENDPOINT}")
        logger.info(f"Knowledge Directory: {config.KNOWLEDGE_DIR}")
        logger.info(f"Default Model: {config.DEFAULT_MODEL}")
        logger.info(f"Langfuse Enabled: {config.is_langfuse_enabled()}")
        
        # Interactive mode
        run_interactive_mode()
        
    except KeyboardInterrupt:
        print("\n\nExiting gracefully...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        sys.exit(1)

def run_interactive_mode():
    """Run the application in interactive mode."""
    log_title("INTERACTIVE MODE")
    print("🤖 Multi-Agent RAG System Ready!")
    print("Ask questions and I'll use my specialized agents to help you.")
    print("Type 'exit', 'quit', or press Ctrl+C to exit.\n")
    
    while True:
        try:
            # Get user input
            user_input = input("❓ Your question: ").strip()
            
            # Check for exit commands
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("\n👋 Goodbye!")
                break
            
            if not user_input:
                print("Please enter a question or type 'exit' to quit.")
                continue
            
            # Process the query using the supervisor agent
            print("\n🔄 Processing your request...")
            
            try:
                # Use the Langfuse-enabled supervisor agent if Langfuse is configured
                if config.is_langfuse_enabled():
                    response = supervisor_agent_with_langfuse(user_input)
                    print(f"\n🤖 Response (with Langfuse tracing):\n{response}")
                else:
                    response = supervisor_agent(user_input)
                    print(f"\n🤖 Response:\n{response}")
                
            except Exception as e:
                print(f"\n❌ Error: {e}")
                logger.error(f"Error processing query: {e}")
            
            print("\n" + "="*60 + "\n")
            
        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except Exception as e:
            print(f"\n❌ An error occurred: {e}")
            print("Please try again with a different question.\n")

def run_single_query(query: str) -> Optional[str]:
    """Run a single query and return the result."""
    try:
        config.validate_config()
        
        # Use the Langfuse-enabled supervisor agent if Langfuse is configured
        if config.is_langfuse_enabled():
            response = supervisor_agent_with_langfuse(query)
        else:
            response = supervisor_agent(query)
            
        return str(response)
    except Exception as e:
        logging.error(f"Single query execution failed: {e}")
        return None

if __name__ == "__main__":
    main()
