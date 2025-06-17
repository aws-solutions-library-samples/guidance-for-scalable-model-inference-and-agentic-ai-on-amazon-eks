"""Configuration management for the multi-agent RAG system."""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for the application."""
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "us.anthropic.claude-3-7-sonnet-20250219-v1:0")
    
    # AWS Configuration
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    OPENSEARCH_ENDPOINT: str = os.getenv("OPENSEARCH_ENDPOINT", "")
    
    # Langfuse Configuration
    LANGFUSE_HOST: str = os.getenv("LANGFUSE_HOST", "")
    LANGFUSE_PUBLIC_KEY: str = os.getenv("LANGFUSE_PUBLIC_KEY", "")
    LANGFUSE_SECRET_KEY: str = os.getenv("LANGFUSE_SECRET_KEY", "")
    
    # Application Configuration
    KNOWLEDGE_DIR: str = os.getenv("KNOWLEDGE_DIR", "knowledge")
    OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", "output")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    
    # Vector Search Configuration
    VECTOR_INDEX_NAME: str = os.getenv("VECTOR_INDEX_NAME", "knowledge-embeddings")
    TOP_K_RESULTS: int = int(os.getenv("TOP_K_RESULTS", "5"))
    
    @classmethod
    def is_langfuse_enabled(cls) -> bool:
        """Check if Langfuse is properly configured."""
        return bool(cls.LANGFUSE_HOST and cls.LANGFUSE_PUBLIC_KEY and cls.LANGFUSE_SECRET_KEY)
    
    @classmethod
    def validate_config(cls) -> None:
        """Validate required configuration."""
        required_vars = [
            ("OPENAI_API_KEY", cls.OPENAI_API_KEY),
            ("OPENSEARCH_ENDPOINT", cls.OPENSEARCH_ENDPOINT),
        ]
        
        missing_vars = [name for name, value in required_vars if not value]
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

# Global config instance
config = Config()
