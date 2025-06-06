import MCPClient from "../MCPClient";
import ChatOpenAI from "../ChatOpenAI";
import { logTitle } from "../utils";
import { ToolCall } from "../ChatOpenAI";
import path from "path";

export default class MCPAgent {
    private mcpClients: MCPClient[];
    private llm: ChatOpenAI | null = null;
    private model: string;
    private outPath: string;

    constructor(mcpClients: MCPClient[], model: string = 'Qwen/QwQ-32B-AWQ') {
        this.mcpClients = mcpClients;
        this.model = model;
        this.outPath = path.resolve(process.cwd(), 'output');
    }

    async init() {
        logTitle('INITIALIZING MCP AGENT');
        
        // Initialize all MCP clients
        for (const client of this.mcpClients) {
            await client.init();
        }
        
        // Get all available tools
        const tools = this.mcpClients.flatMap(client => client.getTools());
        console.log(`Initialized ${this.mcpClients.length} MCP clients with ${tools.length} tools`);
        
        // Initialize LLM with tools but without system prompt and context yet
        this.llm = new ChatOpenAI(this.model, '', tools, '');
        
        console.log('MCP Agent initialized');
    }

    async close() {
        // Close all MCP clients
        for (const client of this.mcpClients) {
            await client.close();
        }
    }

    async executeTask(query: string, context: string): Promise<string> {
        logTitle('MCP AGENT TASK EXECUTION');
        console.log(`Executing task with context length: ${context.length} characters`);
        
        if (!this.llm) {
            throw new Error('MCP Agent not initialized');
        }

        // Create system prompt with context
        const systemPrompt = `You are a helpful assistant that can retrieve information and complete tasks.
You have access to tools that can help you complete tasks.
When asked to save files, always use the filesystem tool to write the content.
Specifically, use the write_file tool to save files.
The output path is ${this.outPath}.

Context from knowledge base:
${context}

Use this context to inform your responses and complete the requested task.`;

        // Update the LLM with the system prompt and context
        this.llm.updateSystemPrompt(systemPrompt);

        try {
            console.log("Starting conversation with LLM...");
            
            // Start the conversation with the user query
            let response = await this.llm.chat(query);
            
            // Continue the conversation until no more tool calls are needed
            while (response.toolCalls && response.toolCalls.length > 0) {
                logTitle('PROCESSING TOOL CALLS');
                console.log(`Processing ${response.toolCalls.length} tool calls`);
                
                // Process each tool call
                for (const toolCall of response.toolCalls) {
                    await this.processToolCall(toolCall);
                }
                
                // Continue the conversation with the tool results
                response = await this.llm.chat();
            }
            
            logTitle('TASK COMPLETED');
            console.log("Successfully completed task");
            return response.content;
        } catch (error) {
            console.error("Error in MCP agent execution:", error);
            throw error;
        }
    }

    async callTool(toolName: string, args: any): Promise<any> {
        logTitle('DIRECT TOOL CALL');
        console.log(`Calling tool: ${toolName}`);
        console.log(`Arguments:`, args);
        
        // Find the appropriate MCP client for this tool
        for (const client of this.mcpClients) {
            const tools = client.getTools();
            const tool = tools.find(t => t.name === toolName);
            
            if (tool) {
                try {
                    const result = await client.callTool(toolName, args);
                    console.log(`Tool result:`, result);
                    return result;
                } catch (error) {
                    console.error(`Error calling tool ${toolName}:`, error);
                    throw error;
                }
            }
        }
        
        throw new Error(`Tool ${toolName} not found in any MCP client`);
    }

    async listAvailableTools(): Promise<any[]> {
        const allTools = this.mcpClients.flatMap(client => client.getTools());
        return allTools;
    }

    private async processToolCall(toolCall: ToolCall) {
        try {
            const { id, function: { name, arguments: argsString } } = toolCall;
            console.log(`Executing tool call: ${name}`);
            
            // Parse the arguments
            const args = JSON.parse(argsString);
            
            // Find the MCP client that can handle this tool
            let result = null;
            let toolFound = false;
            
            for (const client of this.mcpClients) {
                const tools = client.getTools();
                const tool = tools.find(t => t.name === name);
                
                if (tool) {
                    toolFound = true;
                    result = await client.callTool(name, args);
                    break;
                }
            }
            
            if (!toolFound) {
                throw new Error(`No MCP client found for tool: ${name}`);
            }
            
            console.log(`Tool result: ${JSON.stringify(result).substring(0, 100)}...`);
            
            // Append the tool result to the conversation
            this.llm?.appendToolResult(id, JSON.stringify(result));
        } catch (error) {
            console.error(`Error processing tool call: ${error}`);
            // Append the error as the tool result
            this.llm?.appendToolResult(toolCall.id, JSON.stringify({ error: error.message }));
        }
    }

    getStats(): {
        model: string;
        clientCount: number;
        toolCount: number;
        initialized: boolean;
    } {
        const toolCount = this.mcpClients.flatMap(client => client.getTools()).length;
        
        return {
            model: this.model,
            clientCount: this.mcpClients.length,
            toolCount,
            initialized: this.llm !== null
        };
    }
}
