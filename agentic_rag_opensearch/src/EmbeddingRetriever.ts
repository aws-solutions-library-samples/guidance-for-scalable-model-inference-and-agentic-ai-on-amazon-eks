import { logTitle } from "./utils";
import OpenSearchVectorStore from "./OpenSearchVectorStore";
import 'dotenv/config';
import fetch from 'node-fetch';

export default class EmbeddingRetriever {
    private embeddingModel: string;
    private vectorStore: OpenSearchVectorStore;
    private embeddingEndpoint: string;

    constructor(embeddingModel: string) {
        this.embeddingModel = embeddingModel;
        this.vectorStore = new OpenSearchVectorStore();
        this.embeddingEndpoint = 'http://18.232.167.163:8080/v1/embeddings';
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
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            
            const responseBody = await response.json();
            
            // Check if we got a valid embedding
            if (!responseBody.embedding) {
                console.log("Warning: Embedding API didn't return a valid embedding");
                console.log("Response:", JSON.stringify(responseBody, null, 2));
                // Return a small random embedding vector for testing purposes
                return Array(1536).fill(0).map(() => Math.random());
            }
            
            console.log(`Successfully received embedding with ${responseBody.embedding.length} dimensions`);
            return responseBody.embedding;
        } catch (error) {
            console.error("Error fetching embedding from custom endpoint:", error);
            // Return a mock embedding in case of error
            return Array(1536).fill(0).map(() => Math.random());
        }
    }

    async retrieve(query: string, topK: number = 3): Promise<string[]> {
        const queryEmbedding = await this.embedQuery(query);
        return this.vectorStore.search(queryEmbedding, topK);
    }
}
