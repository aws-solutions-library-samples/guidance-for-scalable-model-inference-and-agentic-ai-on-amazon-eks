#!/usr/bin/env python3
"""
Clean single query runner that suppresses async warnings.
"""

# Import global async cleanup FIRST
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.utils.global_async_cleanup import setup_global_async_cleanup, install_global_stderr_filter

# Ensure global cleanup is applied
setup_global_async_cleanup()
install_global_stderr_filter()

# Now import the supervisor agent
from src.agents.supervisor_agent import supervisor_agent

def run_clean_query(query: str):
    """Run a single query with clean output."""
    print("🚀 Enhanced RAG System - Single Query (Clean Mode)")
    print("=" * 60)
    print(f"Query: {query}")
    print("=" * 60)
    
    try:
        response = supervisor_agent(query)
        print("\n📝 Response:")
        print("-" * 40)
        print(response)
        print("-" * 40)
        print("\n✅ Query completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error processing query: {e}")
        return False
    
    return True

if __name__ == "__main__":
    # Test with a sample query
    test_query = "What is Bell's palsy and how is it treated?"
    
    if len(sys.argv) > 1:
        # Use command line argument if provided
        test_query = " ".join(sys.argv[1:])
    
    success = run_clean_query(test_query)
    sys.exit(0 if success else 1)
