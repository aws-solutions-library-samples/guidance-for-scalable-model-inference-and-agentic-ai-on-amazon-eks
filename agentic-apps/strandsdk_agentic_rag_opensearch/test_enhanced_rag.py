#!/usr/bin/env python3
"""
Test script for the enhanced RAG system with chunk relevance evaluation.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.agents.supervisor_agent import supervisor_agent

def test_enhanced_rag_workflow():
    """Test the enhanced RAG workflow with relevance evaluation."""
    
    print("=" * 60)
    print("Testing Enhanced RAG System with Chunk Relevance Evaluation")
    print("=" * 60)
    
    # Test queries
    test_queries = [
        "What is Bell's palsy?",  # Medical query likely in knowledge base
        "What's the weather like today?",  # Time-sensitive query for web search
        "Tell me about machine learning algorithms",  # General tech query
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n--- Test {i}: {query} ---")
        try:
            response = supervisor_agent(query)
            print(f"Response: {response}")
        except Exception as e:
            print(f"Error: {str(e)}")
        print("-" * 40)

if __name__ == "__main__":
    test_enhanced_rag_workflow()
