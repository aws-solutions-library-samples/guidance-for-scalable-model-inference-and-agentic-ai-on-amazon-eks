# Enhanced RAG System with Chunk Relevance Evaluation

## Changes Made to supervisor_agent.py

### 1. Added RAGAs Evaluation Dependencies
- Imported `asyncio`, `re` for chunk processing
- Added `ChatBedrockConverse`, `SingleTurnSample`, `LLMContextPrecisionWithoutReference`, `LangchainLLMWrapper`
- Configured evaluation model with Claude 3.7 Sonnet

### 2. New Tool: check_chunks_relevance()
```python
@tool
def check_chunks_relevance(results: str, question: str):
    """
    Evaluates the relevance of retrieved chunks to the user question using RAGAs.
    
    Returns:
        dict: {"chunk_relevance_score": "yes"/"no", "chunk_relevance_value": float}
    """
```

### 3. Enhanced search_knowledge_base() Tool
- Added `formatted_for_evaluation` field to response
- Formats results with "Score:" and "Content:" patterns for RAGAs evaluation
- Maintains backward compatibility with existing JSON response format

### 4. Updated Agent Workflow
The new workflow follows these steps:

1. **Check Knowledge Base Status**: `check_knowledge_status()`
2. **Search Knowledge Base**: `search_knowledge_base(query)` - returns results with `formatted_for_evaluation`
3. **Evaluate Relevance**: `check_chunks_relevance(results=formatted_for_evaluation, question=original_query)`
4. **Decision Point**:
   - If `chunk_relevance_score` is "yes" (score > 0.5): Use RAG results
   - If `chunk_relevance_score` is "no" (score ≤ 0.5): Use web search via Tavily MCP
   - For time-sensitive queries: Skip evaluation, use web search directly
5. **File Writing**: Use `file_write(content, filename)` when needed

### 5. Updated System Prompts
- Enhanced prompts for both MCP-enabled and fallback agents
- Clear instructions for using the new evaluation workflow
- Transparency requirements for mentioning evaluation results

### 6. Tool Integration
- Added `check_chunks_relevance` to all agent configurations:
  - Main supervisor agent wrapper
  - Fresh supervisor agent creator
  - Fallback agents (without MCP)

## Benefits of the Enhanced System

1. **Intelligent Decision Making**: Uses RAGAs evaluation instead of simple similarity scores
2. **Reduced False Positives**: Advanced evaluation prevents irrelevant results from being used
3. **Hybrid Approach**: Seamlessly combines knowledge base and web search
4. **Transparency**: Users know which evaluation method was used and why
5. **Backward Compatibility**: Existing functionality remains unchanged

## Usage Example

```python
from src.agents.supervisor_agent import supervisor_agent

# The agent will automatically:
# 1. Check KB status
# 2. Search knowledge base
# 3. Evaluate chunk relevance using RAGAs
# 4. Use RAG results if relevant, otherwise web search
response = supervisor_agent("What are the symptoms of Bell's palsy?")
```

## Testing

Run the test script to verify the enhanced workflow:

```bash
python test_enhanced_rag.py
```

The system will now provide more accurate and relevant responses by intelligently choosing between knowledge base results and web search based on RAGAs evaluation scores.
