import MCPClient from "./MCPClient";
import Agent from "./Agent";
import path from "path";
import EmbeddingRetriever from "./EmbeddingRetriever";
import fs from "fs";
import { logTitle } from "./utils";

const outPath = path.join(process.cwd(), 'output');
const TASK = `
Tell me the information about Stanton, first find the relevant information from the context I gave you, and then summarize it and create a story about her.
Save the story and her basic information to ${outPath}/Stanton.md, and output a beautiful md file
`

// Make sure output directory exists
if (!fs.existsSync(outPath)) {
  fs.mkdirSync(outPath, { recursive: true });
}

// Start the application immediately
(async () => {
  try {
    // Initialize only the file MCP client
    const fileMCP = new MCPClient("mcp-server-file", "npx", ['-y', '@modelcontextprotocol/server-filesystem', outPath]);
    
    await main(fileMCP);
  } catch (error) {
    console.error("Error in main:", error);
  }
})();

async function main(fileMCP: MCPClient) {
  // RAG
  const context = await retrieveContext();

  // Agent
  const agent = new Agent('Qwen/QwQ-32B-AWQ', [fileMCP], '', context);
  await agent.init();
  const response = await agent.invoke(TASK);
  await agent.close();
  
  // Since we can't use tools, manually write the file
  console.log("Writing response to file manually...");
  try {
    fs.writeFileSync(path.join(outPath, 'antonette.md'), response);
    console.log("Successfully wrote to antonette.md");
  } catch (error) {
    console.error("Error writing file:", error);
  }
  
  // Close Milvus connection when done
  const embeddingRetriever = new EmbeddingRetriever("amazon.titan-embed-text-v1");
  // @ts-ignore - Access private property for cleanup
  if (embeddingRetriever.vectorStore && typeof embeddingRetriever.vectorStore.close === 'function') {
    // @ts-ignore
    await embeddingRetriever.vectorStore.close();
  }
}

async function retrieveContext() {
    // RAG
    const embeddingRetriever = new EmbeddingRetriever("amazon.titan-embed-text-v1");
    const knowledgeDir = path.join(process.cwd(), 'knowledge');
    const files = fs.readdirSync(knowledgeDir);
    for await (const file of files) {
        const content = fs.readFileSync(path.join(knowledgeDir, file), 'utf-8');
        await embeddingRetriever.embedDocument(content);
    }
    const context = (await embeddingRetriever.retrieve(TASK, 3)).join('\n');
    logTitle('CONTEXT');
    console.log(context);
    return context
}
