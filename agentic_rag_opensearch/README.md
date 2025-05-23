# Agentic RAG with MCP and OpenSearch

This project implements an augmented Large Language Model (LLM) system that combines Model Context Protocol (MCP) for tool usage and Retrieval Augmented Generation (RAG) for enhanced context awareness, using OpenSearch as the vector database.

## Project Overview

This application creates an AI agent that can:
1. Retrieve relevant information from a knowledge base using vector embeddings stored in OpenSearch
2. Interact with external tools through the Model Context Protocol (MCP)
3. Generate responses based on both the retrieved context and tool interactions
4. Complete tasks like summarizing content and saving results to files

## Architecture

The system is built with a modular architecture consisting of these key components:

```
Agent → Manages the overall workflow and coordinates components
  ├── ChatOpenAI → Handles LLM interactions and tool calling
  ├── MCPClient → Connects to MCP servers for tool access
  └── EmbeddingRetriever → Performs vector search for relevant context
      └── OpenSearchVectorStore → Stores and searches document embeddings
```

## Workflow Explanation

1. **Initialization**:
   - The system loads knowledge documents and creates embeddings
   - Embeddings are stored in an AWS OpenSearch Serverless vector database
   - MCP client is initialized to connect to filesystem tool server

2. **RAG Process**:
   - When a query is received, it's converted to an embedding
   - The system searches for the most relevant documents using cosine similarity in OpenSearch
   - Retrieved documents are combined to form context for the LLM

3. **Agent Execution**:
   - The agent initializes with the LLM, MCP client, and retrieved context
   - The user query is sent to the LLM along with the context
   - The LLM generates responses and may request tool calls

4. **Tool Usage**:
   - When the LLM requests a tool, the agent routes the call to the MCP client
   - The MCP client executes the tool and returns results
   - Results are fed back to the LLM to continue the conversation

## Key Components

- **Agent**: Coordinates the overall workflow and manages tool usage
- **ChatOpenAI**: Handles interactions with the language model and tool calling
- **MCPClient**: Connects to MCP servers and manages tool calls
- **EmbeddingRetriever**: Creates and searches vector embeddings for relevant context
- **OpenSearchVectorStore**: Interfaces with OpenSearch for storing and retrieving embeddings

## Getting Started

### Prerequisites

- Node.js 18+
- pnpm or npm
- OpenAI API key
- AWS OpenSearch Serverless collection
- AWS credentials configured

### Installation

```bash
# Clone the repository
git clone <repository-url>

# Install dependencies
pnpm install

# Set up environment variables
# Create a .env file with:
OPENAI_API_KEY=your-api-key
OPENAI_BASE_URL=your-model-hosting-endpoint
OPENSEARCH_ENDPOINT=your-opensearch-endpoint
AWS_REGION=your-aws-region
```

### Usage

```bash
# Embed md files knowledge documents
pnpm embed-knowledge

# Embed CSV files knowledge documents
pnpm embed-csv

# Run the application
pnpm dev
```

## Example Use Case

The current implementation demonstrates a task where the agent:
1. Retrieves information about a specific topic from the knowledge base
2. Summarizes the information and creates a story
3. Saves the output to a markdown file using the filesystem MCP tool

## Extending the System

This modular architecture can be easily extended:
- Add more MCP servers for additional tool capabilities
- Implement advanced OpenSearch features like filtering and hybrid search
- Add more sophisticated RAG techniques like reranking or chunking
- Implement conversation history for multi-turn interactions
- Deploy as a service with API endpoints
- Integrate with different LLM providers
- Scale the vector database for production workloads
