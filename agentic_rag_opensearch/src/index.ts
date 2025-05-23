import 'dotenv/config';
import MCPClient from "./MCPClient";
import Agent from "./Agent";
import path from "path";
import EmbeddingRetriever from "./EmbeddingRetriever";
import fs from "fs";
import { logTitle } from "./utils";

// Verify environment variables are loaded
if (!process.env.AWS_REGION || !process.env.OPENSEARCH_ENDPOINT) {
  throw new Error('Required environment variables AWS_REGION and OPENSEARCH_ENDPOINT are not set');
}

// Use the parent directory (where the command is run) instead of src directory
const outPath = path.resolve(process.cwd(), 'output');
const TASK = `
Find information about What is the most important aspect of initial treatment for Bell's palsy?. 
Summarize this information and create a story about her.
Save the story and her basic information to a file named "antonette.md" in the output directory as a beautiful markdown file.
`

// Make sure output directory exists
if (!fs.existsSync(outPath)) {
  fs.mkdirSync(outPath, { recursive: true });
}

// Start the application immediately
(async () => {
  try {
    logTitle('INITIALIZING AGENTIC RAG SYSTEM');
    
    // Initialize the filesystem MCP client
    const fileMCP = new MCPClient("mcp-server-file", "npx", ['-y', '@modelcontextprotocol/server-filesystem', outPath]);
    
    await main(fileMCP);
  } catch (error) {
    console.error("Error in main:", error);
  }
})();

async function main(fileMCP: MCPClient) {
  // Step 1: Retrieve relevant context using RAG
  const context = await retrieveContext("What is the most important aspect of initial treatment for Bell's palsy?");
  
  // Step 2: Initialize the agent with the context and MCP client
  logTitle('INITIALIZING AGENT');
  const systemPrompt = `You are a helpful assistant that can retrieve information and create stories.
You have access to tools that can help you complete tasks.
When asked to save files, always use the filesystem tool to write the content.
Specifically, use the write_file tool to save files.
The output path is ${outPath}.`;

  const agent = new Agent('Qwen/QwQ-32B-AWQ', [fileMCP], systemPrompt, context);
  await agent.init();
  
  // Step 3: Execute the task with the agent
  logTitle('EXECUTING TASK');
  console.log(TASK);
  const response = await agent.invoke(TASK);
  
  // Step 4: Close connections
  logTitle('TASK COMPLETED');
  console.log(response);
  await agent.close();
  
  // Close OpenSearch connection when done
  const embeddingRetriever = new EmbeddingRetriever("custom-embedding-model");
  // @ts-ignore - Access private property for cleanup
  if (embeddingRetriever.vectorStore && typeof embeddingRetriever.vectorStore.close === 'function') {
    // @ts-ignore
    await embeddingRetriever.vectorStore.close();
  }
}

async function retrieveContext(query: string) {
    logTitle('RETRIEVING CONTEXT');
    console.log(`Query: ${query}`);
    
    // Initialize the embedding retriever
    const embeddingRetriever = new EmbeddingRetriever("custom-embedding-model");
    
    // Retrieve relevant documents
    const documents = await embeddingRetriever.retrieve(query, 5);
    
    // Combine documents into context
    const context = documents.join('\n\n');
    
    console.log(`Retrieved ${documents.length} relevant documents`);
    console.log('Context preview:', context);
    
    return context;
}
