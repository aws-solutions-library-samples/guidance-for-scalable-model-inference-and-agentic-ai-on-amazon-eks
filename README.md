# Cost Effective and Scalable Model Inference and Agentic AI on AWS Graviton with EKS

## Overview
This solution implements a comprehensive, scalable ML inference architecture using Amazon EKS, leveraging both Graviton processors for cost-effective CPU-based inference and GPU instances for accelerated inference. The system provides a complete end-to-end platform for deploying large language models with agentic AI capabilities, including RAG (Retrieval Augmented Generation) and intelligent document processing.

## Architecture
![Architecture Diagram](image/arch.png)

The architecture diagram illustrates our scalable ML inference solution with the following components:

1. **Amazon EKS Cluster**: The foundation of our architecture, providing a managed Kubernetes environment with automated provisioning and configuration.
   
2. **Karpenter Auto-scaling**: Dynamically provisions and scales compute resources based on workload demands across multiple node pools.
   
3. **Node Pools**:
   - **Graviton-based nodes (ARM64)**: Cost-effective CPU inference using m8g/c8g instances
   - **GPU-based nodes (x86_64)**: High-performance inference using NVIDIA GPU instances (g5, g6 families)
   - **x86-based nodes**: General purpose compute for compatibility requirements
   
4. **Model Hosting Services**:
   - **Ray Serve**: Distributed model serving with automatic scaling
   - **Standalone Services**: Direct model deployment for specific use cases
   - **Multi-modal Support**: Text, vision, and reasoning model capabilities
   
5. **Model Gateway**: 
   - **LiteLLM Proxy**: Unified OpenAI-compatible API gateway with load balancing and routing
   - **Ingress Controller**: External access management with SSL termination
   
6. **Agentic AI Applications**:
   - **RAG with OpenSearch**: Intelligent document retrieval and question answering
   - **Intelligent Document Processing (IDP)**: Automated document analysis and extraction
   - **Multi-Agent Systems**: Coordinated AI workflows with specialized agents
   
7. **Observability & Monitoring**: 
   - **Langfuse**: LLM observability and performance tracking
   - **Prometheus & Grafana**: Infrastructure monitoring and alerting

This architecture provides flexibility to choose between cost-optimized CPU inference on Graviton processors or high-throughput GPU inference based on your specific requirements, all while maintaining elastic scalability through Kubernetes and Karpenter.

## Quick Start Guide

We provide two approaches to set up the complete solution:

### Option 1: Automated Setup with Makefile (Recommended)

For the fastest and most reliable setup, use our automated Makefile:

#### Prerequisites
- EKS cluster set up following the [AWS Solutions Guidance: Automated Provisioning of Application-Ready Amazon EKS Clusters](https://aws.amazon.com/solutions/guidance/automated-provisioning-of-application-ready-amazon-eks-clusters/)
- `kubectl` configured to access your cluster
- Required CLI tools installed (`pnpm`, `pip`, etc.)

#### Complete Installation
```bash
# Install all core components (base infrastructure, models, gateway, observability)
make install

# Or for development setup only (base + models + gateway)
make dev-setup
```

#### Individual Components
```bash
# Install specific components as needed
make setup-base           # Base infrastructure
make setup-models         # Model hosting services
make setup-gateway        # LiteLLM proxy gateway
make setup-observability  # Langfuse monitoring
make setup-milvus         # Milvus vector database
make setup-idp            # Intelligent Document Processing
make setup-rag            # RAG with OpenSearch
```

#### Utility Commands
```bash
make help                 # Show all available targets
make status               # Check deployment status
make verify-cluster       # Verify EKS cluster access
make clean                # Remove all deployments
```

### Option 2: Manual Step-by-Step Setup

If you prefer manual control or need to customize the installation:

#### Step 1: Set Up EKS Cluster

Set up your EKS cluster using the AWS Solutions Guidance for automated provisioning:

**Follow the [AWS Solutions Guidance: Automated Provisioning of Application-Ready Amazon EKS Clusters](https://aws.amazon.com/solutions/guidance/automated-provisioning-of-application-ready-amazon-eks-clusters/)**

This guidance provides:
- Automated EKS cluster provisioning with best practices
- Pre-configured add-ons and operators
- Security and networking configurations
- Monitoring and observability setup

After completing the guidance, ensure your `kubectl` is configured to access the cluster:

```bash
# Verify cluster access
kubectl cluster-info
kubectl get nodes
```

#### Step 2: Install Base Infrastructure Components

Navigate to the base setup directory and run the installation script:

```bash
cd base_eks_setup
chmod +x install_operators.sh
./install_operators.sh
```

This script installs:
- KubeRay Operator for distributed model serving
- NVIDIA GPU Operator for GPU workloads
- GP3 storage class for optimized storage
- All Karpenter node pools for different workload types

#### Step 3: Deploy Model Hosting Services

Set up the model hosting infrastructure:

```bash
cd model-hosting
chmod +x setup.sh
./setup.sh
```

This deploys:
- Ray service with LlamaCPP and embedding capabilities
- Standalone vLLM reasoning service
- Standalone vLLM vision service
- All necessary Kubernetes resources and configurations

#### Step 4: Deploy Model Gateway

Set up the unified API gateway:

```bash
cd model-gateway
chmod +x setup.sh
./setup.sh
```

This deploys:
- LiteLLM proxy deployment
- Load balancer and ingress configuration
- Waits for services to be ready before proceeding

**Important**: After deployment, configure LiteLLM:
1. Access the LiteLLM web interface
2. Login with username "admin" and password "sk-123456"
3. Go to "Virtual Keys" on the sidebar and create a new key
4. Mark "All Team Models" for the models field
5. Store the generated secret key - you'll need it for the agentic applications

#### Step 5: Set Up Observability

Deploy monitoring and observability tools:

```bash
cd model-observability
chmod +x setup.sh
./setup.sh
```

This installs:
- Langfuse for LLM observability
- Web ingress for external access
- Service monitoring and logging

**Important**: After deployment, configure Langfuse:
1. Access Langfuse web interface
2. Create an organization named "test"
3. Create a project inside it named "demo"
4. Go to "Tracing" menu and set up tracing
5. Record the Public Key (PK) and Secret Key (SK) - you'll need these for the agentic applications

#### Step 6: Deploy Agentic Applications

##### Option A: Intelligent Document Processing (IDP)

Set up the IDP application for automated document analysis:

```bash
cd agentic-apps/agentic-idp

# Create and configure environment file
cp .env.example .env
# Edit .env with your configuration:
# - LLAMA_VISION_MODEL_KEY=your-litellm-virtual-key (from Step 4)
# - API_GATEWAY_URL=your-litellm-gateway-url
# - LANGFUSE_HOST=your-langfuse-endpoint
# - LANGFUSE_PUBLIC_KEY=your-langfuse-public-key (from Step 5)
# - LANGFUSE_SECRET_KEY=your-langfuse-secret-key (from Step 5)

# Install dependencies
pip install -r requirements.txt

# Run the IDP application
python agentic_idp.py
```

##### Option B: RAG with OpenSearch

Set up the RAG application with OpenSearch vector database:

```bash
cd agentic-apps/agentic_rag_opensearch

# Set up OpenSearch cluster
chmod +x setup-opensearch.sh
./setup-opensearch.sh

# Create and configure environment file
cp .env.example .env
# Edit .env with your configuration:
# - OPENAI_API_KEY=your-litellm-virtual-key (from Step 4)
# - OPENAI_BASE_URL=your-model-endpoint-url
# - LANGFUSE_HOST=your-langfuse-endpoint
# - LANGFUSE_PUBLIC_KEY=your-langfuse-public-key (from Step 5)
# - LANGFUSE_SECRET_KEY=your-langfuse-secret-key (from Step 5)
# Note: OPENSEARCH_ENDPOINT and AWS_REGION are automatically set by setup-opensearch.sh

# Install dependencies
pnpm install

# Embed knowledge documents
pnpm embed-knowledge

# Run the multi-agent RAG application
pnpm dev
```

## Post-Installation Configuration

After running either installation method, you'll need to configure the following:

### LiteLLM Configuration
1. Access the LiteLLM web interface
2. Login with username "admin" and password "sk-123456"
3. Go to "Virtual Keys" on the sidebar and create a new key
4. Mark "All Team Models" for the models field
5. Store the generated secret key for use in agentic applications

### Langfuse Configuration
1. Access Langfuse web interface
2. Create an organization named "test"
3. Create a project inside it named "demo"
4. Go to "Tracing" menu and set up tracing
5. Record the Public Key (PK) and Secret Key (SK) for use in agentic applications

## Makefile Reference

The Makefile provides comprehensive automation for the entire deployment process. Here's a detailed breakdown of all available targets:

### Core Installation Targets

| Target | Description | Dependencies |
|--------|-------------|--------------|
| `make install` | Complete installation of all core components | `verify-cluster`, `setup-base`, `setup-models`, `setup-gateway`, `setup-observability` |
| `make dev-setup` | Quick development setup (core components only) | `verify-cluster`, `setup-base`, `setup-models`, `setup-gateway` |

### Individual Component Targets

| Target | Description | What it installs |
|--------|-------------|------------------|
| `make setup-base` | Base infrastructure components | KubeRay Operator, NVIDIA GPU Operator, GP3 storage class, Karpenter node pools |
| `make setup-models` | Model hosting services | Ray service with LlamaCPP, vLLM reasoning service, vLLM vision service |
| `make setup-gateway` | Model gateway | LiteLLM proxy deployment, load balancer, ingress configuration |
| `make setup-observability` | Monitoring and observability | Langfuse for LLM observability, web ingress |
| `make setup-milvus` | Vector database | Milvus standalone deployment with cert-manager and EBS storage |
| `make setup-idp` | Intelligent Document Processing | Environment setup and dependency installation |
| `make setup-rag` | RAG with OpenSearch | OpenSearch cluster setup and Node.js dependencies |

### Utility Targets

| Target | Description | Use case |
|--------|-------------|----------|
| `make help` | Show all available targets and prerequisites | Getting started, reference |
| `make verify-cluster` | Verify EKS cluster access | Troubleshooting, pre-installation check |
| `make status` | Check deployment status across all namespaces | Monitoring, troubleshooting |
| `make clean` | Remove all deployments | Cleanup, fresh start |
| `make setup-function-calling` | Deploy function calling service | Agentic AI with external tool integration |
| `make setup-benchmark` | Performance benchmarking setup instructions | Performance testing |

### Advanced Features

The Makefile includes several advanced features for better user experience:

- **Sequential Dependencies**: Each target automatically runs its prerequisites
- **Environment File Management**: Automatically creates `.env` templates with configuration instructions
- **Error Handling**: Graceful handling of missing files and failed operations
- **Status Feedback**: Clear progress indicators and next-step instructions
- **Configuration Reminders**: Important post-deployment configuration steps for LiteLLM and Langfuse

### Example Workflows

#### Complete Setup
```bash
# One command to set up everything
make install
```

#### Development Workflow
```bash
# Quick setup for development
make dev-setup

# Add specific components as needed
make setup-milvus
make setup-idp
```

#### Troubleshooting
```bash
# Check cluster connectivity
make verify-cluster

# Check deployment status
make status

# Clean up and start fresh
make clean
make install
```

#### Component-by-Component Setup
```bash
# Install components individually with full control
make setup-base
make setup-models
make setup-gateway
make setup-observability
```

## Detailed Component Information

## Deployment Options

### Option 1: CPU-based Inference with llama.cpp on Graviton

Deploy an elastic Ray service hosting llama 3.2 model on Graviton:

#### 1. Edit your Hugging Face token for env `HUGGING_FACE_HUB_TOKEN` in the secret section of `ray-service-llamacpp-with-function-calling.yaml`

#### 2. Configure model and inference parameters in the yaml file:
   - `MODEL_ID`: Hugging Face model repository
   - `MODEL_FILENAME`: Model file name in the Hugging Face repo
   - `N_THREADS`: Number of threads for inference (recommended: match host EC2 instance vCPU count)
   - `CMAKE_ARGS`: C/C++ compile flags for llama.cpp on Graviton

> Note: The example model uses GGUF format, optimized for llama.cpp. See [GGUF documentation](https://huggingface.co/docs/hub/en/gguf) for details. You can find out different quantization version for the model, check these hugging face repo: https://huggingface.co/bartowski or https://huggingface.co/unsloth  
> Note: To run function call, better with reasoning model like Qwen-QwQ-32B in this example

#### 3. Create the Kubernetes service:
```bash
kubectl create -f ray-service-llamacpp-with-function-calling.yaml
```

#### 4. Get the Kubernetes service name:
```bash
kubectl get svc
```

### Option 2: GPU-based Inference with vLLM

Deploy an elastic Ray service hosting models on GPU instances using vLLM:

#### 1. Edit your Hugging Face token for env `HUGGING_FACE_HUB_TOKEN` in the secret section of `ray-service-vllm-with-function-calling.yaml`

#### 2. Configure model and inference parameters in the yaml file:
   - `MODEL_ID`: Hugging Face model repository (default: mistralai/Mistral-7B-Instruct-v0.2)
   - `GPU_MEMORY_UTILIZATION`: Percentage of GPU memory to utilize (default: 0.9)
   - `MAX_MODEL_LEN`: Maximum sequence length for the model (default: 8192)
   - `MAX_NUM_SEQ`: Maximum number of sequences to process in parallel (default: 4)
   - `MAX_NUM_BATCHED_TOKENS`: Maximum number of tokens in a batch (default: 32768)
   - `ENABLE_FUNCTION_CALLING`: Set to "true" to enable function calling support

#### 3. Create the Kubernetes service:
```bash
kubectl create namespace rayserve-vllm
kubectl create -f ray-service-vllm-with-function-calling.yaml
```

#### 4. Get the Kubernetes service name:
```bash
kubectl get svc -n rayserve-vllm
```

## Agentic AI with Function Calling

This solution supports building agentic AI applications that can leverage either CPU-based (llama.cpp) or GPU-based (vLLM) model inference backends. The agent architecture enables models to call external functions and services.

### Understanding Agentic AI and Function Calling

Agentic AI refers to AI systems that can act autonomously to achieve specific goals by making decisions and taking actions. In this solution, we implement agentic capabilities through function calling, which allows language models to:

1. **Recognize when to use tools**: The model identifies when external data or capabilities are needed to fulfill a user request
2. **Structure function calls**: The model generates properly formatted function calls with appropriate parameters
3. **Process function results**: The model incorporates returned data into its responses

Function calling enables models to bridge the gap between natural language understanding and external systems, allowing them to:

- Access real-time information (like weather data in our example)
- Perform calculations or data transformations
- Interact with external APIs and services
- Execute specific actions based on user requests

Our implementation provides a framework where the model:
- Parses user intent from natural language
- Determines which function to call and with what parameters
- Makes the API call through a dedicated service
- Processes the returned information to generate a coherent response

This approach significantly extends the capabilities of language models beyond their pre-trained knowledge, making them more useful for real-world applications.

### Deploying the Function Service

#### 1. Configure the function service:
The function service is defined in `agent/kubernetes/combined.yaml` and includes:
- A Kubernetes Secret for API credentials
- A Deployment for the function service (weather service example)
- A LoadBalancer Service to expose the function API

#### 2. Deploy the function service:
```bash
kubectl apply -f agent/kubernetes/combined.yaml
```

#### 3. Configure your model backend for function calling:
- For CPU-based inference: Use `ray-service-llamacpp-with-function-calling.yaml`
- For GPU-based inference: Use `ray-service-vllm-with-function-calling.yaml` with `ENABLE_FUNCTION_CALLING: "true"`

#### 4. Test function calling:
Once deployed, you can test the weather function service using a simple curl command:

```bash
curl -X POST http://<YOUR-LOAD-BALANCER-URL>/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the current weather in London?"}'
```
```bash
curl -X POST http://<YOUR-LOAD-BALANCER-URL>/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the future 2 days weather in London?"}'
```

The service will:
1. Process your natural language query
2. Identify the need to call the weather function
3. Make the appropriate API call
4. Return the weather information in a conversational format

## Installing Milvus Vector Database in EKS

Milvus is an open-source vector database that powers embedding similarity search and AI applications. This section guides you through deploying Milvus on your EKS cluster with Graviton processors.

### Prerequisites

- Your EKS cluster is already set up with Graviton (ARM64) nodes
- Cert-manager is installed on the cluster
- AWS EBS CSI driver is configured for persistent storage

### Deployment Steps

#### 1. Install cert-manager (if not already installed):
```bash
kubectl apply -f https://github.com/jetstack/cert-manager/releases/download/v1.5.3/cert-manager.yaml
kubectl get pods -n cert-manager
```

#### 2. Install Milvus Operator:
```bash
kubectl apply -f https://raw.githubusercontent.com/zilliztech/milvus-operator/main/deploy/manifests/deployment.yaml
kubectl get pods -n milvus-operator
```

#### 3. Create EBS Storage Class:
```bash
kubectl apply -f milvus/ebs-storage-class.yaml
```

#### 4. Deploy Milvus in standalone mode:
```bash
kubectl apply -f milvus/milvus-standalone.yaml
```

#### 5. Create Network Load Balancer Service (optional, for external access):
```bash
kubectl apply -f milvus/milvus-nlb-service.yaml
```

#### 6. Access Milvus:
You can access Milvus using port-forwarding:
```bash
kubectl port-forward service/my-release-milvus 19530:19530
```

Or through the Network Load Balancer if you deployed the NLB service.

## Deploying MCP (Model Context Protocol) Service

The MCP service enables augmented LLM capabilities by combining tool usage with Retrieval Augmented Generation (RAG) for enhanced context awareness. This implementation is framework-independent, not relying on LangChain or LlamaIndex.

### Architecture

The MCP service consists of several modular components:
- **Agent**: Coordinates workflow and manages tool usage
- **ChatOpenAI**: Handles interactions with the language model and tool calling
- **MCPClient**: Connects to MCP servers and manages tool calls
- **EmbeddingRetriever**: Creates and searches vector embeddings for relevant context
- **VectorStore**: Interfaces with Milvus for storing and retrieving embeddings

### Workflow

1. **Knowledge Embedding**
   - Documents from the `knowledge` directory are converted to vector embeddings
   - Embeddings and source documents are stored in Milvus vector database

2. **Context Retrieval (RAG)**
   - User queries are converted to embeddings
   - The system finds relevant documents by calculating similarity between embeddings
   - Top matching documents form context for the LLM

3. **MCP Tool Setup**
   - MCP clients connect to tool servers (e.g., filesystem operations)
   - Tools are registered with the agent

4. **Task Execution**
   - User tasks are processed by the LLM with retrieved context
   - The LLM may use tools via MCP clients
   - Tool results are fed back to the LLM to continue the conversation

### Deployment Steps

#### 1. Set up environment variables:
Create a `.env` file in the `mcp` directory with:
```
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=your_openai_model_inference_endpoint
EMBEDDING_BASE_URL=https://bedrock-runtime.us-west-2.amazonaws.com
EMBEDDING_KEY=not_needed_for_aws_credentials
AWS_REGION=us-west-2
MILVUS_ADDRESS=your_milvus_service_address
```

#### 2. Install dependencies:
```bash
cd mcp
pnpm install
```

#### 3. Run the application:
```bash
pnpm dev
```

#### 4. Extend the system:
This modular architecture can be extended by:
- Adding more MCP servers for additional tool capabilities
- Implementing advanced Milvus features like filtering and hybrid search
- Adding more sophisticated RAG techniques
- Implementing conversation history for multi-turn interactions
- Deploying as a service with API endpoints

## Performance Benchmarking

Our client program will generate prompts with different concurrency for each run. Every run will have common GenAI related prompts and assemble them into standard HTTP requests, and concurrency calls will keep increasing until the maximum CPU usage reaches to nearly 100%. We capture the total time from when a HTTP request is initiated to when a HTTP response is received as the latency metric of model performance. We also capture output token generated per second as throughput. The test aims to reach maximum CPU utilization on the worker pods to assess the concurrency performance.

Follow this guidance if you want to set it up and replicate the experiment

### 1. Launch load generator instance
Launch an EC2 instance as the client in the same AZ with the Ray cluster (For optimal performance testing, deploy a client EC2 instance in the same AZ as your Ray cluster. To generate sufficient load, use a compute-optimized instance like c6i.16xlarge. If you observe that worker node CPU utilization remains flat despite increasing concurrent requests, this indicates your test client may be reaching its capacity limits. In such cases, scale your testing infrastructure by launching additional EC2 instances to generate higher concurrent loads.)

### 2. Execute port forward for the ray service
```bash
kubectl port-forward service/ray-service-llamacpp-serve-svc 8000:8000
```

### 3. Configure environment
Install Golang environment in the client EC2 instance (please refer [this](https://go.dev/doc/install) for the Golang installation guidance). Specify the environment variables as the test configuration.

```bash
export URL=http://localhost:8000/v1/chat/completions
export REQUESTS_PER_PROMPT=<The_number_of_concurrent_calls>
export NUM_WARMUP_REQUESTS=<The_number_of_warmup_requests>
```

### 4. Run test
Run the performance test golang script and you can find the results from the output.

```bash
go run perf_benchmark.go
```

## Contact
Please contact wangaws@ or fmamazon@ if you want to know more and/or contribute.
