"""Model provider configurations for Strands agents."""

from strands.models.litellm import LiteLLMModel
from ..config import config

def create_litellm_reasoning_model():
    """Create a LiteLLM model instance for reasoning tasks."""
    return LiteLLMModel(
        client_args={
            "api_key": config.LITELLM_API_KEY,
            "base_url": config.LITELLM_BASE_URL,
        },
        model_id=config.REASONING_MODEL,
        params={
            "temperature": 0.7,
            "max_tokens": 4096,
        }
    )

def get_reasoning_model():
    """Get the configured reasoning model for agents."""
    try:
        # Try to use LiteLLM if available
        return create_litellm_reasoning_model()
    except ImportError:
        # Fallback to string model ID (will use Bedrock)
        return config.REASONING_MODEL
    except Exception as e:
        print(f"Warning: Failed to create LiteLLM model, falling back to string ID: {e}")
        return config.REASONING_MODEL
