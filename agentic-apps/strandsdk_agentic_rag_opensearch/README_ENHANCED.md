# Enhanced Multi-Agent RAG with Strands SDK and Langfuse Tracing

This project implements a sophisticated multi-agent Large Language Model (LLM) system using the **Strands SDK** with comprehensive **Langfuse observability integration**. The system combines Model Context Protocol (MCP) for tool usage and Retrieval Augmented Generation (RAG) for enhanced context awareness, using OpenSearch as the vector database.

## 🚀 What's New in the Enhanced Version

### Advanced Langfuse Integration
- **Native Strands SDK Integration**: Built-in callback handlers for comprehensive tracing
- **Real-time Streaming Tracing**: Track streaming responses and tool calls in real-time
- **Session & User Tracking**: Maintain conversation context across interactions
- **Comprehensive Observability**: Trace agent execution, tool calls, embeddings, and errors
- **Performance Monitoring**: Track response times, token usage, and system performance

### Enhanced Agent Architecture
- **Streaming Support**: Real-time response streaming with full tracing
- **Session Management**: Persistent conversation tracking across interactions
- **Error Recovery**: Robust error handling with detailed trace logging
- **Multi-modal Tracing**: Support for text, tool calls, and embedding operations

## 🏗️ Architecture

The enhanced system uses a modular multi-agent architecture with integrated observability:

```
Enhanced SupervisorAgent (Orchestrator + Tracing)
├── Enhanced KnowledgeAgent → RAG with embedding tracing
├── Enhanced MCPAgent → Tool interactions with execution tracing
├── Strands SDK → Native agent framework with callback integration
└── Langfuse Integration → Comprehensive observability and monitoring
```

## 🚀 Key Features

### Multi-Agent Orchestration with Tracing
- **Enhanced SupervisorAgent**: Main orchestrator with integrated RAG and comprehensive tracing
- **Session-aware Agents**: Maintain context across conversations with session tracking
- **Tool Execution Tracing**: Monitor all tool calls, inputs, outputs, and performance
- **Error Tracing**: Detailed error tracking and recovery monitoring

### Advanced RAG Capabilities with Observability
- **OpenSearch Integration**: Vector storage with search performance tracing
- **Embedding Tracing**: Monitor embedding generation and similarity searches
- **Multi-format Support**: Handles markdown, text, JSON, CSV with processing traces
- **Intelligent Search**: Vector similarity search with detailed performance metrics

### Comprehensive Langfuse Integration
- **Native Callback Handlers**: Built-in Strands SDK callback integration
- **Streaming Tracing**: Real-time trace updates during response streaming
- **Tool Call Monitoring**: Detailed tracing of MCP tool executions
- **Performance Analytics**: Response times, token usage, and success rates

## 📋 Prerequisites

- Python 3.9+
- OpenAI API key or compatible LLM endpoint
- AWS OpenSearch Domain
- AWS credentials configured
- Langfuse account (optional but recommended for observability)

## 🛠️ Installation

```bash
# Clone the repository
git clone <repository-url>
cd strandsdk_agentic_rag_opensearch

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies (includes enhanced Langfuse integration)
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration (see Configuration section)
```

## ⚙️ Configuration

Create a `.env` file with the following variables:

```env
# LLM Configuration
OPENAI_API_KEY=your-api-key-or-litellm-key
OPENAI_BASE_URL=https://your-litellm-endpoint/v1
DEFAULT_MODEL=us.anthropic.claude-3-7-sonnet-20250219-v1:0

# Embedding Configuration
EMBEDDING_BASE_URL=https://bedrock-runtime.us-west-2.amazonaws.com
EMBEDDING_MODEL=amazon.titan-embed-text-v2:0
EMBEDDING_KEY=not_needed_for_aws_credentials

# AWS Configuration  
AWS_REGION=us-west-2
OPENSEARCH_ENDPOINT=https://your-opensearch-domain.region.es.amazonaws.com

# Langfuse Configuration (Enhanced Observability)
LANGFUSE_HOST=https://cloud.langfuse.com
LANGFUSE_PUBLIC_KEY=pk-lf-your-public-key
LANGFUSE_SECRET_KEY=sk-lf-your-secret-key

# Application Settings
KNOWLEDGE_DIR=knowledge
OUTPUT_DIR=output
VECTOR_INDEX_NAME=knowledge-embeddings
TOP_K_RESULTS=5
```

## 🏃‍♂️ Running the Enhanced System

### 1. Setup OpenSearch and Knowledge Base

```bash
# First, set up your OpenSearch cluster (if not already done)
./setup-opensearch.sh

# Process and embed knowledge documents
python -c "
from src.agents.knowledge_agent import knowledge_agent_with_langfuse
print(knowledge_agent_with_langfuse('Please embed all knowledge files'))
"
```

### 2. Run the Enhanced Interactive System

```bash
# Start the enhanced interactive system with full tracing
source venv/bin/activate
python -m src.enhanced_main

# Or run with async streaming support
python -m src.enhanced_main --async
```

### 3. Run Single Queries with Tracing

```bash
# Single query with session tracking
python -m src.enhanced_main --query "What is Bell's palsy and how is it treated?"

# Or programmatically
python -c "
from src.enhanced_main import run_single_query
result = run_single_query('What are the symptoms of Bell\'s palsy?', session_id='test-session')
print(result)
"
```

### 4. Run the Original System (Backward Compatibility)

```bash
# Original system still available
python -m src.main
```

## 🔍 Enhanced Usage Examples

### Interactive Mode with Session Tracking

```bash
$ python -m src.enhanced_main

🚀 Enhanced Multi-Agent RAG System Ready!
✨ Features: Strands SDK + Langfuse Tracing + Session Tracking
Ask questions and I'll use my specialized agents with full observability.
Type 'exit', 'quit', or press Ctrl+C to exit.
📊 Session ID: 550e8400-e29b-41d4-a716-446655440000
🔍 Langfuse tracing: ENABLED

❓ Your question: What is Bell's palsy?

🔄 Processing request #1...
============================================================
Bell's palsy is a condition that causes sudden weakness or paralysis 
of the muscles on one side of the face...
============================================================
📊 Trace logged to Langfuse

❓ Your question: session
📊 Current session ID: 550e8400-e29b-41d4-a716-446655440000
💬 Conversation count: 1

❓ Your question: exit
👋 Goodbye!

📊 Session Summary:
   Session ID: 550e8400-e29b-41d4-a716-446655440000
   Total conversations: 1
   Langfuse tracing: ENABLED
```

### Async Streaming Mode

```bash
$ python -m src.enhanced_main --async

🚀 Enhanced Multi-Agent RAG System (Async Streaming Mode)
✨ Features: Real-time streaming + Langfuse Tracing
Ask questions and see responses stream in real-time.

❓ Your question: Explain the treatment options for Bell's palsy

🔄 Streaming response #1...
============================================================
Based on the medical literature, Bell's palsy treatment typically involves...
[Response streams in real-time with full tracing]
============================================================
📊 Streaming trace logged to Langfuse
```

### Programmatic Usage with Enhanced Tracing

```python
from src.agents.enhanced_supervisor_agent import (
    enhanced_supervisor_agent_with_tracing,
    ask_enhanced_supervisor
)

# Simple usage
response = ask_enhanced_supervisor(
    "What are the risk factors for Bell's palsy?",
    session_id="my-session",
    user_id="user-123"
)
print(response)

# Advanced usage with custom session tracking
response = enhanced_supervisor_agent_with_tracing(
    query="Compare Bell's palsy with other facial nerve disorders",
    session_id="medical-consultation-456",
    user_id="doctor-789"
)
```

### Batch Processing with Session Tracking

```python
from src.enhanced_main import run_batch_queries

queries = [
    "What is Bell's palsy?",
    "What are the symptoms?", 
    "How is it diagnosed?",
    "What are the treatment options?"
]

responses = run_batch_queries(
    queries, 
    session_id="batch-medical-queries"
)

for i, response in enumerate(responses):
    print(f"Q{i+1}: {queries[i]}")
    print(f"A{i+1}: {response}\n")
```

## 🧪 Testing the Enhanced System

### Run Comprehensive Tests

```bash
# Test all enhanced components
python -m src.test_agents

# Test Langfuse integration specifically
python -m src.examples.langfuse_integration_example
```

### Test Individual Components

```python
# Test enhanced supervisor agent
from src.agents.enhanced_supervisor_agent import ask_enhanced_supervisor
response = ask_enhanced_supervisor("Test query with tracing")

# Test Langfuse integration
from src.utils.strands_langfuse_integration import strands_langfuse
print(f"Langfuse enabled: {strands_langfuse.is_enabled}")
```

## 📊 Observability and Monitoring

### Langfuse Dashboard Features

1. **Conversation Tracking**: View complete conversation flows with session IDs
2. **Agent Performance**: Monitor response times and success rates
3. **Tool Usage Analytics**: Track which tools are used most frequently
4. **Error Analysis**: Detailed error tracking and debugging information
5. **Token Usage**: Monitor LLM token consumption and costs
6. **Search Performance**: Track embedding and retrieval performance

### Accessing Langfuse Traces

1. **Login to Langfuse**: Visit your Langfuse host URL
2. **Navigate to Traces**: View real-time traces of agent interactions
3. **Session Analysis**: Filter traces by session ID or user ID
4. **Performance Metrics**: Analyze response times and success rates
5. **Error Investigation**: Drill down into failed interactions

### Key Metrics Tracked

- **Response Time**: End-to-end query processing time
- **Tool Execution Time**: Individual tool call performance
- **Search Performance**: Embedding generation and similarity search times
- **Token Usage**: Input/output tokens for cost tracking
- **Success Rates**: Query success vs. failure rates
- **Session Analytics**: User engagement and conversation patterns

## 🔧 Advanced Configuration

### Custom Langfuse Integration

```python
from src.utils.strands_langfuse_integration import StrandsLangfuseIntegration

# Create custom integration
custom_langfuse = StrandsLangfuseIntegration()

# Create custom callback handler
callback = custom_langfuse.create_strands_callback_handler(
    trace_name="custom-agent",
    user_id="custom-user",
    session_id="custom-session",
    metadata={"custom": "metadata"}
)

# Use with any Strands agent
from strands import Agent
agent = Agent(
    model="your-model",
    tools=[],
    callback_handler=callback
)
```

### Environment-Specific Configuration

```bash
# Development environment
export LANGFUSE_HOST=http://localhost:3000
export DEFAULT_MODEL=gpt-4o-mini

# Production environment  
export LANGFUSE_HOST=https://cloud.langfuse.com
export DEFAULT_MODEL=us.anthropic.claude-3-7-sonnet-20250219-v1:0
```

## 🚀 Deployment Options

### Local Development

```bash
# Run with development settings
python -m src.enhanced_main
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "-m", "src.enhanced_main"]
```

### API Server Mode

```python
# Create a FastAPI server with the enhanced system
from fastapi import FastAPI
from src.enhanced_main import run_single_query

app = FastAPI()

@app.post("/query")
async def query_endpoint(query: str, session_id: str = None):
    response = run_single_query(query, session_id=session_id)
    return {"response": response, "session_id": session_id}
```

## 🔍 Troubleshooting

### Common Issues

1. **Langfuse Not Connecting**
   ```bash
   # Check environment variables
   echo $LANGFUSE_HOST
   echo $LANGFUSE_PUBLIC_KEY
   
   # Test connection
   python -c "from src.utils.strands_langfuse_integration import strands_langfuse; print(strands_langfuse.is_enabled)"
   ```

2. **OpenSearch Connection Issues**
   ```bash
   # Test OpenSearch connectivity
   python -c "from src.tools.embedding_retriever import EmbeddingRetriever; r = EmbeddingRetriever(); print(r.get_document_count())"
   ```

3. **Model Endpoint Issues**
   ```bash
   # Test model connectivity
   python -c "from src.utils.model_providers import get_reasoning_model; print(get_reasoning_model())"
   ```

### Debug Mode

```bash
# Run with debug logging
export LOG_LEVEL=DEBUG
python -m src.enhanced_main
```

## 📈 Performance Optimization

### Recommended Settings

```env
# For high-throughput scenarios
TOP_K_RESULTS=3
MAX_QUERY_LENGTH=1000
MAX_RESPONSE_LENGTH=5000

# For detailed tracing
LANGFUSE_FLUSH_INTERVAL=1
TRACE_ALL_TOOLS=true
```

### Monitoring Performance

```python
# Monitor system performance
from src.utils.strands_langfuse_integration import strands_langfuse

# Check trace statistics
if strands_langfuse.is_enabled:
    print("Langfuse tracing active - check dashboard for metrics")
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/enhanced-tracing`)
3. Make your changes with comprehensive tracing
4. Add tests for new functionality
5. Ensure Langfuse integration works
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🎯 Quick Start Summary

1. **Install**: `pip install -r requirements.txt`
2. **Configure**: Copy `.env.example` to `.env` and fill in your settings
3. **Setup Knowledge**: Run OpenSearch setup and embed documents
4. **Run Enhanced System**: `python -m src.enhanced_main`
5. **Monitor**: Check Langfuse dashboard for comprehensive observability

The enhanced system provides the same functionality as the original with added comprehensive observability, session tracking, and streaming support through native Strands SDK integration with Langfuse.
