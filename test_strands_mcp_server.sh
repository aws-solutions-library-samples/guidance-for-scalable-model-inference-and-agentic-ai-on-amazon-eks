echo "START SCALE INFERENCE AND AGENTIC APPS TEST on $(date)"
echo "---------------------"

# Get the Application Load Balancer endpoint
ALB_ENDPOINT=$(kubectl get ingress strandsdk-rag-ingress-alb -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

echo "ALB ENDPOINT: ${ALB_ENDPOINT}"

# Test the health endpoint
echo "Test the MCP health endpoint: ${ALB_ENDPOINT}/health"
echo ""
curl -X GET "http://${ALB_ENDPOINT}/health"
echo "\----------"

# Test a simple query
echo "Test a simple query http://${ALB_ENDPOINT}/query"
echo ""
curl -X POST "http://${ALB_ENDPOINT}/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is Bell'\''s palsy?",
    "include_web_search": true
  }'
echo "\---------"

# Test knowledge embedding
echo "Test knowledge embedding ENDPOINT: ${ALB_ENDPOINT}/embed-knowledge.."
echo ""
curl -X POST "http://${ALB_ENDPOINT}/embed-knowledge" \
  -H "Content-Type: application/json"
echo "------"


# Test with a more complex medical query
echo "Test with a more complex medical query about study on encainide and flecainide in patients with supraventricular arrhythmias..."
echo ""
#"question": "Find information about \"What was the purpose of the study on encainide and flecainide in patients with supraventricular arrhythmias\". Summarize this information and create a comprehensi$

curl -X POST "http://${ALB_ENDPOINT}/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Find information about \"What was the purpose of the study on sodium chloride in patients with heart failure\". Summarize this information and create a comprehensive story",
    "top_k": 3
  }' \
  --max-time 600
echo "\---------"
echo "END SCALABLE INFERENCE AND AGENTIC APPS on: $(date)"

#Health check: curl -X GET "http://k8s-default-strandsd-68c6191426-1903627097.us-east-1.elb.amazonaws.com/health"
#Embed knowledge: curl -X POST "http://k8s-default-strandsd-68c6191426-1903627097.us-east-1.elb.amazonaws.com/embed" -H "Content-Type: application/json" -d '{"force_refresh": false}'
#Complex query: curl -i -X POST "http://k8s-default-strandsd-68c6191426-1903627097.us-east-1.elb.amazonaws.com/query" -H "Content-Type: application/json" -d '{"question": "Find information about \"What was the purpose of the study on encainide and flecainide in patients with supraventricular arrhythmias\". Summarize this information and create a comprehensive story.Save the story and important information to a file named \"test1.md\" in the output directory as a beautiful markdown file.", "top_k": 3}' --max-time 600
