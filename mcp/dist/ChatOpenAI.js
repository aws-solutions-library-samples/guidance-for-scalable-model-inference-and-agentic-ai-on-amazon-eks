import OpenAI from "openai";
import 'dotenv/config';
import { logTitle } from "./utils";
export default class ChatOpenAI {
    constructor(model, systemPrompt = '', tools = [], context = '') {
        this.messages = [];
        this.llm = new OpenAI({
            apiKey: process.env.OPENAI_API_KEY,
            baseURL: process.env.OPENAI_BASE_URL,
        });
        this.model = model;
        this.tools = tools;
        if (systemPrompt)
            this.messages.push({ role: "system", content: systemPrompt });
        if (context)
            this.messages.push({ role: "user", content: context });
    }
    async chat(prompt) {
        logTitle('CHAT');
        if (prompt) {
            this.messages.push({ role: "user", content: prompt });
        }
        const stream = await this.llm.chat.completions.create({
            model: this.model,
            messages: this.messages,
            stream: true,
            tools: this.getToolsDefinition(),
        });
        let content = "";
        let toolCalls = [];
        logTitle('RESPONSE');
        for await (const chunk of stream) {
            const delta = chunk.choices[0].delta;
            // 处理普通Content
            if (delta.content) {
                const contentChunk = chunk.choices[0].delta.content || "";
                content += contentChunk;
                process.stdout.write(contentChunk);
            }
            // 处理ToolCall
            if (delta.tool_calls) {
                for (const toolCallChunk of delta.tool_calls) {
                    // 第一次要创建一个toolCall
                    if (toolCalls.length <= toolCallChunk.index) {
                        toolCalls.push({ id: '', function: { name: '', arguments: '' } });
                    }
                    let currentCall = toolCalls[toolCallChunk.index];
                    if (toolCallChunk.id)
                        currentCall.id += toolCallChunk.id;
                    if (toolCallChunk.function?.name)
                        currentCall.function.name += toolCallChunk.function.name;
                    if (toolCallChunk.function?.arguments)
                        currentCall.function.arguments += toolCallChunk.function.arguments;
                }
            }
        }
        this.messages.push({ role: "assistant", content: content, tool_calls: toolCalls.map(call => ({ id: call.id, type: "function", function: call.function })) });
        return {
            content: content,
            toolCalls: toolCalls,
        };
    }
    appendToolResult(toolCallId, toolOutput) {
        this.messages.push({
            role: "tool",
            content: toolOutput,
            tool_call_id: toolCallId
        });
    }
    getToolsDefinition() {
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
