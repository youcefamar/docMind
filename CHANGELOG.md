# Changelog 📜

All notable changes to **DocMind** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-07-25

### Added
- **Core RAG Pipeline**:
  - `pypdf` page-by-page document extraction and overlapping chunking.
  - Local vector embeddings via `sentence-transformers` (`all-MiniLM-L6-v2`).
  - Persistent vector storage and cosine similarity search via `ChromaDB`.
  - Zero-latency LLM synthesis via Groq API (`llama-3.1-8b-instant`).
  - Grounding validation enforcing "I don't know" when context is insufficient.
  - Confidence scoring system (High, Medium, Low).
- **FastAPI Backend Services**:
  - `POST /api/ask`: Semantic RAG question answering endpoint with multi-turn chat history.
  - `POST /api/upload`: Multi-file PDF upload with category metadata tagging (`HR`, `Tech`, `Finance`, `Legal`, etc.).
  - `GET /api/docs`: Document catalog listing with chunk & page statistics.
  - `DELETE /api/doc/{id}`: Clean vector embedding removal.
- **Next.js 15 Frontend**:
  - Modern dark mode glassmorphic UI built with Next.js 15 App Router and Tailwind CSS.
  - Interactive multi-turn chat interface with category filters and prompt suggestions.
  - Expandable source citation cards highlighting document title, page numbers, match score, and excerpt quotes.
  - Admin management panel with stats cards and document catalog table.
  - NextAuth.js authentication setup.
- **DevOps & Infrastructure**:
  - Containerized production setup with `docker-compose.yml`.
  - Prototype Jupyter Notebook `notebooks/rag_pipeline_demo.ipynb`.
