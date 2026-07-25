# 1. Vector Database Selection: PostgreSQL with `pgvector` Extension

- **Status**: Accepted
- **Date**: 2026-07-25
- **Deciders**: AI Engineering Team

---

## Context & Problem Statement

DocMind requires a high-performance vector database to store and query 384-dimensional vector embeddings generated from company PDF documents. The vector store must support cosine similarity search (`<=>` operator), metadata filtering (`category`, `filename`, `page_number`), and fit seamlessly into enterprise production infrastructure.

---

## Decision Drivers

- **Enterprise Reliability**: Standard PostgreSQL with native vector capabilities (`pgvector`).
- **Relational Integrity**: Allows linking PDF text chunks to relational tables and auditing metadata directly using SQL queries.
- **HNSW Index Performance**: High-speed Cosine similarity indexing using `hnsw (embedding vector_cosine_ops)`.

---

## Decision Outcome

**Chosen Option**: **`pgvector` (PostgreSQL 16 extension)** via official `pgvector/pgvector:pg16` Docker image.

### Table Schema (`doc_chunks`)
```sql
CREATE EXTENSION IF NOT EXISTS vector;

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

CREATE INDEX IF NOT EXISTS doc_chunks_embedding_idx 
ON doc_chunks USING hnsw (embedding vector_cosine_ops);
```
