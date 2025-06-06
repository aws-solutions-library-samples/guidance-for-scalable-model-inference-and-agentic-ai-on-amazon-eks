FROM python:3.9-slim

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY server.py weather_service.py ./

# Set environment variables with default values
# These can be overridden when running the container
ENV LLM_SERVER_URL="http://llm-service:8080/v1/chat/completions" \
    LLM_API_KEY="sk-1234" \
    LLM_MODEL="llama3" \
    CONNECT_TIMEOUT=10 \
    READ_TIMEOUT=300 \
    LLM_MAX_RETRIES=3

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
