# Makefile for Cost Effective and Scalable Model Inference on AWS Graviton with EKS
# This Makefile automates the deployment of the complete ML inference solution

.PHONY: help install setup-base setup-models setup-gateway setup-observability setup-idp setup-rag setup-milvus clean verify-cluster

# Default target
help:
	@echo "Available targets:"
	@echo "  install           - Complete installation of all components"
	@echo "  verify-cluster    - Verify EKS cluster access"
	@echo "  setup-base        - Install base infrastructure components"
	@echo "  setup-models      - Deploy model hosting services"
	@echo "  setup-gateway     - Deploy model gateway (LiteLLM)"
	@echo "  setup-observability - Deploy monitoring and observability"
	@echo "  setup-idp         - Setup Intelligent Document Processing"
	@echo "  setup-rag         - Setup RAG with OpenSearch"
	@echo "  setup-milvus      - Install Milvus vector database"
	@echo "  clean             - Clean up all deployments"
	@echo ""
	@echo "Prerequisites:"
	@echo "  - EKS cluster must be set up following AWS Solutions Guidance"
	@echo "  - kubectl configured to access the cluster"
	@echo "  - Required environment variables configured"

# Complete installation
install: verify-cluster setup-base setup-models setup-gateway setup-observability
	@echo "✅ Complete installation finished!"
	@echo ""
	@echo "Next steps:"
	@echo "1. Configure LiteLLM:"
	@echo "   - Access LiteLLM web interface"
	@echo "   - Login with username 'admin' and password 'sk-123456'"
	@echo "   - Create a virtual key in 'Virtual Keys' section"
	@echo "   - Mark 'All Team Models' for the models field"
	@echo ""
	@echo "2. Configure Langfuse:"
	@echo "   - Access Langfuse web interface"
	@echo "   - Create organization 'test' and project 'demo'"
	@echo "   - Record Public Key (PK) and Secret Key (SK)"
	@echo ""
	@echo "3. Deploy agentic applications:"
	@echo "   - Run 'make setup-idp' for Intelligent Document Processing"
	@echo "   - Run 'make setup-rag' for RAG with OpenSearch"

# Verify cluster access
verify-cluster:
	@echo "🔍 Verifying EKS cluster access..."
	kubectl cluster-info
	kubectl get nodes
	@echo "✅ Cluster verification complete"

# Setup base infrastructure
setup-base: verify-cluster
	@echo "🚀 Installing base infrastructure components..."
	cd base_eks_setup && chmod +x install_operators.sh && ./install_operators.sh
	@echo "✅ Base infrastructure setup complete"

# Setup model hosting services
setup-models: setup-base
	@echo "🤖 Deploying model hosting services..."
	cd model-hosting && chmod +x setup.sh && ./setup.sh
	@echo "✅ Model hosting services deployed"

# Setup model gateway
setup-gateway: setup-models
	@echo "🌐 Deploying model gateway..."
	cd model-gateway && chmod +x setup.sh && ./setup.sh
	@echo "✅ Model gateway deployed"
	@echo ""
	@echo "⚠️  IMPORTANT: Configure LiteLLM after deployment:"
	@echo "   1. Access LiteLLM web interface"
	@echo "   2. Login with username 'admin' and password 'sk-123456'"
	@echo "   3. Go to 'Virtual Keys' and create a new key"
	@echo "   4. Mark 'All Team Models' for the models field"
	@echo "   5. Store the generated secret key for agentic applications"

# Setup observability
setup-observability: setup-gateway
	@echo "📊 Deploying observability tools..."
	cd model-observability && chmod +x setup.sh && ./setup.sh
	@echo "✅ Observability tools deployed"
	@echo ""
	@echo "⚠️  IMPORTANT: Configure Langfuse after deployment:"
	@echo "   1. Access Langfuse web interface"
	@echo "   2. Create organization 'test' and project 'demo'"
	@echo "   3. Go to 'Tracing' menu and set up tracing"
	@echo "   4. Record Public Key (PK) and Secret Key (SK)"

# Setup Intelligent Document Processing
setup-idp:
	@echo "📄 Setting up Intelligent Document Processing..."
	@if [ ! -f agentic-apps/agentic-idp/.env ]; then \
		echo "Creating .env file from template..."; \
		cd agentic-apps/agentic-idp && cp .env.example .env; \
		echo "⚠️  Please edit agentic-apps/agentic-idp/.env with your configuration"; \
		echo "   - LLAMA_VISION_MODEL_KEY=your-litellm-virtual-key"; \
		echo "   - API_GATEWAY_URL=your-litellm-gateway-url"; \
		echo "   - LANGFUSE_HOST=your-langfuse-endpoint"; \
		echo "   - LANGFUSE_PUBLIC_KEY=your-langfuse-public-key"; \
		echo "   - LANGFUSE_SECRET_KEY=your-langfuse-secret-key"; \
		echo ""; \
		echo "After configuring .env, run: cd agentic-apps/agentic-idp && pip install -r requirements.txt && python agentic_idp.py"; \
	else \
		echo "Installing Python dependencies..."; \
		cd agentic-apps/agentic-idp && pip install -r requirements.txt; \
		echo "✅ IDP setup complete. Run: cd agentic-apps/agentic-idp && python agentic_idp.py"; \
	fi

# Setup RAG with OpenSearch
setup-rag:
	@echo "🔍 Setting up RAG with OpenSearch..."
	cd agentic-apps/agentic_rag_opensearch && chmod +x setup-opensearch.sh && ./setup-opensearch.sh
	@if [ ! -f agentic-apps/agentic_rag_opensearch/.env ]; then \
		echo "Creating .env file from template..."; \
		cd agentic-apps/agentic_rag_opensearch && cp .env.example .env; \
		echo "⚠️  Please edit agentic-apps/agentic_rag_opensearch/.env with your configuration"; \
		echo "   - OPENAI_API_KEY=your-litellm-virtual-key"; \
		echo "   - OPENAI_BASE_URL=your-model-endpoint-url"; \
		echo "   - LANGFUSE_HOST=your-langfuse-endpoint"; \
		echo "   - LANGFUSE_PUBLIC_KEY=your-langfuse-public-key"; \
		echo "   - LANGFUSE_SECRET_KEY=your-langfuse-secret-key"; \
		echo ""; \
		echo "After configuring .env, run the following commands:"; \
		echo "   cd agentic-apps/agentic_rag_opensearch"; \
		echo "   pnpm install"; \
		echo "   pnpm embed-knowledge"; \
		echo "   pnpm dev"; \
	else \
		echo "Installing Node.js dependencies..."; \
		cd agentic-apps/agentic_rag_opensearch && pnpm install; \
		echo "✅ RAG setup complete. Run the following commands:"; \
		echo "   cd agentic-apps/agentic_rag_opensearch"; \
		echo "   pnpm embed-knowledge"; \
		echo "   pnpm dev"; \
	fi

# Setup Milvus vector database
setup-milvus:
	@echo "🗄️  Installing Milvus vector database..."
	@echo "Installing cert-manager..."
	kubectl apply -f https://github.com/jetstack/cert-manager/releases/download/v1.5.3/cert-manager.yaml
	@echo "Waiting for cert-manager to be ready..."
	kubectl wait --for=condition=ready pod -l app=cert-manager -n cert-manager --timeout=300s
	@echo "Installing Milvus operator..."
	kubectl apply -f https://raw.githubusercontent.com/zilliztech/milvus-operator/main/deploy/manifests/deployment.yaml
	kubectl wait --for=condition=ready pod -l control-plane=controller-manager -n milvus-operator --timeout=300s
	@echo "Creating EBS storage class..."
	kubectl apply -f milvus/ebs-storage-class.yaml
	@echo "Deploying Milvus standalone..."
	kubectl apply -f milvus/milvus-standalone.yaml
	@echo "Creating Network Load Balancer service..."
	kubectl apply -f milvus/milvus-nlb-service.yaml
	@echo "✅ Milvus installation complete"

# Function calling setup
setup-function-calling:
	@echo "🔧 Setting up function calling service..."
	kubectl apply -f agent/kubernetes/combined.yaml
	@echo "✅ Function calling service deployed"
	@echo ""
	@echo "Test function calling with:"
	@echo "curl -X POST http://<YOUR-LOAD-BALANCER-URL>/chat \\"
	@echo "  -H \"Content-Type: application/json\" \\"
	@echo "  -d '{\"message\": \"What is the current weather in London?\"}'"

# Performance benchmarking setup
setup-benchmark:
	@echo "📊 Setting up performance benchmarking..."
	@echo "Please ensure you have:"
	@echo "1. Launched a client EC2 instance in the same AZ as your Ray cluster"
	@echo "2. Installed Golang on the client instance"
	@echo "3. Set environment variables:"
	@echo "   export URL=http://localhost:8000/v1/chat/completions"
	@echo "   export REQUESTS_PER_PROMPT=<concurrent_calls>"
	@echo "   export NUM_WARMUP_REQUESTS=<warmup_requests>"
	@echo "4. Run: kubectl port-forward service/ray-service-llamacpp-serve-svc 8000:8000"
	@echo "5. Execute: go run perf_benchmark.go"

# Clean up all deployments
clean:
	@echo "🧹 Cleaning up deployments..."
	@echo "Removing agentic applications..."
	-kubectl delete -f agent/kubernetes/combined.yaml 2>/dev/null || true
	@echo "Removing Milvus..."
	-kubectl delete -f milvus/milvus-nlb-service.yaml 2>/dev/null || true
	-kubectl delete -f milvus/milvus-standalone.yaml 2>/dev/null || true
	-kubectl delete -f milvus/ebs-storage-class.yaml 2>/dev/null || true
	@echo "Removing observability..."
	-cd model-observability && kubectl delete -f . 2>/dev/null || true
	@echo "Removing model gateway..."
	-cd model-gateway && kubectl delete -f . 2>/dev/null || true
	@echo "Removing model hosting..."
	-cd model-hosting && kubectl delete -f . 2>/dev/null || true
	@echo "Removing base infrastructure..."
	-cd base_eks_setup && kubectl delete -f . 2>/dev/null || true
	@echo "✅ Cleanup complete"

# Status check
status:
	@echo "📋 Checking deployment status..."
	@echo ""
	@echo "Namespaces:"
	kubectl get namespaces
	@echo ""
	@echo "Pods across all namespaces:"
	kubectl get pods --all-namespaces
	@echo ""
	@echo "Services:"
	kubectl get services --all-namespaces
	@echo ""
	@echo "Ingresses:"
	kubectl get ingress --all-namespaces

# Quick development setup (models + gateway only)
dev-setup: verify-cluster setup-base setup-models setup-gateway
	@echo "✅ Development setup complete!"
	@echo "Core components (base, models, gateway) are ready for development."
