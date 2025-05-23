import { MilvusClient, DataType, InsertReq, SearchParam } from '@zilliz/milvus2-sdk-node';
import { VectorStoreItem } from './VectorStore';
import 'dotenv/config';

export default class MilvusVectorStore {
    private client: MilvusClient;
    private collectionName: string = 'rag_documents';
    private dimension: number = 1536; // Default dimension for Titan embeddings

    constructor() {
        // Connect to Milvus service through NLB
        this.client = new MilvusClient({
            address: process.env.MILVUS_ADDRESS || 'k8s-default-milvusnl-fd87300847-5fa4d28f059626c9.elb.us-east-1.amazonaws.com:19530',
            username: process.env.MILVUS_USERNAME || '',
            password: process.env.MILVUS_PASSWORD || '',
        });
        this.initCollection();
    }

    private async initCollection() {
        try {
            // Check if collection exists
            const hasCollection = await this.client.hasCollection({
                collection_name: this.collectionName,
            });

            if (!hasCollection.value) {
                // Create collection if it doesn't exist
                await this.client.createCollection({
                    collection_name: this.collectionName,
                    fields: [
                        {
                            name: 'id',
                            data_type: DataType.Int64,
                            is_primary_key: true,
                            autoID: true,
                        },
                        {
                            name: 'embedding',
                            data_type: DataType.FloatVector,
                            dim: this.dimension,
                        },
                        {
                            name: 'document',
                            data_type: DataType.VarChar,
                            max_length: 65535,
                        },
                    ],
                });

                // Create index for vector search
                await this.client.createIndex({
                    collection_name: this.collectionName,
                    field_name: 'embedding',
                    index_type: 'HNSW',
                    metric_type: 'COSINE',
                    params: { M: 8, efConstruction: 64 },
                });

                // Load collection into memory
                await this.client.loadCollection({
                    collection_name: this.collectionName,
                });
            }
        } catch (error) {
            console.error('Error initializing Milvus collection:', error);
        }
    }

    async addEmbedding(embedding: number[], document: string) {
        try {
            const insertData: InsertReq = {
                collection_name: this.collectionName,
                fields_data: [{
                    embedding: embedding,
                    document: document,
                }],
            };
            
            await this.client.insert(insertData);
        } catch (error) {
            console.error('Error adding embedding to Milvus:', error);
        }
    }

    async search(queryEmbedding: number[], topK: number = 3): Promise<string[]> {
        try {
            const searchParams: SearchParam = {
                collection_name: this.collectionName,
                vector: queryEmbedding,
                output_fields: ['document'],
                limit: topK,
                params: { ef: 64 },
            };
            
            const searchResult = await this.client.search(searchParams);
            
            if (searchResult && searchResult.results) {
                return searchResult.results.map(item => item.document as string);
            }
            
            return [];
        } catch (error) {
            console.error('Error searching in Milvus:', error);
            return [];
        }
    }

    async close() {
        try {
            await this.client.closeConnection();
        } catch (error) {
            console.error('Error closing Milvus connection:', error);
        }
    }
}
