"""
Qdrant Vector Database Client
Handles pattern storage and similarity search
"""

import os
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from dotenv import load_dotenv

load_dotenv()

class QdrantManager:
    def __init__(self):
        self.url = os.getenv("QDRANT_URL")
        self.api_key = os.getenv("QDRANT_API_KEY")
        
        if self.url and self.api_key:
            self.client = QdrantClient(
                url=self.url,
                api_key=self.api_key
            )
        else:
            # Use in-memory for local development
            self.client = QdrantClient(":memory:")
    
    def test_connection(self) -> dict:
        """
        Test Qdrant connection
        """
        try:
            collections = self.client.get_collections()
            return {
                "status": "success",
                "message": "Qdrant connected successfully",
                "collections": len(collections.collections),
                "mode": "cloud" if self.url else "memory"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    def create_collection(self, collection_name: str, vector_size: int = 1536):
        """
        Create a new collection for patterns
        """
        try:
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
            )
            return {"status": "success", "collection": collection_name}
        except Exception as e:
            return {"status": "error", "message": str(e)}