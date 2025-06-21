# Web Search Integration with Tavily API

This document explains the new web search capabilities integrated into the multi-agent RAG system using Tavily API as an MCP server.

## 🌐 Overview

The system now automatically determines when to use web search based on RAG relevance scores:

- **RAG Relevance Score ≥ 0.3**: Uses knowledge base results
- **RAG Relevance Score < 0.3**: Automatically triggers web search for real-time information

## 🏗️ Architecture

```
SupervisorAgent
├── search_knowledge_base() → Returns relevance_score
├── web_search_when_needed() → Auto-triggers based on relevance
├── search_recent_news() → Dedicated news search
└── Tavily MCP Server (localhost:8002/mcp)
    ├── web_search tool
    ├── news_search tool
    └── health_check tool
```

## 🚀 Setup

### 1. Get Tavily API Key

1. Visit [https://tavily.com](https://tavily.com)
2. Sign up for an account
3. Get your API key from the dashboard

### 2. Configure Environment

Add to your `.env` file:
```env
TAVILY_API_KEY=your-tavily-api-key-here
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Start Tavily MCP Server

```bash
# Option 1: Using the startup script
python scripts/start_tavily_server.py

# Option 2: Direct server start
python src/mcp_servers/tavily_search_server.py
```

The server will start on:
- Health check: `http://localhost:8001/health`
- MCP endpoint: `http://localhost:8002/mcp`

## 🔧 Usage

### Automatic Web Search

The system automatically decides when to use web search:

```python
# This query likely has low RAG relevance → triggers web search
result = supervisor_agent("What happened in the news today?")

# This query likely has high RAG relevance → uses knowledge base
result = supervisor_agent("What is Bell's palsy?")
```

### Explicit Web Search

Force web search for current information:

```python
result = supervisor_agent("Use web search to find the latest AI developments")
```

### News Search

Search for recent news specifically:

```python
result = supervisor_agent("Find recent news about artificial intelligence")
```

## 🛠️ Available Tools

### 1. `web_search_when_needed`

Automatically determines if web search is needed based on RAG relevance.

**Parameters:**
- `query` (str): Search query
- `rag_relevance_score` (float): RAG relevance score (0.0-1.0)
- `max_results` (int): Maximum results to return

**Example Response:**
```json
{
  "web_search_performed": true,
  "query": "latest AI developments",
  "answer": "Recent AI developments include...",
  "results": [
    {
      "title": "Latest AI Breakthrough",
      "url": "https://example.com/article",
      "content": "Summary of the article...",
      "score": 0.95,
      "published_date": "2024-01-15"
    }
  ],
  "search_reason": "RAG relevance (0.2) below threshold (0.3)"
}
```

### 2. `search_recent_news`

Dedicated news search for current events.

**Parameters:**
- `query` (str): News search query
- `days_back` (int): How many days back to search (default: 7)
- `max_results` (int): Maximum results to return

### 3. `search_knowledge_base`

Enhanced RAG search that now returns relevance scores.

**Enhanced Response:**
```json
{
  "results": [...],
  "relevance_score": 0.75,
  "total_results": 3,
  "query": "your search query"
}
```

## 📊 Relevance Scoring

The system calculates relevance scores to determine search strategy:

### Score Calculation
- **Vector similarity scores**: Primary relevance indicator
- **Content length**: Secondary indicator for quality
- **Result count**: Availability of relevant information

### Thresholds
- **≥ 0.7**: High relevance - excellent RAG results
- **0.3-0.7**: Medium relevance - good RAG results
- **< 0.3**: Low relevance - triggers web search

## 🔍 Query Examples

### High RAG Relevance (Uses Knowledge Base)
```python
# Medical knowledge (assuming medical docs in knowledge base)
"What are the symptoms of Bell's palsy?"
"How is facial paralysis treated?"
"What causes neurological disorders?"

# Technical documentation
"How to configure OpenSearch?"
"What is vector similarity search?"
```

### Low RAG Relevance (Triggers Web Search)
```python
# Current events
"What happened in the news today?"
"Latest stock market updates"
"Recent political developments"

# Real-time information
"Current weather in New York"
"Today's cryptocurrency prices"
"Live sports scores"
```

### Hybrid Queries (May Use Both)
```python
# Combines foundational knowledge + current trends
"What is machine learning and what are the latest developments?"
"Explain blockchain technology and recent innovations"
"What are neural networks and current research trends?"
```

## 🧪 Testing

### Run Integration Tests
```bash
python src/test_web_search_integration.py
```

### Manual Testing
```python
from src.agents.supervisor_agent import supervisor_agent

# Test automatic web search triggering
result = supervisor_agent("What are today's top technology news?")
print(result)

# Test RAG with high relevance
result = supervisor_agent("What is artificial intelligence?")
print(result)
```

### Health Check
```bash
curl http://localhost:8001/health
```

## 🔧 Configuration

### Relevance Threshold

Modify the threshold in `supervisor_agent.py`:

```python
# Current default
RELEVANCE_THRESHOLD = 0.3

# More aggressive web search (lower threshold)
RELEVANCE_THRESHOLD = 0.2

# More conservative web search (higher threshold)
RELEVANCE_THRESHOLD = 0.5
```

### Search Parameters

Customize search behavior:

```python
# In web_search_when_needed tool
max_results = 10  # More results
search_depth = "advanced"  # Deeper search
include_domains = ["reuters.com", "bbc.com"]  # Specific sources
```

## 📈 Performance Considerations

### Token Usage
- Web search results are truncated to 500 characters per result
- RAG results are truncated to 300 characters per result
- Relevance scoring adds minimal overhead

### Rate Limiting
- Tavily API has rate limits based on your plan
- The system includes 2-second delays between requests in tests
- Consider caching for frequently requested information

### Fallback Strategy
- If Tavily MCP server is unavailable, system falls back to RAG-only
- Health checks ensure service availability
- Graceful error handling for API failures

## 🚨 Troubleshooting

### Common Issues

1. **"Tavily MCP client not available"**
   - Check if the MCP server is running
   - Verify the server is accessible at `localhost:8002/mcp`
   - Check server logs for errors

2. **"TAVILY_API_KEY environment variable is required"**
   - Ensure API key is set in `.env` file
   - Restart the application after adding the key

3. **"Web search failed"**
   - Check your Tavily API key validity
   - Verify internet connectivity
   - Check Tavily service status

### Debug Mode

Enable detailed logging:

```python
import logging
logging.getLogger().setLevel(logging.DEBUG)
```

### Server Logs

Check MCP server logs:
```bash
python src/mcp_servers/tavily_search_server.py
```

## 🔮 Future Enhancements

### Planned Features
- **Caching**: Cache web search results to reduce API calls
- **Source Ranking**: Prioritize trusted news sources
- **Multi-language**: Support for non-English queries
- **Custom Filters**: Domain-specific search filters
- **Analytics**: Track search patterns and relevance accuracy

### Integration Opportunities
- **Slack/Discord**: Real-time notifications for news searches
- **Scheduled Searches**: Periodic updates on specific topics
- **Email Summaries**: Daily/weekly digest of relevant information
- **Custom Dashboards**: Visual representation of search trends

## 📚 References

- [Tavily API Documentation](https://docs.tavily.com)
- [Strands SDK Documentation](https://docs.strands.ai)
- [MCP Protocol Specification](https://modelcontextprotocol.io)
- [OpenTelemetry Tracing](https://opentelemetry.io)
