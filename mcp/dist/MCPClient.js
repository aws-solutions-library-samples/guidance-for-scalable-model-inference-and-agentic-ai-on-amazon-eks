import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
export default class MCPClient {
    constructor(name, command, args, version) {
        this.transport = null;
        this.tools = [];
        this.mcp = new Client({ name, version: version || "0.0.1" });
        this.command = command;
        this.args = args;
    }
    async init() {
        await this.connectToServer();
    }
    async close() {
        await this.mcp.close();
    }
    getTools() {
        return this.tools;
    }
    callTool(name, params) {
        return this.mcp.callTool({
            name,
            arguments: params,
        });
    }
    async connectToServer() {
        try {
            this.transport = new StdioClientTransport({
                command: this.command,
                args: this.args,
            });
            await this.mcp.connect(this.transport);
            const toolsResult = await this.mcp.listTools();
            this.tools = toolsResult.tools.map((tool) => {
                return {
                    name: tool.name,
                    description: tool.description,
                    inputSchema: tool.inputSchema,
                };
            });
            console.log("Connected to server with tools:", this.tools.map(({ name }) => name));
        }
        catch (e) {
            console.log("Failed to connect to MCP server: ", e);
            throw e;
        }
    }
}
