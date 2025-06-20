"""
Enhanced Langfuse integration for Strands Agent SDK.

This module provides comprehensive tracing capabilities that integrate with
Strands Agent SDK's native streaming and callback mechanisms.
"""

import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, field
from ..config import config

try:
    from langfuse import Langfuse
    from langfuse.decorators import observe
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False
    Langfuse = None
    observe = lambda func: func  # No-op decorator if Langfuse not available

logger = logging.getLogger(__name__)

@dataclass
class TraceContext:
    """Context for tracking trace information across agent execution."""
    trace_id: Optional[str] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    start_time: float = field(default_factory=time.time)
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    streaming_chunks: List[str] = field(default_factory=list)
    total_tokens: int = 0
    completion_tokens: int = 0
    prompt_tokens: int = 0

class StrandsLangfuseIntegration:
    """Enhanced Langfuse integration for Strands Agent SDK."""
    
    def __init__(self):
        self.client: Optional[Langfuse] = None
        self.current_trace: Optional[Any] = None
        self.current_generation: Optional[Any] = None
        self.trace_context: Optional[TraceContext] = None
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize Langfuse client if available and configured."""
        if not LANGFUSE_AVAILABLE:
            logger.warning("Langfuse not available. Install with: pip install langfuse")
            return
        
        if not config.is_langfuse_enabled():
            logger.info("Langfuse not configured. Skipping initialization.")
            return
        
        try:
            self.client = Langfuse(
                host=config.LANGFUSE_HOST,
                public_key=config.LANGFUSE_PUBLIC_KEY,
                secret_key=config.LANGFUSE_SECRET_KEY
            )
            logger.info("Langfuse initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Langfuse: {e}")
            self.client = None
    
    @property
    def is_enabled(self) -> bool:
        """Check if Langfuse is enabled and available."""
        return self.client is not None
    
    def create_strands_callback_handler(self, trace_name: str = "strands-agent-execution", 
                                      user_id: Optional[str] = None,
                                      session_id: Optional[str] = None,
                                      metadata: Optional[Dict[str, Any]] = None):
        """
        Create a callback handler for Strands Agent SDK that integrates with Langfuse.
        
        Args:
            trace_name: Name for the trace
            user_id: Optional user identifier
            session_id: Optional session identifier
            metadata: Additional metadata for the trace
            
        Returns:
            Callback handler function compatible with Strands Agent SDK
        """
        if not self.is_enabled:
            # Return a no-op callback handler if Langfuse is not available
            return lambda **kwargs: None
        
        # Initialize trace context
        self.trace_context = TraceContext(
            user_id=user_id,
            session_id=session_id,
            metadata=metadata or {}
        )
        
        def callback_handler(**kwargs):
            """Callback handler that processes Strands Agent SDK events."""
            try:
                self._process_strands_event(**kwargs)
            except Exception as e:
                logger.error(f"Error in Langfuse callback handler: {e}")
        
        return callback_handler
    
    def _process_strands_event(self, **kwargs):
        """Process events from Strands Agent SDK and update Langfuse traces."""
        if not self.is_enabled or not self.trace_context:
            return
        
        # Handle streaming data chunks
        if "data" in kwargs:
            self._handle_streaming_data(kwargs["data"])
        
        # Handle tool use events
        elif "current_tool_use" in kwargs:
            self._handle_tool_use(kwargs["current_tool_use"])
        
        # Handle model response events
        elif "model_response" in kwargs:
            self._handle_model_response(kwargs["model_response"])
        
        # Handle error events
        elif "error" in kwargs:
            self._handle_error(kwargs["error"])
    
    def _handle_streaming_data(self, data: str):
        """Handle streaming text data from the agent."""
        if self.trace_context:
            self.trace_context.streaming_chunks.append(data)
            
            # Update generation with streaming data
            if self.current_generation:
                try:
                    # For newer Langfuse versions, update the generation
                    self.current_generation.update(
                        completion=data,
                        metadata={
                            "streaming": True,
                            "chunk_count": len(self.trace_context.streaming_chunks)
                        }
                    )
                except Exception as e:
                    logger.debug(f"Could not update streaming generation: {e}")
    
    def _handle_tool_use(self, tool_use: Dict[str, Any]):
        """Handle tool use events from the agent."""
        if not self.trace_context:
            return
        
        tool_name = tool_use.get("name", "unknown_tool")
        tool_id = tool_use.get("toolUseId", "unknown_id")
        
        # Check if this is a new tool call
        existing_tool = next(
            (t for t in self.trace_context.tool_calls if t.get("id") == tool_id), 
            None
        )
        
        if not existing_tool:
            # Create new tool call record
            tool_call = {
                "id": tool_id,
                "name": tool_name,
                "input": tool_use.get("input", {}),
                "start_time": time.time(),
                "status": "running"
            }
            self.trace_context.tool_calls.append(tool_call)
            
            # Create Langfuse span for tool execution
            if self.current_trace:
                try:
                    tool_span = self.current_trace.span(
                        name=f"tool-{tool_name}",
                        input=tool_use.get("input", {}),
                        metadata={
                            "tool_id": tool_id,
                            "tool_name": tool_name
                        }
                    )
                    tool_call["langfuse_span"] = tool_span
                except Exception as e:
                    logger.debug(f"Could not create tool span: {e}")
        
        # Handle tool completion
        if "output" in tool_use:
            if existing_tool:
                existing_tool["output"] = tool_use["output"]
                existing_tool["end_time"] = time.time()
                existing_tool["status"] = "completed"
                
                # End the Langfuse span
                if "langfuse_span" in existing_tool:
                    try:
                        existing_tool["langfuse_span"].end(
                            output=tool_use["output"]
                        )
                    except Exception as e:
                        logger.debug(f"Could not end tool span: {e}")
    
    def _handle_model_response(self, response: Dict[str, Any]):
        """Handle model response events."""
        if self.trace_context:
            # Extract token usage if available
            usage = response.get("usage", {})
            self.trace_context.total_tokens = usage.get("total_tokens", 0)
            self.trace_context.completion_tokens = usage.get("completion_tokens", 0)
            self.trace_context.prompt_tokens = usage.get("prompt_tokens", 0)
    
    def _handle_error(self, error: Dict[str, Any]):
        """Handle error events from the agent."""
        if self.current_trace:
            try:
                self.current_trace.update(
                    level="ERROR",
                    status_message=str(error.get("message", "Unknown error")),
                    metadata={
                        "error_type": error.get("type", "unknown"),
                        "error_details": error
                    }
                )
            except Exception as e:
                logger.debug(f"Could not update trace with error: {e}")
    
    @observe(name="strands-agent-query")
    def trace_agent_execution(self, agent_func, query: str, **kwargs):
        """
        Decorator-style tracing for agent execution.
        
        Args:
            agent_func: The agent function to execute
            query: User query
            **kwargs: Additional arguments for the agent
            
        Returns:
            Agent response
        """
        if not self.is_enabled:
            return agent_func(query, **kwargs)
        
        try:
            # Create trace
            self.current_trace = self.client.trace(
                name="strands-agent-execution",
                input={"query": query, "kwargs": kwargs},
                metadata={
                    "agent_type": "strands",
                    "timestamp": datetime.now().isoformat(),
                    "session_id": self.trace_context.session_id if self.trace_context else None,
                    "user_id": self.trace_context.user_id if self.trace_context else None
                }
            )
            
            # Create generation for the main LLM call
            self.current_generation = self.current_trace.generation(
                name="agent-reasoning",
                input={"query": query},
                model=kwargs.get("model", "unknown"),
                metadata={"agent_execution": True}
            )
            
            # Execute the agent
            start_time = time.time()
            response = agent_func(query, **kwargs)
            end_time = time.time()
            
            # Update generation with response
            full_response = "".join(self.trace_context.streaming_chunks) if self.trace_context else str(response)
            
            self.current_generation.end(
                output={"response": full_response},
                usage={
                    "total_tokens": self.trace_context.total_tokens if self.trace_context else 0,
                    "completion_tokens": self.trace_context.completion_tokens if self.trace_context else 0,
                    "prompt_tokens": self.trace_context.prompt_tokens if self.trace_context else 0
                },
                metadata={
                    "execution_time": end_time - start_time,
                    "tool_calls_count": len(self.trace_context.tool_calls) if self.trace_context else 0,
                    "streaming_chunks": len(self.trace_context.streaming_chunks) if self.trace_context else 0
                }
            )
            
            # Update trace with final results
            self.current_trace.update(
                output={"response": full_response},
                metadata={
                    "execution_time": end_time - start_time,
                    "success": True,
                    "tool_calls": self.trace_context.tool_calls if self.trace_context else [],
                    "total_tokens": self.trace_context.total_tokens if self.trace_context else 0
                }
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error in traced agent execution: {e}")
            
            # Update trace with error
            if self.current_trace:
                self.current_trace.update(
                    level="ERROR",
                    status_message=str(e),
                    output={"error": str(e)},
                    metadata={"success": False, "error_type": type(e).__name__}
                )
            
            raise
        
        finally:
            # Clean up
            self.flush()
            self.current_trace = None
            self.current_generation = None
            self.trace_context = None
    
    def create_agent_with_tracing(self, agent_class, trace_name: str = "strands-agent", 
                                 user_id: Optional[str] = None,
                                 session_id: Optional[str] = None,
                                 **agent_kwargs):
        """
        Create a Strands Agent with built-in Langfuse tracing.
        
        Args:
            agent_class: Strands Agent class
            trace_name: Name for traces
            user_id: Optional user identifier
            session_id: Optional session identifier
            **agent_kwargs: Arguments for agent initialization
            
        Returns:
            Agent instance with tracing enabled
        """
        if not self.is_enabled:
            # Return regular agent if Langfuse is not available
            return agent_class(**agent_kwargs)
        
        # Create callback handler for tracing
        callback_handler = self.create_strands_callback_handler(
            trace_name=trace_name,
            user_id=user_id,
            session_id=session_id
        )
        
        # Add callback handler to agent kwargs
        agent_kwargs["callback_handler"] = callback_handler
        
        # Create and return the agent
        return agent_class(**agent_kwargs)
    
    def flush(self):
        """Flush pending traces to Langfuse."""
        if self.client:
            try:
                self.client.flush()
            except Exception as e:
                logger.error(f"Failed to flush Langfuse: {e}")

# Global instance
strands_langfuse = StrandsLangfuseIntegration()

# Convenience functions
def create_traced_agent(agent_class, **kwargs):
    """Create a Strands Agent with Langfuse tracing enabled."""
    return strands_langfuse.create_agent_with_tracing(agent_class, **kwargs)

def trace_agent_call(agent_func):
    """Decorator to trace agent function calls."""
    def wrapper(query: str, **kwargs):
        return strands_langfuse.trace_agent_execution(agent_func, query, **kwargs)
    return wrapper

# Export main components
__all__ = [
    "StrandsLangfuseIntegration",
    "strands_langfuse", 
    "create_traced_agent",
    "trace_agent_call",
    "TraceContext"
]
