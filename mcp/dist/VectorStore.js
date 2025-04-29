export default class VectorStore {
    constructor() {
        this.vectorStore = [];
    }
    async addEmbedding(embedding, document) {
        this.vectorStore.push({ embedding, document });
    }
    async search(queryEmbedding, topK = 3) {
        const scored = this.vectorStore.map((item) => ({
            document: item.document,
            score: this.cosineSimilarity(queryEmbedding, item.embedding),
        }));
        const topKDocuments = scored.sort((a, b) => b.score - a.score).slice(0, topK).map((item) => item.document);
        return topKDocuments;
    }
    cosineSimilarity(vecA, vecB) {
        const dotProduct = vecA.reduce((sum, a, idx) => sum + a * vecB[idx], 0);
        const normA = Math.sqrt(vecA.reduce((sum, a) => sum + a * a, 0));
        const normB = Math.sqrt(vecB.reduce((sum, b) => sum + b * b, 0));
        return dotProduct / (normA * normB);
    }
}
