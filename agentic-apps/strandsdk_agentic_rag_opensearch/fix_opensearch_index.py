#!/usr/bin/env python3
"""
Script to fix OpenSearch index for vector embeddings.
This script will:
1. Delete the existing index if it exists
2. Create a new index with proper knn_vector mapping
"""

import os
import sys
import logging
from dotenv import load_dotenv
from opensearchpy import OpenSearch, RequestsHttpConnection
from aws_requests_auth.aws_auth import AWSRequestsAuth
import boto3

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get configuration from environment
OPENSEARCH_ENDPOINT = os.getenv('OPENSEARCH_ENDPOINT')
AWS_REGION = os.getenv('AWS_REGION')
VECTOR_INDEX_NAME = os.getenv('VECTOR_INDEX_NAME', 'knowledge-embeddings')
EMBEDDING_DIMENSION = 384  # Default dimension for embeddings

def initialize_client():
    """Initialize OpenSearch client with AWS authentication."""
    try:
        # Get AWS credentials
        session = boto3.Session()
        credentials = session.get_credentials()
        
        if not credentials:
            raise ValueError("AWS credentials not found")
        
        # Parse endpoint to get host
        endpoint_url = OPENSEARCH_ENDPOINT
        if endpoint_url.startswith('https://'):
            host = endpoint_url.replace('https://', '')
        else:
            host = endpoint_url
        
        logger.info(f"Connecting to OpenSearch at {host}")
        
        # Create AWS auth
        awsauth = AWSRequestsAuth(
            aws_access_key=credentials.access_key,
            aws_secret_access_key=credentials.secret_key,
            aws_token=credentials.token,
            aws_host=host,
            aws_region=AWS_REGION,
            aws_service='es'
        )
        
        # Initialize OpenSearch client
        client = OpenSearch(
            hosts=[{'host': host, 'port': 443}],
            http_auth=awsauth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection
        )
        
        logger.info("OpenSearch client initialized successfully")
        return client
        
    except Exception as e:
        logger.error(f"Failed to initialize OpenSearch client: {e}")
        raise

def delete_index(client):
    """Delete the vector index if it exists."""
    try:
        if client.indices.exists(index=VECTOR_INDEX_NAME):
            logger.info(f"Deleting existing index: {VECTOR_INDEX_NAME}")
            response = client.indices.delete(index=VECTOR_INDEX_NAME)
            logger.info(f"Index deleted: {response}")
            return True
        else:
            logger.info(f"Index {VECTOR_INDEX_NAME} does not exist")
            return True
            
    except Exception as e:
        logger.error(f"Failed to delete index: {e}")
        return False

def create_index(client, dimension=EMBEDDING_DIMENSION):
    """Create the vector index with proper mapping."""
    try:
        # Create index with vector mapping
        index_body = {
            "settings": {
                "index": {
                    "knn": True,
                    "knn.space_type": "cosinesimil"
                }
            },
            "mappings": {
                "properties": {
                    "embedding": {
                        "type": "knn_vector",
                        "dimension": dimension,
                        "method": {
                            "name": "hnsw",
                            "space_type": "cosinesimil",
                            "engine": "nmslib",
                            "parameters": {
                                "ef_construction": 128,
                                "m": 16
                            }
                        }
                    },
                    "document": {
                        "type": "text",
                        "store": True
                    },
                    "metadata": {
                        "type": "object"
                    },
                    "timestamp": {
                        "type": "date"
                    }
                }
            }
        }
        
        logger.info(f"Creating index {VECTOR_INDEX_NAME} with dimension {dimension}")
        response = client.indices.create(
            index=VECTOR_INDEX_NAME,
            body=index_body
        )
        
        logger.info(f"Index created: {response}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create index: {e}")
        return False

def check_index_mapping(client):
    """Check the mapping of the index."""
    try:
        if client.indices.exists(index=VECTOR_INDEX_NAME):
            mapping = client.indices.get_mapping(index=VECTOR_INDEX_NAME)
            logger.info(f"Index mapping: {mapping}")
            return mapping
        else:
            logger.info(f"Index {VECTOR_INDEX_NAME} does not exist")
            return None
    except Exception as e:
        logger.error(f"Failed to get index mapping: {e}")
        return None

def main():
    """Main function to fix OpenSearch index."""
    try:
        # Check environment variables
        if not OPENSEARCH_ENDPOINT:
            logger.error("OPENSEARCH_ENDPOINT environment variable not set")
            sys.exit(1)
        
        if not AWS_REGION:
            logger.error("AWS_REGION environment variable not set")
            sys.exit(1)
        
        logger.info(f"OpenSearch Endpoint: {OPENSEARCH_ENDPOINT}")
        logger.info(f"AWS Region: {AWS_REGION}")
        logger.info(f"Vector Index Name: {VECTOR_INDEX_NAME}")
        
        # Initialize client
        client = initialize_client()
        
        # Delete existing index
        delete_index(client)
        
        # Create new index with proper mapping
        create_index(client)
        
        # Check mapping
        check_index_mapping(client)
        
        logger.info("OpenSearch index fixed successfully")
        
    except Exception as e:
        logger.error(f"Failed to fix OpenSearch index: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
