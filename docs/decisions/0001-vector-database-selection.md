# 1. Vector Database Selection: ChromaDB & pgvector

- **Status**: Accepted
- **Date**: 2026-07-25
- **Deciders**: AI Engineering Team

---

## Context & Problem Statement

DocMind requires an efficient, developer-friendly vector store to persist and query high-dimensional embeddings generated from enterprise PDF documents. The vector database must support cosine similarity search, metadata filtering (such as document category, filename, and page numbers), and zero-friction deployment.

---

## Decision Drivers

- **Ease of Setup & Development**: Minimal external infrastructure overhead for local development and notebook experimentation.
- **Metadata Filtering**: Native support for filtering queries by category tags (`HR`, `Tech`, `Finance`).
- **Persistence & Portability**: Ability to persist embeddings to local disk or Docker volume without complex cluster management.
- **Production Path**: Simple upgrade path to enterprise PostgreSQL (`pgvector`) if required by infrastructure constraints.

---

## Considered Options

1. **ChromaDB (Selected for primary deployment)**
2. **PostgreSQL with `pgvector` extension**
3. **Pinecone / Qdrant (Cloud SaaS)**

---

## Decision Outcome

**Chosen Option**: **ChromaDB** (with optional `pgvector` migration path).

### Positive Consequences
- **Zero Configuration**: Runs in-process with Python via `chromadb.PersistentClient`, storing vector indices directly on disk in `backend/db/chroma`.
- **Fast Similarity Filtering**: Built-in HNSW index with cosine distance metrics.
- **Category Metadata Support**: Supports `where={"category": "HR"}` queries seamlessly out of the box.

### Negative Consequences
- For massive scale (>10M vectors), a dedicated PostgreSQL + `pgvector` instance or distributed vector database cluster may be preferred.
