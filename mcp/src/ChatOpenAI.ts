import OpenAI from "openai";
import { Tool } from "@modelcontextprotocol/sdk/types.js";
import 'dotenv/config'
import { logTitle } from "./utils";

export interface ToolCall {
    id: string;
    function: {
        name: string;
        arguments: string;
    };
}

export default class ChatOpenAI {
    private llm: OpenAI;
    private model: string;
    private messages: OpenAI.Chat.ChatCompletionMessageParam[] = [];
    private tools: Tool[];

    constructor(model: string, systemPrompt: string = '', tools: Tool[] = [], context: string = '') {
        this.llm = new OpenAI({
            apiKey: process.env.OPENAI_API_KEY,
            baseURL: process.env.OPENAI_BASE_URL,
            defaultHeaders: {
                "api-key": process.env.OPENAI_API_KEY,
                "Authorization": `Bearer ${process.env.OPENAI_API_KEY}`
            }
        });
        this.model = model;
        this.tools = tools;
        if (systemPrompt) this.messages.push({ role: "system", content: systemPrompt });
        if (context) this.messages.push({ role: "user", content: context });
    }

    async chat(prompt?: string): Promise<{ content: string, toolCalls: ToolCall[] }> {
        logTitle('CHAT');
        if (prompt) {
            this.messages.push({ role: "user", content: prompt });
        }
        
        // Debug the request
        console.log('Sending request to model:', this.model);
        console.log('Messages count:', this.messages.length);
        
        try {
            // Create request options - NO TOOLS, NO STREAMING
            const requestOptions = {
                model: this.model,
                messages: this.messages,
                stream: false,
            };
            
            console.log('Sending request with options:', JSON.stringify(requestOptions, null, 2));
            
            const completion = await this.llm.chat.completions.create(requestOptions);
            
            // Extract the response content
            const content = completion.choices[0]?.message?.content || "";
            console.log('Response content:', content);
            
            // Add the response to messages
            this.messages.push({ role: "assistant", content: content });
            
            return {
                content: content,
                toolCalls: [], // No tool calls since we're not using tools
            };
        } catch (error) {
            console.error('Error details:', error);
            if (error.response) {
                console.error('Response status:', error.response.status);
                console.error('Response headers:', error.response.headers);
                try {
                    console.error('Response data:', await error.response.text());
                } catch (e) {
                    console.error('Could not read response data');
                }
            }
            throw error;
        }
    }

    public appendToolResult(toolCallId: string, toolOutput: string) {
        this.messages.push({
            role: "tool",
            content: toolOutput,
            tool_call_id: toolCallId
        });
    }

    private getToolsDefinition(): OpenAI.Chat.Completions.ChatCompletionTool[] {
        return this.tools.map((tool) => ({
            type: "function",
            function: {
                name: tool.name,
                description: tool.description,
                parameters: tool.inputSchema,
            },
        }));
    }
}
