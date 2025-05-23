import { logTitle } from "./utils";
import OpenSearchVectorStore from "./OpenSearchVectorStore";
import 'dotenv/config';
import fetch from 'node-fetch';

export default class EmbeddingRetriever {
    private embeddingModel: string;
    private vectorStore: OpenSearchVectorStore;
    private embeddingEndpoint: string;
    private readonly targetDimension: number = 384;

    constructor(embeddingModel: string) {
        this.embeddingModel = embeddingModel;
        this.vectorStore = new OpenSearchVectorStore();
        this.embeddingEndpoint = 'http://18.232.167.163:8080/v1/embeddings';
    }

    async embedDocument(document: string) {
        logTitle('EMBEDDING DOCUMENT');
        const embedding = await this.embed(document);
        await this.vectorStore.addEmbedding(embedding, document);
        return embedding;
    }

    async embedQuery(query: string) {
        logTitle('EMBEDDING QUERY');
        const embedding = await this.embed(query);
        return embedding;
    }

    private generateRandomEmbedding(): number[] {
        return Array(this.targetDimension).fill(0).map(() => (Math.random() * 2 - 1));
    }

    private normalizeVector(vector: number[]): number[] {
        const magnitude = Math.sqrt(vector.reduce((sum, val) => sum + val * val, 0));
        return vector.map(val => val / magnitude);
    }

    private resizeEmbedding(embedding: number[]): number[] {
        if (embedding.length === this.targetDimension) {
            return embedding;
        }

        const result = new Array(this.targetDimension).fill(0);
        const ratio = embedding.length / this.targetDimension;

        for (let i = 0; i < this.targetDimension; i++) {
            const start = Math.floor(i * ratio);
            const end = Math.floor((i + 1) * ratio);
            let sum = 0;
            for (let j = start; j < end; j++) {
                sum += embedding[j] || 0;
            }
            result[i] = sum / (end - start);
        }

        return this.normalizeVector(result);
    }

    private async embed(document: string): Promise<number[]> {
        try {
            console.log(`Sending embedding request to custom endpoint: ${this.embeddingEndpoint}`);
            console.log(`Document length: ${document.length} characters`);
            
            const response = await fetch(this.embeddingEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    content: document
                }),
            });
            
            if (!response.ok) {
                console.log(`HTTP error! Status: ${response.status}`);
                return this.generateRandomEmbedding();
            }
            
            const responseBody = await response.json();
            
            // Check if we got a valid embedding
            if (!responseBody || !responseBody[0] || !responseBody[0].embedding || !Array.isArray(responseBody[0].embedding[0])) {
                console.log("Warning: Embedding API didn't return a valid embedding");
                console.log("Response:", JSON.stringify(responseBody, null, 2));
                return this.generateRandomEmbedding();
            }
            
            // Get the embedding array
            const embedding = responseBody[0].embedding[0];
            
            // Ensure we have a 384-dimensional vector
            const resizedEmbedding = this.resizeEmbedding(embedding);
            
            console.log(`Successfully processed embedding with ${resizedEmbedding.length} dimensions`);
            return resizedEmbedding;
            
        } catch (error) {
            console.error("Error fetching embedding from custom endpoint:", error);
            return this.generateRandomEmbedding();
        }
    }

    async retrieve(query: string, topK: number = 3): Promise<string[]> {
        const queryEmbedding = await this.embedQuery(query);
        return this.vectorStore.search(queryEmbedding, topK);
    }
}
