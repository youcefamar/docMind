import os
from typing import Any, Dict, List, Optional

import psycopg2
from pgvector.psycopg2 import register_vector
from psycopg2.extras import RealDictCursor

# PostgreSQL Connection details from environment variables
PG_HOST = os.getenv("POSTGRES_HOST", "localhost")
PG_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
PG_USER = os.getenv("POSTGRES_USER", "docmind")
PG_PASSWORD = os.getenv("POSTGRES_PASSWORD", "docmind_secret")
PG_DB = os.getenv("POSTGRES_DB", "docmind_db")
PG_URL = os.getenv("DATABASE_URL", f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_DB}")

class VectorStoreService:
    def __init__(self, connection_url: str = PG_URL, initialize: Optional[bool] = None):
        self.connection_url = connection_url
        if initialize is None:
            initialize = os.getenv("DOCMIND_INIT_LEGACY_DB", "false").lower() == "true"
        if initialize:
            self._init_db()

    def _get_connection(self):
        conn = psycopg2.connect(self.connection_url)
        register_vector(conn)
        return conn

    def _init_db(self):
        """
        Initializes PostgreSQL pgvector extension and creates doc_chunks table schema.
        """
        try:
            conn = psycopg2.connect(self.connection_url)
            conn.autocommit = True
            with conn.cursor() as cur:
                # 1. Enable pgvector extension
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

                # 2. Create chunks table with vector(384) column
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS doc_chunks (
                        id VARCHAR(128) PRIMARY KEY,
                        doc_id VARCHAR(128) NOT NULL,
                        filename VARCHAR(255) NOT NULL,
                        category VARCHAR(64) NOT NULL,
                        page_number INT NOT NULL,
                        total_pages INT NOT NULL,
                        chunk_index INT NOT NULL,
                        excerpt TEXT NOT NULL,
                        embedding vector(384) NOT NULL,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    );
                """)

                # 3. Create index for fast vector search if not exists
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS doc_chunks_embedding_idx
                    ON doc_chunks USING hnsw (embedding vector_cosine_ops);
                """)
            conn.close()
            print("[VectorStore] Successfully initialized PostgreSQL pgvector table schema!")
        except Exception as e:
            print(f"[VectorStore] Notice: pgvector DB init pending connection ({e}). Will connect on demand.")

    def add_document_chunks(self, chunks: List[Dict[str, Any]], embeddings: List[List[float]]):
        """
        Inserts document chunks and their 384d embeddings into pgvector.
        """
        if not chunks:
            return

        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                for c, emb in zip(chunks, embeddings):
                    cur.execute("""
                        INSERT INTO doc_chunks (
                            id, doc_id, filename, category, page_number, total_pages, chunk_index, excerpt, embedding
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO UPDATE SET
                            excerpt = EXCLUDED.excerpt,
                            embedding = EXCLUDED.embedding;
                    """, (
                        c["id"],
                        c["doc_id"],
                        c["filename"],
                        c["category"],
                        c["page_number"],
                        c["total_pages"],
                        c["chunk_index"],
                        c["text"],
                        emb
                    ))
            conn.commit()
        finally:
            conn.close()

    def search(
        self,
        query_embedding: List[List[float]],
        category: Optional[str] = None,
        top_k: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Queries pgvector using cosine distance (<=>) for top_k nearest neighbors.
        """
        if not query_embedding or len(query_embedding) == 0:
            return []

        emb_vector = query_embedding[0]
        conn = None
        sources = []

        try:
            conn = self._get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                if category and category.lower() != "all":
                    query = """
                        SELECT id, doc_id, filename, category, page_number, total_pages, excerpt,
                               (1 - (embedding <=> %s::vector)) AS similarity
                        FROM doc_chunks
                        WHERE category = %s
                        ORDER BY embedding <=> %s::vector
                        LIMIT %s;
                    """
                    cur.execute(query, (emb_vector, category, emb_vector, top_k))
                else:
                    query = """
                        SELECT id, doc_id, filename, category, page_number, total_pages, excerpt,
                               (1 - (embedding <=> %s::vector)) AS similarity
                        FROM doc_chunks
                        ORDER BY embedding <=> %s::vector
                        LIMIT %s;
                    """
                    cur.execute(query, (emb_vector, emb_vector, top_k))

                rows = cur.fetchall()
                for r in rows:
                    sources.append({
                        "doc_id": r["doc_id"],
                        "filename": r["filename"],
                        "category": r["category"],
                        "page_number": r["page_number"],
                        "total_pages": r["total_pages"],
                        "excerpt": r["excerpt"],
                        "similarity": round(float(r["similarity"]), 3)
                    })
        except Exception as e:
            print(f"[pgvector Search Error] {e}")
        finally:
            if conn:
                conn.close()

        return sources

    def list_all_documents(self) -> List[Dict[str, Any]]:
        """
        Lists unique uploaded PDF documents from pgvector.
        """
        conn = None
        summary = []

        try:
            conn = self._get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = """
                    SELECT doc_id AS id,
                           filename,
                           category,
                           COUNT(*) AS chunk_count,
                           MAX(total_pages) AS total_pages,
                           MIN(created_at)::text AS created_at
                    FROM doc_chunks
                    GROUP BY doc_id, filename, category;
                """
                cur.execute(query)
                summary = [dict(r) for r in cur.fetchall()]
        except Exception as e:
            print(f"[pgvector List Docs Error] {e}")
        finally:
            if conn:
                conn.close()

        return summary

    def delete_document_by_id(self, doc_id: str) -> int:
        """
        Deletes all chunks of doc_id from pgvector.
        """
        conn = None
        deleted_count = 0

        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                cur.execute("DELETE FROM doc_chunks WHERE doc_id = %s;", (doc_id,))
                deleted_count = cur.rowcount
            conn.commit()
        finally:
            if conn:
                conn.close()

        return deleted_count
