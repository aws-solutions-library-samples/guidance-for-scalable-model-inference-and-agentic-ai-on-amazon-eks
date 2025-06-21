# Multi-Agent RAG with Strands SDK and OpenSearch

This project implements a sophisticated multi-agent Large Language Model (LLM) system using the **Strands SDK** that combines Model Context Protocol (MCP) for tool usage and Retrieval Augmented Generation (RAG) for enhanced context awareness, using OpenSearch as the vector database.

## 🏗️ Architecture

The system is built with a modular multi-agent architecture using Strands SDK patterns with built-in OpenTelemetry tracing:

```
SupervisorAgent (Orchestrator) [with built-in tracing]
├── KnowledgeAgent → Manages knowledge base and embeddings [traced]
├── MCPAgent → Manages tool interactions via MCP protocol [traced]
└── Strands SDK → Provides agent framework, tool integration, and OpenTelemetry tracing
```

## 🚀 Key Features

### Multi-Agent Orchestration
- **SupervisorAgent**: Main orchestrator with integrated RAG capabilities using Strands SDK
- **KnowledgeAgent**: Monitors and manages knowledge base changes
- **MCPAgent**: Executes tasks using MCP tools and file operations
- **Built-in Tracing**: All agents include OpenTelemetry tracing via Strands SDK

### Advanced RAG Capabilities
- **OpenSearch Integration**: Vector storage and similarity search
- **Embedding Generation**: Configurable embedding models and endpoints
- **Multi-format Support**: Handles markdown, text, JSON, and CSV files
- **Intelligent Search**: Vector similarity search with metadata and scoring

### MCP Tool Integration
- **Filesystem Operations**: Read, write, and manage files using Strands tools
- **Extensible Architecture**: Easy to add new MCP servers
- **Error Handling**: Robust tool execution with fallbacks
- **Built-in Tools**: Integration with Strands built-in tools

### Observability & Tracing
- **OpenTelemetry Integration**: Native tracing through Strands SDK
- **Multiple Export Options**: Console, OTLP endpoints, Jaeger, Langfuse
- **Automatic Instrumentation**: All agent interactions are automatically traced
- **Performance Monitoring**: Track execution times, token usage, and tool calls

## 📋 Prerequisites

- Python 3.9+
- OpenAI API key or compatible embedding endpoint
- AWS OpenSearch Domain
- AWS credentials configured

## 🛠️ Installation

```bash
# Clone the repository
git clone <repository-url>
cd strandsdk_agentic_rag_opensearch

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration
```

## ⚙️ Configuration

Create a `.env` file with the following variables:

```env
# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key
OPENAI_BASE_URL=https://api.openai.com/v1
DEFAULT_MODEL=us.anthropic.claude-3-7-sonnet-20250219-v1:0

# AWS Configuration  
AWS_REGION=us-east-1
OPENSEARCH_ENDPOINT=https://your-opensearch-domain.region.es.amazonaws.com

# Tracing Configuration (Optional)
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
OTEL_EXPORTER_OTLP_HEADERS=key1=value1,key2=value2
STRANDS_OTEL_ENABLE_CONSOLE_EXPORT=true

# Optional: Langfuse for observability
LANGFUSE_HOST=https://cloud.langfuse.com
LANGFUSE_PUBLIC_KEY=your-public-key
LANGFUSE_SECRET_KEY=your-secret-key

# Application Settings
KNOWLEDGE_DIR=knowledge
OUTPUT_DIR=output
VECTOR_INDEX_NAME=knowledge-embeddings
TOP_K_RESULTS=5
```

## 🏃‍♂️ Usage

### 1. Embed Knowledge Documents

```bash
# Process and embed all knowledge documents
python -c "from src.agents.knowledge_agent import knowledge_agent; print(knowledge_agent('Please embed all knowledge files'))"
```

### 2. Run the Multi-Agent System

```bash
# Start the interactive system (with built-in tracing)
source venv/bin/activate
python -m src.main

# Or run a single query
python -c "from src.main import run_single_query; print(run_single_query('What is Bell\'s palsy?'))"
```

### 3. Test the System

```bash
# Run comprehensive tests
python -m src.test_agents
```

## 🔍 Observability & Tracing

The system includes comprehensive observability through Strands SDK's built-in OpenTelemetry integration:

### Automatic Tracing
- **All agents** are automatically traced using Strands SDK
- **Tool calls**, **LLM interactions**, and **workflows** are captured
- **Performance metrics** including token usage and execution times

### Trace Export Options
- **Console Output**: Set `STRANDS_OTEL_ENABLE_CONSOLE_EXPORT=true` for development
- **OTLP Endpoint**: Configure `OTEL_EXPORTER_OTLP_ENDPOINT` for production
- **Langfuse**: Use Langfuse credentials for advanced observability
- **Jaeger/Zipkin**: Compatible with standard OpenTelemetry collectors

### Local Development Setup
```bash
# Pull and run Jaeger all-in-one container
docker run -d --name jaeger \
  -e COLLECTOR_OTLP_ENABLED=true \
  -p 16686:16686 \
  -p 4317:4317 \
  -p 4318:4318 \
  jaegertracing/all-in-one:latest

# Access Jaeger UI at http://localhost:16686
```

## 🧠 Agent Workflows

### Knowledge Management Workflow
1. **File Monitoring**: Scans knowledge directory for changes
2. **Change Detection**: Uses file hashes and timestamps
3. **Document Processing**: Handles multiple file formats
4. **Embedding Generation**: Creates vector embeddings
5. **Vector Storage**: Stores in OpenSearch with metadata

### RAG Retrieval Workflow  
1. **Query Processing**: Analyzes user queries
2. **Embedding Generation**: Converts queries to vectors
3. **Similarity Search**: Finds relevant documents in OpenSearch
4. **Context Formatting**: Structures results for LLM consumption
5. **Relevance Ranking**: Orders results by similarity scores

### MCP Tool Execution Workflow
1. **Tool Discovery**: Connects to available MCP servers
2. **Context Integration**: Combines RAG context with user queries
3. **Tool Selection**: Chooses appropriate tools for tasks
4. **Execution Management**: Handles tool calls and responses
5. **Result Processing**: Formats and returns final outputs

## 🔧 Extending the System

### Adding New Agents

### Adding New Agents

```python
from strands import Agent, tool
from src.utils.strands_langfuse_integration import create_traced_agent

# Define tools for the agent
@tool
def my_custom_tool(param: str) -> str:
    """Custom tool implementation."""
    return f"Processed: {param}"

# Create the agent with built-in tracing
my_agent = create_traced_agent(
    Agent,
    model="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    tools=[my_custom_tool],
    system_prompt="Your specialized prompt here",
    session_id="my-agent-session",
    user_id="system"
)
```

### Adding New MCP Servers

```python
from fastmcp import FastMCP

mcp = FastMCP("My Custom Server")

@mcp.tool(description="Custom tool description")
def my_custom_tool(param: str) -> str:
    """Custom tool implementation."""
    return f"Processed: {param}"

if __name__ == "__main__":
    mcp.run(transport="streamable-http", port=8002)
```

## 📊 Monitoring and Observability

The system includes comprehensive observability features:

- **OpenTelemetry Integration**: Native tracing through Strands SDK
- **Multiple Export Options**: Console, OTLP endpoints, Jaeger, Langfuse
- **Workflow Summaries**: Detailed execution reports
- **Performance Metrics**: Duration and success tracking
- **Error Handling**: Comprehensive error reporting and recovery

## 🧪 Example Use Cases

### Medical Knowledge Query
```python
query = "What are the symptoms and treatment options for Bell's palsy?"
result = supervisor_agent(query)
print(result['response'])
```

### Document Analysis and Report Generation
```python
query = "Analyze the medical documents and create a summary report saved to a file"
result = supervisor_agent(query)
# System will retrieve relevant docs, analyze them, and save results using MCP tools
```

## 🔍 Architecture Benefits

1. **Modularity**: Each agent has specific responsibilities
2. **Scalability**: Agents can be scaled independently  
3. **Reliability**: Isolated failures don't affect the entire system
4. **Extensibility**: Easy to add new capabilities
5. **Observability**: Comprehensive monitoring and tracing via Strands SDK
6. **Standards Compliance**: Uses MCP for tool integration and OpenTelemetry for tracing

## 🔧 Key Improvements

### Unified Architecture
- **Single Codebase**: No separate "enhanced" versions - all functionality is built into the standard agents
- **Built-in Tracing**: OpenTelemetry tracing is automatically enabled through Strands SDK
- **Simplified Deployment**: One main application with all features included
- **Consistent API**: All agents use the same tracing and configuration patterns

### Enhanced Developer Experience
- **Automatic Instrumentation**: No manual trace management required
- **Multiple Export Options**: Console, OTLP, Jaeger, Langfuse support out of the box
- **Environment-based Configuration**: Easy setup through environment variables
- **Clean Code Structure**: Removed duplicate wrapper functions and complex manual tracing

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
