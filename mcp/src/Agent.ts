import MCPClient from "./MCPClient";
import ChatOpenAI from "./ChatOpenAI";
import { logTitle } from "./utils";

export default class Agent {
    private mcpClients: MCPClient[];
    private llm: ChatOpenAI | null = null;
    private model: string;
    private systemPrompt: string;
    private context: string;

    constructor(model: string, mcpClients: MCPClient[], systemPrompt: string = '', context: string = '') {
        this.mcpClients = mcpClients;
        this.model = model;
        this.systemPrompt = systemPrompt;
        this.context = context;
    }

    async init() {
        logTitle('TOOLS');
        for await (const client of this.mcpClients) {
            await client.init();
        }
        const tools = this.mcpClients.flatMap(client => client.getTools());
        this.llm = new ChatOpenAI(this.model, this.systemPrompt, tools, this.context);
    }

    async close() {
        for await (const client of this.mcpClients) {
            await client.close();
        }
    }

    async invoke(prompt: string) {
        if (!this.llm) throw new Error('Agent not initialized');
        
        // First try without tools
        try {
            console.log("Attempting to invoke LLM without tools...");
            const noToolsLLM = new ChatOpenAI(this.model, this.systemPrompt, [], this.context);
            const response = await noToolsLLM.chat(prompt);
            console.log("Successfully completed request without tools");
            await this.close();
            return response.content;
        } catch (error) {
            console.error("Error invoking LLM without tools:", error);
            throw error;
        }
    }
}