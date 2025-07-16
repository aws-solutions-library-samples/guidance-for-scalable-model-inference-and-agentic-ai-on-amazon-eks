# Makefile for Cost Effective and Scalable Model Inference on AWS Graviton with EKS
# This Makefile automates the deployment of the complete ML inference solution

.PHONY: help install setup-base setup-models setup-gateway setup-observability setup-idp setup-rag setup-rag-strands setup-milvus clean clean-pvcs clean-safe verify-cluster

# Default target
help:
	@echo "Available targets:"
	@echo "  install           - Complete installation of all components"
	@echo "  verify-cluster    - Verify EKS cluster access"
	@echo "  setup-base        - Install base infrastructure components (includes GP3 with Immediate binding)"
	@echo "  setup-models      - Deploy model hosting services"
	@echo "  setup-gateway     - Deploy model gateway (LiteLLM)"
	@echo "  setup-observability - Deploy monitoring and observability"
	@echo "  setup-idp         - Setup Intelligent Document Processing"
	@echo "  setup-rag         - Setup RAG with OpenSearch"
	@echo "  setup-rag-strands - Setup RAG with Strands SDK and OpenSearch (Kubernetes deployment)"
	@echo "  setup-milvus      - Install Milvus vector database"
	@echo "  clean             - Complete cleanup including PVCs and persistent resources"
	@echo "  clean-safe        - Safe cleanup (applications only, preserves data)"
	@echo "  clean-pvcs        - Remove only persistent volume claims and volumes"
	@echo "  status            - Check deployment status"
	@echo ""
	@echo "Storage Configuration:"
	@echo "  - GP3 storage class uses Immediate binding mode to prevent timeout issues"
	@echo "  - This ensures StatefulSets and complex workloads provision volumes correctly"
	@echo ""
	@echo "Prerequisites:"
	@echo "  - EKS cluster must be set up following AWS Solutions Guidance"
	@echo "  - kubectl configured to access the cluster"
	@echo "  - Required environment variables configured"

# Complete installation
install: verify-cluster setup-base setup-models setup-observability setup-gateway
	@echo "✅ Complete installation finished!"
	@echo ""
	@echo "Next steps:"
	@echo "1. Configure LiteLLM:"
	@echo "   - Access LiteLLM web interface"
	@echo "   - Login with username 'admin' and password 'sk-123456'"
	@echo "   - Create a virtual key in 'Virtual Keys' section"
	@echo "   - Mark 'All Team Models' for the models field"
	@echo "   - Note down the key value"
	@echo ""
	@echo "2. Deploy agentic applications:"
	@echo "   - Refer to the README for agentic application deployment"

# Verify cluster access
verify-cluster:
	@echo "🔍 Verifying EKS cluster access..."
	kubectl cluster-info
	kubectl get nodes
	@echo "✅ Cluster verification complete"

# Setup base infrastructure
setup-base: verify-cluster
	@echo "🚀 Installing base infrastructure components..."
	@echo "   - KubeRay Operator for distributed model serving"
	@echo "   - NVIDIA GPU Operator for GPU workloads"
	@echo "   - GP3 storage class with Immediate binding (prevents timeout issues)"
	@echo "   - Karpenter node pools for different workload types"
	cd base_eks_setup && chmod +x install_operators.sh && ./install_operators.sh
	@echo "✅ Base infrastructure setup complete"

# Setup model hosting services
setup-models: setup-base
	@echo "🤖 Deploying model hosting services..."
	cd model-hosting && chmod +x setup.sh && ./setup.sh
	@echo "✅ Model hosting services deployed"

# Setup observability
setup-observability: setup-models
	@echo "📊 Deploying observability tools..."
	@echo "⏱️  Note: Langfuse deployment may take up to 10 minutes to complete"
	cd model-observability && chmod +x setup.sh && ./setup.sh
	@echo "✅ Observability tools deployed"
	@echo ""
	@echo "⚠️  IMPORTANT: Configure Langfuse after deployment:"
	@echo "   1. Access Langfuse web interface"
	@echo "   2. Create organization 'test' and project 'demo'"
	@echo "   3. Go to 'Tracing' menu and set up tracing"
	@echo "   4. Record Public Key (PK) and Secret Key (SK)"

# Setup model gateway
setup-gateway: setup-observability
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

# Setup RAG with Strands SDK and OpenSearch (Kubernetes deployment)
setup-rag-strands:
	@echo "🔍 Setting up RAG with Strands SDK and OpenSearch..."
	@echo "📋 This will deploy a containerized multi-agent RAG system with:"
	@echo "   - SupervisorAgent (Orchestrator) with built-in tracing"
	@echo "   - KnowledgeAgent for managing knowledge base and embeddings"
	@echo "   - MCPAgent for tool interactions via MCP protocol"
	@echo "   - OpenSearch cluster for vector storage"
	@echo "   - Tavily web search integration"
	@echo "   - OpenTelemetry tracing with Langfuse integration"
	@echo ""
	@echo "⚠️  Prerequisites:"
	@echo "   - Python 3.9+"
	@echo "   - EKS cluster"
	@echo "   - TAVILY_API_KEY (https://docs.tavily.com/documentation/quickstart#get-your-free-tavily-api-key)"
	@echo "   - AWS credentials configured"
	@echo "   - Docker daemon in running status"
	@echo ""
	@echo "🚀 Starting deployment..."
	cd agentic-apps/strandsdk_agentic_rag_opensearch && chmod +x setup.sh && ./setup.sh
	@echo "✅ RAG with Strands SDK deployment complete!"

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

# Clean up all deployments including persistent volumes
clean:
	@echo "🧹 Cleaning up all deployments and persistent resources..."
	@echo ""
	@echo "⚠️  WARNING: This will delete ALL resources including persistent data!"
	@echo "📋 Resources that will be deleted:"
	@echo "   - All application deployments and services"
	@echo "   - All persistent volume claims and volumes"
	@echo "   - All custom storage classes"
	@echo "   - All secrets and configmaps (except system ones)"
	@echo "   - All custom resource definitions"
	@echo "   - All operators and system components"
	@echo "   - All custom namespaces"
	@echo "   - Base infrastructure components (KubeRay, NVIDIA operators, Karpenter nodepools)"
	@echo ""
	@echo "Press Ctrl+C within 15 seconds to cancel..."
	@sleep 15
	@echo ""
	@echo "🗑️  Removing agentic applications..."
	-kubectl delete -f agent/kubernetes/combined.yaml 2>/dev/null || true
	@echo "🗑️  Removing Strands SDK RAG applications..."
	-kubectl delete -f agentic-apps/strandsdk_agentic_rag_opensearch/k8s/ 2>/dev/null || true
	-kubectl delete ingress strandsdk-rag-ingress-alb 2>/dev/null || true
	-kubectl delete secret app-secrets 2>/dev/null || true
	-kubectl delete configmap app-config 2>/dev/null || true
	-kubectl delete serviceaccount strandsdk-rag-service-account 2>/dev/null || true
	@echo ""
	@echo "🗑️  Removing Milvus and related resources..."
	-kubectl delete -f milvus/milvus-nlb-service.yaml 2>/dev/null || true
	-kubectl delete -f milvus/milvus-standalone.yaml 2>/dev/null || true
	-kubectl delete -f milvus/ebs-storage-class.yaml 2>/dev/null || true
	@echo "Waiting for Milvus pods to terminate..."
	-kubectl wait --for=delete pod -l app=milvus --timeout=120s 2>/dev/null || true
	@echo ""
	@echo "🗑️  Removing observability components..."
	@echo "   Uninstalling Langfuse Helm release..."
	-helm uninstall langfuse 2>/dev/null || true
	-cd model-observability && kubectl delete -f . 2>/dev/null || true
	@echo ""
	@echo "🗑️  Removing model gateway..."
	-cd model-gateway && kubectl delete -f . 2>/dev/null || true
	@echo ""
	@echo "🗑️  Removing model hosting services..."
	-cd model-hosting && kubectl delete -f . 2>/dev/null || true
	@echo ""
	@echo "🗑️  Removing base infrastructure components..."
	@echo "   Removing Karpenter nodepools..."
	-kubectl delete -f base_eks_setup/karpenter_nodepool/ 2>/dev/null || true
	@echo "   Removing GP3 storage class..."
	-kubectl delete -f base_eks_setup/gp3.yaml 2>/dev/null || true
	@echo "   Removing Prometheus monitoring..."
	-kubectl delete -f base_eks_setup/prometheus-monitoring.yaml 2>/dev/null || true
	@echo ""
	@echo "🗑️  Removing NVIDIA GPU Operator..."
	@echo "   Uninstalling NVIDIA GPU Operator Helm releases..."
	-helm list -n gpu-operator --short | xargs -r -I {} helm uninstall {} -n gpu-operator 2>/dev/null || true
	@echo "   Removing NVIDIA Device Plugin..."
	-kubectl delete -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/v0.17.2/deployments/static/nvidia-device-plugin.yml 2>/dev/null || true
	@echo "   Removing GPU operator namespace..."
	-kubectl delete namespace gpu-operator 2>/dev/null || true
	@echo ""
	@echo "🗑️  Removing KubeRay Operator..."
	@echo "   Uninstalling KubeRay Operator Helm release..."
	-helm uninstall kuberay-operator -n kuberay 2>/dev/null || true
	@echo "   Removing KubeRay namespace..."
	-kubectl delete namespace kuberay 2>/dev/null || true
	@echo ""
	@echo "🗑️  Removing persistent volume claims..."
	-kubectl delete pvc --all --all-namespaces --timeout=60s 2>/dev/null || true
	@echo ""
	@echo "🗑️  Removing persistent volumes..."
	-kubectl delete pv --all --timeout=60s 2>/dev/null || true
	@echo ""
	@echo "🗑️  Removing storage classes (custom ones)..."
	-kubectl delete storageclass gp3 2>/dev/null || true
	-kubectl delete storageclass gp3-csi 2>/dev/null || true
	-kubectl delete storageclass ebs-sc 2>/dev/null || true
	@echo ""
	@echo "🗑️  Removing secrets and configmaps..."
	-kubectl delete secret --all --all-namespaces --field-selector type!=kubernetes.io/service-account-token 2>/dev/null || true
	-kubectl delete configmap --all --all-namespaces --field-selector metadata.name!=kube-root-ca.crt 2>/dev/null || true
	@echo ""
	@echo "🗑️  Removing service accounts in default namespace..."
	-kubectl delete serviceaccount --all -n default --field-selector metadata.name!=default 2>/dev/null || true
	@echo ""
	@echo "🗑️  Removing custom resource definitions..."
	-kubectl delete crd rayclusters.ray.io 2>/dev/null || true
	-kubectl delete crd rayservices.ray.io 2>/dev/null || true
	-kubectl delete crd rayjobs.ray.io 2>/dev/null || true
	-kubectl delete crd milvuses.milvus.io 2>/dev/null || true
	@echo ""
	@echo "🗑️  Removing operators and system components..."
	-kubectl delete -f https://raw.githubusercontent.com/zilliztech/milvus-operator/main/deploy/manifests/deployment.yaml 2>/dev/null || true
	-kubectl delete -f https://github.com/jetstack/cert-manager/releases/download/v1.5.3/cert-manager.yaml 2>/dev/null || true
	@echo ""
	@echo "🗑️  Removing namespaces (non-system)..."
	-kubectl delete namespace kuberay 2>/dev/null || true
	-kubectl delete namespace milvus-operator 2>/dev/null || true
	-kubectl delete namespace cert-manager 2>/dev/null || true
	-kubectl delete namespace gpu-operator 2>/dev/null || true
	@echo ""
	@echo "🗑️  Force cleanup any remaining resources..."
	@echo "Checking for stuck resources..."
	-kubectl get pods --all-namespaces --field-selector=status.phase!=Running,status.phase!=Succeeded 2>/dev/null || true
	@echo ""
	@echo "Force deleting any stuck pods..."
	-kubectl delete pods --all --all-namespaces --grace-period=0 --force 2>/dev/null || true
	@echo ""
	@echo "🗑️  Removing Helm repositories..."
	-helm repo remove kuberay 2>/dev/null || true
	-helm repo remove nvidia 2>/dev/null || true
	-helm repo remove langfuse 2>/dev/null || true
	@echo ""
	@echo "✅ Comprehensive cleanup complete!"
	@echo ""
	@echo "ℹ️  Note: Some AWS Load Balancers and EBS volumes may take additional time to be cleaned up by AWS."
	@echo "ℹ️  Check your AWS console to verify all resources have been properly removed."
	@echo "ℹ️  Karpenter-managed nodes will be automatically terminated when workloads are removed."

# Safe cleanup - removes applications but preserves persistent data
clean-safe:
	@echo "🧹 Safe cleanup - removing applications but preserving data..."
	@echo ""
	@echo "🗑️  Removing agentic applications..."
	-kubectl delete -f agent/kubernetes/combined.yaml 2>/dev/null || true
	@echo "🗑️  Removing Strands SDK RAG applications..."
	-kubectl delete -f agentic-apps/strandsdk_agentic_rag_opensearch/k8s/ 2>/dev/null || true
	-kubectl delete ingress strandsdk-rag-ingress-alb 2>/dev/null || true
	-kubectl delete secret app-secrets 2>/dev/null || true
	-kubectl delete configmap app-config 2>/dev/null || true
	-kubectl delete serviceaccount strandsdk-rag-service-account 2>/dev/null || true
	@echo ""
	@echo "🗑️  Removing Milvus services (keeping data)..."
	-kubectl delete -f milvus/milvus-nlb-service.yaml 2>/dev/null || true
	@echo ""
	@echo "🗑️  Removing observability components..."
	@echo "   Uninstalling Langfuse Helm release..."
	-helm uninstall langfuse 2>/dev/null || true
	-cd model-observability && kubectl delete -f . 2>/dev/null || true
	@echo ""
	@echo "🗑️  Removing model gateway..."
	-cd model-gateway && kubectl delete -f . 2>/dev/null || true
	@echo ""
	@echo "🗑️  Removing model hosting services..."
	-cd model-hosting && kubectl delete -f . 2>/dev/null || true
	@echo ""
	@echo "✅ Safe cleanup complete! Persistent data has been preserved."
	@echo "ℹ️  To remove persistent data, run 'make clean-pvcs' or 'make clean'"

# Clean only persistent volume claims and volumes
clean-pvcs:
	@echo "🗑️  Removing persistent volume claims and volumes..."
	@echo ""
	@echo "⚠️  WARNING: This will delete all persistent data!"
	@echo "Press Ctrl+C within 10 seconds to cancel..."
	@sleep 10
	@echo ""
	@echo "🗑️  Removing persistent volume claims..."
	-kubectl delete pvc --all --all-namespaces --timeout=60s 2>/dev/null || true
	@echo ""
	@echo "🗑️  Removing persistent volumes..."
	-kubectl delete pv --all --timeout=60s 2>/dev/null || true
	@echo ""
	@echo "🗑️  Removing custom storage classes..."
	-kubectl delete storageclass gp3-csi 2>/dev/null || true
	-kubectl delete storageclass ebs-sc 2>/dev/null || true
	@echo ""
	@echo "✅ Persistent volume cleanup complete!"

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
dev-setup: verify-cluster setup-base setup-models setup-observability setup-gateway
	@echo "✅ Development setup complete!"
	@echo "Core components (base, models, observability, gateway) are ready for development."
