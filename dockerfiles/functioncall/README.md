# Weather Function Call Service for EKS

This service provides a FastAPI application that uses LLM function calling capabilities to retrieve weather information. It's designed to run in an Amazon EKS cluster.

## Features

- Current weather information for any city
- Weather forecasts for up to 16 days
- LLM-powered chat interface with function calling capabilities
- Health check endpoints

## Environment Variables

The application can be configured using the following environment variables:

- `LLM_SERVER_URL`: URL of the LLM server (default: "http://llm-service:8080/v1/chat/completions")
- `LLM_API_KEY`: API key for the LLM service (default: "sk-1234")
- `CONNECT_TIMEOUT`: Connection timeout in seconds (default: 10)
- `READ_TIMEOUT`: Read timeout in seconds (default: 300)
- `LLM_MAX_RETRIES`: Maximum number of retries for LLM requests (default: 3)

## Building and Running

### Build the Docker image

```bash
docker build -t weather-function-service:latest .
```

### Run locally

```bash
docker run -p 8000:8000 \
  -e LLM_SERVER_URL="http://your-llm-server:8080/v1/chat/completions" \
  -e LLM_API_KEY="your-api-key" \
  weather-function-service:latest
```

## Deploying to EKS

1. Push the image to a container registry (ECR, Docker Hub, etc.)
2. Apply the Kubernetes deployment manifest

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: weather-function-service
spec:
  replicas: 2
  selector:
    matchLabels:
      app: weather-function-service
  template:
    metadata:
      labels:
        app: weather-function-service
    spec:
      containers:
      - name: weather-function-service
        image: your-registry/weather-function-service:latest
        ports:
        - containerPort: 8000
        env:
        - name: LLM_SERVER_URL
          value: "http://llm-service:8080/v1/chat/completions"
        - name: LLM_API_KEY
          valueFrom:
            secretKeyRef:
              name: llm-credentials
              key: api-key
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

3. Create a service to expose the deployment

```yaml
apiVersion: v1
kind: Service
metadata:
  name: weather-function-service
spec:
  selector:
    app: weather-function-service
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
```

## API Endpoints

- `POST /weather/current`: Get current weather for a city
- `POST /weather/forecast`: Get weather forecast for a city
- `POST /chat`: Chat with the LLM using weather functions
- `GET /health`: Health check endpoint
- `GET /health/llm`: LLM health check endpoint
