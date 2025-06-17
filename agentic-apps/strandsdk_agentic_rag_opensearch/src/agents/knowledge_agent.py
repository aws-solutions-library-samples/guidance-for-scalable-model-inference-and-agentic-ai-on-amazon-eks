"""Knowledge Agent using Strands SDK patterns."""

import os
import json
import hashlib
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import pandas as pd
from strands import Agent, tool
from strands_tools import file_read, file_write
from ..tools.embedding_retriever import EmbeddingRetriever
from ..config import config
from ..utils.logging import log_title
from ..utils.langfuse_config import langfuse_config
from ..utils.model_providers import get_reasoning_model

logger = logging.getLogger(__name__)

@tool
def scan_knowledge_directory() -> str:
    """
    Scan the knowledge directory for files and return metadata.
    
    Returns:
        JSON string with file metadata
    """
    # Create Langfuse span for directory scan
    scan_span = langfuse_config.create_span(
        trace=None,
        name="knowledge-directory-scan",
        input_data={"knowledge_dir": config.KNOWLEDGE_DIR}
    )
    
    try:
        knowledge_dir = Path(config.KNOWLEDGE_DIR)
        if not knowledge_dir.exists():
            result = json.dumps({"error": "Knowledge directory does not exist"})
            
            if scan_span and langfuse_config.is_enabled:
                scan_span.end(output={"error": "Directory not found", "success": False})
            
            return result
        
        files_info = []
        for file_path in knowledge_dir.rglob("*"):
            if file_path.is_file() and file_path.suffix in [".md", ".txt", ".json", ".csv"]:
                stat = file_path.stat()
                files_info.append({
                    "path": str(file_path.relative_to(knowledge_dir)),
                    "size": stat.st_size,
                    "modified": stat.st_mtime,
                    "type": file_path.suffix[1:]
                })
        
        result = json.dumps({
            "success": True,
            "files": files_info,
            "total_files": len(files_info)
        })
        
        # Update Langfuse span with results
        if scan_span and langfuse_config.is_enabled:
            scan_span.end(output={
                "total_files": len(files_info),
                "file_types": list(set(f["type"] for f in files_info)),
                "success": True
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Error scanning knowledge directory: {e}")
        error_result = json.dumps({"error": str(e)})
        
        if scan_span and langfuse_config.is_enabled:
            scan_span.end(output={"error": str(e), "success": False})
        
        return error_result

@tool
def embed_knowledge_files() -> str:
    """
    Process and embed all knowledge files.
    
    Returns:
        JSON string with embedding results
    """
    # Create Langfuse span for embedding operation
    embed_span = langfuse_config.create_span(
        trace=None,
        name="knowledge-files-embedding",
        input_data={"knowledge_dir": config.KNOWLEDGE_DIR}
    )
    
    try:
        knowledge_dir = Path(config.KNOWLEDGE_DIR)
        retriever = EmbeddingRetriever()
        
        embedded_count = 0
        total_files = 0
        processed_files = []
        
        for file_path in knowledge_dir.rglob("*"):
            if file_path.is_file() and file_path.suffix in [".md", ".txt", ".json", ".csv"]:
                total_files += 1
                try:
                    # Read file content
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Add to retriever
                    success = retriever.add_document(
                        content=content,
                        metadata={
                            "source": str(file_path.relative_to(knowledge_dir)),
                            "type": file_path.suffix[1:],
                            "size": len(content)
                        }
                    )
                    
                    if success:
                        embedded_count += 1
                        processed_files.append(str(file_path.relative_to(knowledge_dir)))
                    
                except Exception as e:
                    logger.error(f"Error processing file {file_path}: {e}")
        
        result = json.dumps({
            "success": True,
            "embedded_count": embedded_count,
            "total_files": total_files,
            "message": f"Successfully embedded {embedded_count} out of {total_files} files"
        })
        
        # Update Langfuse span with results
        if embed_span and langfuse_config.is_enabled:
            embed_span.end(output={
                "embedded_count": embedded_count,
                "total_files": total_files,
                "success_rate": embedded_count / total_files if total_files > 0 else 0,
                "processed_files": processed_files[:10],  # Limit to first 10 for brevity
                "success": True
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Error embedding knowledge files: {e}")
        error_result = json.dumps({"error": str(e)})
        
        if embed_span and langfuse_config.is_enabled:
            embed_span.end(output={"error": str(e), "success": False})
        
        return error_result

# Create the knowledge agent
knowledge_agent = Agent(
    model=get_reasoning_model(),
    tools=[scan_knowledge_directory, embed_knowledge_files, file_read, file_write],
    system_prompt="""
You are KnowledgeKeeper, a specialized agent for managing knowledge base operations. Your capabilities include:

1. **File Management**: Scan and monitor knowledge directory for files
2. **Content Processing**: Process markdown, text, JSON, and CSV files
3. **Embedding Operations**: Generate embeddings for knowledge documents
4. **Status Reporting**: Provide detailed reports on knowledge base status

**Available Tools:**
- scan_knowledge_directory: Scan the knowledge directory and return file metadata
- embed_knowledge_files: Process and embed all knowledge files
- file_read: Read content from specific files
- file_write: Write content to files

**Instructions:**
- Use scan_knowledge_directory to check what files are available
- Use embed_knowledge_files to process and embed all knowledge documents
- Provide detailed status reports and handle errors gracefully
- Focus on maintaining an up-to-date and well-organized knowledge base

Your goal is to ensure the knowledge base is current, properly indexed, and ready for retrieval operations.
"""
)

def knowledge_agent_with_langfuse(query: str) -> str:
    """
    Wrapper for knowledge agent with Langfuse tracing.
    
    Args:
        query: User query to process
        
    Returns:
        Agent response as string
    """
    # Create Langfuse trace for the knowledge operation
    trace = langfuse_config.create_trace(
        name="knowledge-agent-query",
        input_data={"query": query},
        metadata={
            "agent_type": "knowledge",
            "model": str(get_reasoning_model()),
            "timestamp": datetime.now().isoformat()
        }
    )
    
    try:
        start_time = datetime.now()
        
        # Call the Strands agent
        response = knowledge_agent(query)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Update trace with successful completion
        if trace and langfuse_config.is_enabled:
            trace.update(
                output={
                    "response": str(response),
                    "success": True,
                    "duration_seconds": duration,
                    "response_length": len(str(response))
                }
            )
        
        logger.info(f"Knowledge agent completed query in {duration:.2f} seconds")
        return str(response)
        
    except Exception as e:
        logger.error(f"Error in knowledge agent: {e}")
        
        # Update trace with error
        if trace and langfuse_config.is_enabled:
            trace.update(
                output={
                    "error": str(e),
                    "success": False,
                    "error_type": type(e).__name__
                }
            )
        
        return f"I apologize, but I encountered an error while processing your request: {str(e)}"
    
    finally:
        # Flush Langfuse traces
        if langfuse_config.is_enabled:
            langfuse_config.flush()

# Export both the original agent and the wrapped version
__all__ = ["knowledge_agent", "knowledge_agent_with_langfuse"]
