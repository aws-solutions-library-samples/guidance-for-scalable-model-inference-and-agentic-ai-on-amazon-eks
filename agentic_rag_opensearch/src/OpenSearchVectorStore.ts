import { Client } from '@opensearch-project/opensearch';
import { VectorStore, VectorStoreItem } from './VectorStore';
import 'dotenv/config';
import AWS from 'aws-sdk';
import { RequestsHttpConnection } from '@opensearch-project/opensearch/lib/aws/connection';

export default class OpenSearchVectorStore implements VectorStore {
    private client: Client;
    private indexName: string = 'rag_documents';
    private dimension: number = 1536; // Default dimension for embeddings

    constructor() {
        // Connect to OpenSearch cluster
        const region = process.env.AWS_REGION || 'us-east-1';
        const opensearchEndpoint = 'https://vpc-test-2pqci5m227ovpoaqcubvm6e5ia.us-east-1.es.amazonaws.com';
        
        // Create AWS credentials
        const credentials = new AWS.EnvironmentCredentials('AWS');
        
        // Initialize the OpenSearch client with AWS Signature V4 authentication
        this.client = new Client({
            node: opensearchEndpoint,
            auth: {
                type: 'aws',
                credentials: credentials,
                region: region
            },
            connection: RequestsHttpConnection,
            ssl: {
                rejectUnauthorized: true
            }
        });
        
        this.initIndex();
    }

    private async initIndex() {
        try {
            // Check if index exists
            const indexExists = await this.client.indices.exists({ index: this.indexName });
            
            if (!indexExists.body) {
                console.log(`Creating index ${this.indexName}`);
                
                // Create index with mapping for vector field
                await this.client.indices.create({
                    index: this.indexName,
                    body: {
                        settings: {
                            "index.knn": true,
                            "index.knn.space_type": "cosinesimil"
                        },
                        mappings: {
                            properties: {
                                embedding: {
                                    type: 'knn_vector',
                                    dimension: this.dimension,
                                    method: {
                                        name: 'hnsw',
                                        space_type: 'cosinesimil',
                                        engine: 'nmslib',
                                        parameters: {
                                            ef_construction: 128,
                                            m: 16
                                        }
                                    }
                                },
                                document: {
                                    type: 'text',
                                    store: true
                                }
                            }
                        }
                    }
                });
                
                console.log(`Index ${this.indexName} created successfully`);
            } else {
                console.log(`Index ${this.indexName} already exists`);
            }
        } catch (error) {
            console.error('Error initializing OpenSearch index:', error);
            console.error(JSON.stringify(error, null, 2));
        }
    }

    async addEmbedding(embedding: number[], document: string): Promise<void> {
        try {
            await this.client.index({
                index: this.indexName,
                body: {
                    embedding: embedding,
                    document: document
                },
                refresh: true // Make the document immediately searchable
            });
            console.log('Document added to OpenSearch');
        } catch (error) {
            console.error('Error adding embedding to OpenSearch:', error);
            console.error(JSON.stringify(error, null, 2));
        }
    }

    async search(queryEmbedding: number[], topK: number = 3): Promise<string[]> {
        try {
            const searchResponse = await this.client.search({
                index: this.indexName,
                body: {
                    size: topK,
                    query: {
                        knn: {
                            embedding: {
                                vector: queryEmbedding,
                                k: topK
                            }
                        }
                    },
                    _source: ['document']
                }
            });
            
            // Extract documents from search results
            const hits = searchResponse.body.hits.hits;
            return hits.map((hit: any) => hit._source.document);
        } catch (error) {
            console.error('Error searching in OpenSearch:', error);
            console.error(JSON.stringify(error, null, 2));
            return [];
        }
    }

    async close(): Promise<void> {
        try {
            await this.client.close();
            console.log('OpenSearch connection closed');
        } catch (error) {
            console.error('Error closing OpenSearch connection:', error);
        }
    }
}
