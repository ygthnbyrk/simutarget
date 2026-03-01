"""Qdrant vector store for persona memories."""

import os
from typing import Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.models import Distance, VectorParams, PointStruct
import uuid


class VectorStore:
    """Vector store using Qdrant for persona memories."""
    
    COLLECTION_NAME = "persona_memories"
    VECTOR_SIZE = 1536  # OpenAI embedding size
    
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
    ):
        self.host = host or os.getenv("QDRANT_HOST", "localhost")
        self.port = port or int(os.getenv("QDRANT_PORT", "6333"))
        
        self.client = QdrantClient(host=self.host, port=self.port)
        self._ensure_collection()
    
    def _ensure_collection(self):
        """Create collection if it doesn't exist."""
        collections = self.client.get_collections().collections
        collection_names = [c.name for c in collections]
        
        if self.COLLECTION_NAME not in collection_names:
            self.client.create_collection(
                collection_name=self.COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=self.VECTOR_SIZE,
                    distance=Distance.COSINE,
                ),
            )
    
    def add_memory(
        self,
        persona_id: str,
        memory_text: str,
        embedding: list[float],
        metadata: Optional[dict] = None,
    ) -> str:
        """Add a memory for a persona."""
        
        memory_id = str(uuid.uuid4())
        
        payload = {
            "persona_id": persona_id,
            "memory_text": memory_text,
            **(metadata or {}),
        }
        
        self.client.upsert(
            collection_name=self.COLLECTION_NAME,
            points=[
                PointStruct(
                    id=memory_id,
                    vector=embedding,
                    payload=payload,
                )
            ],
        )
        
        return memory_id
    
    def search_memories(
        self,
        persona_id: str,
        query_embedding: list[float],
        limit: int = 5,
    ) -> list[dict]:
        """Search memories for a specific persona."""
        
        results = self.client.search(
            collection_name=self.COLLECTION_NAME,
            query_vector=query_embedding,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="persona_id",
                        match=models.MatchValue(value=persona_id),
                    )
                ]
            ),
            limit=limit,
        )
        
        return [
            {
                "id": str(r.id),
                "memory_text": r.payload.get("memory_text", ""),
                "score": r.score,
                "metadata": {k: v for k, v in r.payload.items() if k not in ["persona_id", "memory_text"]},
            }
            for r in results
        ]
    
    def get_all_memories(self, persona_id: str, limit: int = 100) -> list[dict]:
        """Get all memories for a persona."""
        
        results, _ = self.client.scroll(
            collection_name=self.COLLECTION_NAME,
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="persona_id",
                        match=models.MatchValue(value=persona_id),
                    )
                ]
            ),
            limit=limit,
        )
        
        return [
            {
                "id": str(r.id),
                "memory_text": r.payload.get("memory_text", ""),
                "metadata": {k: v for k, v in r.payload.items() if k not in ["persona_id", "memory_text"]},
            }
            for r in results
        ]
    
    def delete_memory(self, memory_id: str) -> bool:
        """Delete a specific memory."""
        
        self.client.delete(
            collection_name=self.COLLECTION_NAME,
            points_selector=models.PointIdsList(
                points=[memory_id],
            ),
        )
        return True
    
    def delete_persona_memories(self, persona_id: str) -> bool:
        """Delete all memories for a persona."""
        
        self.client.delete(
            collection_name=self.COLLECTION_NAME,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="persona_id",
                            match=models.MatchValue(value=persona_id),
                        )
                    ]
                )
            ),
        )
        return True
    
    def get_stats(self) -> dict:
        """Get collection statistics."""
        
        info = self.client.get_collection(self.COLLECTION_NAME)
        return {
            "total_vectors": info.vectors_count,
            "indexed_vectors": info.indexed_vectors_count,
            "status": info.status,
        }
