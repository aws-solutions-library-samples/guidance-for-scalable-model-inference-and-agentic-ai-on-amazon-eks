"""Langfuse configuration and utilities."""

from typing import Optional, Dict, Any
from ..config import config

try:
    from langfuse import Langfuse
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False
    Langfuse = None

class LangfuseConfig:
    """Langfuse configuration and trace management."""
    
    def __init__(self):
        self.client: Optional[Langfuse] = None
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize Langfuse client if available and configured."""
        if not LANGFUSE_AVAILABLE:
            print("Langfuse not available. Install with: pip install langfuse")
            return
        
        if not config.is_langfuse_enabled():
            print("Langfuse not configured. Skipping initialization.")
            return
        
        try:
            self.client = Langfuse(
                host=config.LANGFUSE_HOST,
                public_key=config.LANGFUSE_PUBLIC_KEY,
                secret_key=config.LANGFUSE_SECRET_KEY
            )
            print("Langfuse initialized successfully")
        except Exception as e:
            print(f"Failed to initialize Langfuse: {e}")
            self.client = None
    
    def create_trace(self, name: str, input_data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None):
        """Create a new trace."""
        if not self.client:
            return None
        
        try:
            # Use the correct Langfuse 3.x API
            trace_id = self.client.create_trace_id()
            trace = self.client.start_span(
                name=name,
                input=input_data,
                metadata=metadata or {},
                trace_id=trace_id
            )
            return trace
        except Exception as e:
            print(f"Failed to create trace: {e}")
            return None
    
    def create_span(self, trace, name: str, input_data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None):
        """Create a new span within a trace."""
        if not self.client:
            return None
        
        try:
            # Create a child span
            span = self.client.start_span(
                name=name,
                input=input_data,
                metadata=metadata or {}
            )
            return span
        except Exception as e:
            print(f"Failed to create span: {e}")
            return None
    
    def flush(self) -> None:
        """Flush pending traces."""
        if self.client:
            try:
                self.client.flush()
            except Exception as e:
                print(f"Failed to flush Langfuse: {e}")
    
    @property
    def is_enabled(self) -> bool:
        """Check if Langfuse is enabled and available."""
        return self.client is not None

# Global Langfuse instance
langfuse_config = LangfuseConfig()
