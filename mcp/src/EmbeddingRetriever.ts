import { logTitle } from "./utils";
import MilvusVectorStore from "./MilvusVectorStore";
import 'dotenv/config';
import { BedrockRuntimeClient, InvokeModelCommand } from "@aws-sdk/client-bedrock-runtime";

export default class EmbeddingRetriever {
    private embeddingModel: string;
    private vectorStore: MilvusVectorStore;
    private bedrockClient: BedrockRuntimeClient;

    constructor(embeddingModel: string) {
        this.embeddingModel = embeddingModel;
        this.vectorStore = new MilvusVectorStore();
        this.bedrockClient = new BedrockRuntimeClient({ 
            region: process.env.AWS_REGION || 'us-west-2'
        });
    }

    async embedDocument(document: string) {
        logTitle('EMBEDDING DOCUMENT');
        const embedding = await this.embed(document);
        this.vectorStore.addEmbedding(embedding, document);
        return embedding;
    }

    async embedQuery(query: string) {
        logTitle('EMBEDDING QUERY');
        const embedding = await this.embed(query);
        return embedding;
    }

    private async embed(document: string): Promise<number[]> {
        // For AWS Bedrock
        const modelId = 'amazon.titan-embed-text-v1';
        
        try {
            console.log(`Sending embedding request to AWS Bedrock for model: ${modelId}`);
            console.log(`Document length: ${document.length} characters`);
            
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
            
            // Check if we got a valid embedding
            if (!responseBody.embedding) {
                console.log("Warning: Bedrock API didn't return a valid embedding");
                console.log("Response:", JSON.stringify(responseBody, null, 2));
                // Return a small random embedding vector for testing purposes
                return Array(1536).fill(0).map(() => Math.random());
            }
            
            console.log(`Successfully received embedding with ${responseBody.embedding.length} dimensions`);
            return responseBody.embedding;
        } catch (error) {
            console.error("Error fetching embedding from AWS Bedrock:", error);
            // Return a mock embedding in case of error
            return Array(1536).fill(0).map(() => Math.random());
        }
    }

    async retrieve(query: string, topK: number = 3): Promise<string[]> {
        const queryEmbedding = await this.embedQuery(query);
        return this.vectorStore.search(queryEmbedding, topK);
    }
}
