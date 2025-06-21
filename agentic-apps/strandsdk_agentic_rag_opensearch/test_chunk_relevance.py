#!/usr/bin/env python3
"""
Test script specifically for the chunk relevance evaluation function.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.agents.supervisor_agent import check_chunks_relevance

def test_chunk_relevance_evaluation():
    """Test the chunk relevance evaluation with sample data."""
    
    print("=" * 60)
    print("Testing Chunk Relevance Evaluation (RAGAs)")
    print("=" * 60)
    
    # Sample test data
    sample_results = """Score: 0.85
Content: Bell's palsy is a condition that causes sudden weakness in the muscles on one side of your face. This makes half of your face appear to droop. Your smile is one-sided, and your eye on that side resists closing.

Score: 0.72
Content: The exact cause of Bell's palsy is unknown, but it's believed to be the result of swelling and inflammation of the nerve that controls the muscles on one side of your face. It may be associated with viral infections.

Score: 0.68
Content: Treatment for Bell's palsy may include medications such as corticosteroids to reduce inflammation and antiviral drugs if a viral infection is suspected."""
    
    sample_question = "What is Bell's palsy?"
    
    print(f"Question: {sample_question}")
    print("\nSample Results:")
    print(sample_results)
    print("\n" + "=" * 60)
    print("Running RAGAs Evaluation...")
    print("=" * 60)
    
    try:
        # Test the chunk relevance evaluation
        result = check_chunks_relevance(sample_results, sample_question)
        
        print("\nEvaluation Result:")
        print(f"- Relevance Score: {result.get('chunk_relevance_score', 'N/A')}")
        print(f"- Relevance Value: {result.get('chunk_relevance_value', 'N/A')}")
        
        if 'error' in result:
            print(f"- Error: {result['error']}")
        else:
            print("✅ Evaluation completed successfully!")
            
    except Exception as e:
        print(f"❌ Error during evaluation: {str(e)}")
    
    print("\n" + "=" * 60)
    print("Test completed")
    print("=" * 60)

if __name__ == "__main__":
    test_chunk_relevance_evaluation()
