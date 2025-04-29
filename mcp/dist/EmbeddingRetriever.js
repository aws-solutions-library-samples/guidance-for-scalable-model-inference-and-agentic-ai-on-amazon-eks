import { logTitle } from "./utils";
import VectorStore from "./VectorStore";
import 'dotenv/config';
import { BedrockRuntimeClient, InvokeModelCommand } from "@aws-sdk/client-bedrock-runtime";
export default class EmbeddingRetriever {
    constructor(embeddingModel) {
        this.embeddingModel = embeddingModel;
        this.vectorStore = new VectorStore();
        this.bedrockClient = new BedrockRuntimeClient({
            region: process.env.AWS_REGION || 'us-west-2'
        });
    }
    async embedDocument(document) {
        logTitle('EMBEDDING DOCUMENT');
        const embedding = await this.embed(document);
        this.vectorStore.addEmbedding(embedding, document);
        return embedding;
    }
    async embedQuery(query) {
        logTitle('EMBEDDING QUERY');
        const embedding = await this.embed(query);
        return embedding;
    }
    async embed(document) {
        // For AWS Bedrock
        const modelId = 'amazon.titan-embed-text-v1';
        try {
            const command = new InvokeModelCommand({
                modelId: modelId,
                contentType: 'application/json',
                accept: 'application/json',
                body: JSON.stringify({
                    inputText: document,
                }),
            });
            const response = await this.bedrockClient.send(command);
            // Parse the response body
            const responseBody = JSON.parse(new TextDecoder().decode(response.body));
            console.log(responseBody);
            // If the embedding is undefined, return a mock embedding for testing
            if (!responseBody.embedding) {
                console.log("Warning: Using mock embedding as the API didn't return a valid embedding");
                // Return a small random embedding vector for testing purposes
                return Array(10).fill(0).map(() => Math.random());
            }
            return responseBody.embedding;
        }
        catch (error) {
            console.error("Error fetching embedding:", error);
            // Return a mock embedding in case of error
            return Array(10).fill(0).map(() => Math.random());
        }
    }
    async retrieve(query, topK = 3) {
        const queryEmbedding = await this.embedQuery(query);
        return this.vectorStore.search(queryEmbedding, topK);
    }
}
