import MCPClient from "./MCPClient";
import Agent from "./Agent";
import path from "path";
import EmbeddingRetriever from "./EmbeddingRetriever";
import fs from "fs";
import { logTitle } from "./utils";
const URL = 'https://news.ycombinator.com/';
const outPath = path.join(process.cwd(), 'output');
const TASK = `
告诉我Antonette的信息,先从我给你的context中找到相关信息,总结后创作一个关于她的故事
把故事和她的基本信息保存到${outPath}/antonette.md,输出一个漂亮md文件
`;
// Removing the fetch MCP since it's not available
// const fetchMCP = new MCPClient("mcp-server-fetch", "npx", ['-y', '@modelcontextprotocol/server-fetch']);
const fileMCP = new MCPClient("mcp-server-file", "npx", ['-y', '@modelcontextprotocol/server-filesystem', outPath]);
async function main() {
    // RAG
    const context = await retrieveContext();
    // Agent
    // Using only fileMCP since fetchMCP is not available
    const agent = new Agent('QwQ-32B/QwQ-32B-AWQ', [fileMCP], '', context);
    await agent.init();
    await agent.invoke(TASK);
    await agent.close();
}
main();
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
    return context;
}
