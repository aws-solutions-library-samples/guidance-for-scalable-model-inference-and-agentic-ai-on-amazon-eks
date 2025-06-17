#!/usr/bin/env python3
"""Test script to verify model configuration."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.config import config
from src.utils.model_providers import get_reasoning_model
from src.tools.embedding_retriever import EmbeddingRetriever

def test_configuration():
    """Test the model configuration."""
    print("🔧 Testing Model Configuration")
    print("=" * 50)
    
    # Test configuration loading
    print(f"✅ Reasoning Model: {config.REASONING_MODEL}")
    print(f"✅ Embedding Model: {config.EMBEDDING_MODEL}")
    print(f"✅ LiteLLM Base URL: {config.LITELLM_BASE_URL}")
    print(f"✅ Embedding Base URL: {config.EMBEDDING_BASE_URL}")
    print()
    
    # Test reasoning model provider
    print("🤖 Testing Reasoning Model Provider")
    try:
        reasoning_model = get_reasoning_model()
        print(f"✅ Reasoning model created: {type(reasoning_model)}")
        if hasattr(reasoning_model, 'model_id'):
            print(f"   Model ID: {reasoning_model.model_id}")
        else:
            print(f"   Model String: {reasoning_model}")
    except Exception as e:
        print(f"❌ Failed to create reasoning model: {e}")
    print()
    
    # Test embedding retriever
    print("🔍 Testing Embedding Retriever")
    try:
        retriever = EmbeddingRetriever()
        print(f"✅ Embedding retriever created")
        print(f"   Model: {retriever.embedding_model}")
        print(f"   Endpoint: {retriever.embedding_endpoint}")
        print(f"   Target Dimension: {retriever.target_dimension}")
        
        # Test embedding generation
        test_text = "This is a test sentence for embedding."
        print(f"   Testing embedding generation...")
        embedding = retriever.embed(test_text)
        print(f"✅ Generated embedding with {len(embedding)} dimensions")
        
    except Exception as e:
        print(f"❌ Failed to test embedding retriever: {e}")
    print()
    
    print("🎯 Configuration Test Complete!")

if __name__ == "__main__":
    test_configuration()
