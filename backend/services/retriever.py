import os
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings

CHROMA_DB_DIR = os.getenv("CHROMA_DB_DIR", os.path.join(os.path.dirname(__file__), "..", "db", "chroma"))

class VectorStoreService:
    def __init__(self, db_path: str = CHROMA_DB_DIR):
        os.makedirs(db_path, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(
            name="docmind_knowledge_base",
            metadata={"hnsw:space": "cosine"}
        )

    def add_document_chunks(self, chunks: List[Dict[str, Any]], embeddings: List[List[float]]):
        """
        Stores chunks and their computed embeddings into the Chroma vector DB.
        """
        if not chunks:
            return

        ids = [c["id"] for c in chunks]
        documents = [c["text"] for c in chunks]
        metadatas = [
            {
                "doc_id": c["doc_id"],
                "filename": c["filename"],
                "category": c["category"],
                "page_number": c["page_number"],
                "total_pages": c["total_pages"],
                "chunk_index": c["chunk_index"],
                "created_at": c["created_at"]
            }
            for c in chunks
        ]

        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )

    def search(
        self, 
        query_embedding: List[List[float]], 
        category: Optional[str] = None, 
        top_k: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Queries Chroma DB for the top_k nearest chunk neighbors.
        """
        where_filter = {}
        if category and category.lower() != "all":
            where_filter = {"category": category}

        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=top_k,
            where=where_filter if where_filter else None
        )

        sources = []
        if results and results.get("documents") and len(results["documents"]) > 0:
            docs = results["documents"][0]
            metas = results["metadatas"][0]
            distances = results["distances"][0] if "distances" in results and results["distances"] else [0.0] * len(docs)

            for doc_text, meta, dist in zip(docs, metas, distances):
                # Cosine distance: similarity = 1 - distance
                similarity = round(max(0.0, 1.0 - dist), 3)
                sources.append({
                    "doc_id": meta.get("doc_id"),
                    "filename": meta.get("filename"),
                    "category": meta.get("category"),
                    "page_number": meta.get("page_number"),
                    "total_pages": meta.get("total_pages"),
                    "excerpt": doc_text,
                    "similarity": similarity
                })

        return sources

    def list_all_documents(self) -> List[Dict[str, Any]]:
        """
        Lists summary of all unique documents currently stored in vector store.
        """
        all_items = self.collection.get()
        if not all_items or not all_items.get("metadatas"):
            return []

        doc_summary = {}
        for meta in all_items["metadatas"]:
            doc_id = meta.get("doc_id")
            if not doc_id:
                continue

            if doc_id not in doc_summary:
                doc_summary[doc_id] = {
                    "id": doc_id,
                    "filename": meta.get("filename", "Unknown.pdf"),
                    "category": meta.get("category", "General"),
                    "chunk_count": 0,
                    "total_pages": meta.get("total_pages", 1),
                    "created_at": meta.get("created_at", "")
                }
            
            doc_summary[doc_id]["chunk_count"] += 1
            if meta.get("total_pages", 1) > doc_summary[doc_id]["total_pages"]:
                doc_summary[doc_id]["total_pages"] = meta.get("total_pages", 1)

        return list(doc_summary.values())

    def delete_document_by_id(self, doc_id: str) -> int:
        """
        Deletes all chunks belonging to doc_id.
        """
        all_items = self.collection.get(where={"doc_id": doc_id})
        if not all_items or not all_items.get("ids"):
            return 0

        ids_to_delete = all_items["ids"]
        self.collection.delete(ids=ids_to_delete)
        return len(ids_to_delete)
