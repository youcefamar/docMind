# DocMind System Architecture 🏛️

> This document contains the original prototype flow. The current offline
> ingestion implementation is documented in [P1 ingestion](p1-ingestion.md);
> FAISS/BM25 retrieval is documented in [P2 Fast retrieval](p2-fast-retrieval.md)
> and [P3 Quality retrieval](p3-quality-retrieval.md); local Qwen generation
> and citation validation are documented in [P4 local generation](p4-local-generation.md).

DocMind is designed as a modular, lightweight Retrieval-Augmented Generation (RAG) platform that enables enterprise teams to query internal PDF documents in natural language with source citation grounding.

---

## 📐 System Dataflow & Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    actor Employee as Employee / Admin
    participant FE as Next.js 15 Frontend
    participant BE as FastAPI Backend
    participant Emb as SentenceTransformers
    participant DB as Local FAISS + BM25 indexes
    participant LLM as Local Qwen3-4B GGUF

    rect rgb(240, 244, 255)
    note right of Employee: 1. Ingestion Phase
    Employee->>FE: Upload document or place it in managed knowledge folder
    FE->>BE: POST /api/upload or POST /api/sources/sync
    BE->>BE: Extract text page-by-page (pypdf)
    BE->>BE: Chunk text (configured chunk size and overlap)
    BE->>Emb: Generate configured multilingual embeddings
    Emb-->>BE: Return Vector Floating Arrays
    BE->>DB: Add Documents, Metadatas & Embeddings
    DB-->>BE: Confirmation
    BE-->>FE: Return Document Summary
    end

    rect rgb(245, 255, 245)
    note right of Employee: 2. Query & Retrieval Phase
    Employee->>FE: Ask Question ("What is the PTO policy?")
    FE->>BE: POST /api/ask (Question + History + Category Filter)
    BE->>Emb: Embed Question Text
    Emb-->>BE: Return Query Vector
    BE->>DB: Cosine similarity query (configured top-k and category filter)
    DB-->>BE: Top Matching Context Chunks + Page Numbers + Scores
    BE->>LLM: Prompt LLM (System Grounding + Context Chunks + Question)
    LLM-->>BE: Generated Answer with Citation Verification
    BE->>BE: Evaluate Confidence Score & Label
    BE-->>FE: JSON (Answer + Confidence + Verified Source Cards)
    FE-->>Employee: Render Response + Expandable Citation Cards
    end
```

---

## 🛠️ Subsystem Responsibilities

### 1. Next.js 15 Frontend Layer
- **App Router (`app/`)**: Provides Server Side Rendering (SSR) and Client component isolation.
- **Tailwind Design System**: Custom glassmorphic dark theme, glowing indigo visual tokens, and responsive mobile-first views.
- **NextAuth.js**: Protects workspace routes (`/`, `/admin`) and handles user session state.
- **Client Components (`components/`)**:
  - `ChatWindow.tsx`: Manages multi-turn conversation state, category pill selection, prompt suggestions, and streaming responses.
  - `SourceCard.tsx`: Formats citation cards displaying filename, page number, similarity percentage, and chunk quotes.
  - `UploadPanel.tsx`: Handles PDF drag-and-drop file inputs, category selection, document indexing metrics, and deletion requests.

### 2. FastAPI Backend Layer
- **`main.py`**: Initializes ASGI app, handles CORS headers, mounts sub-routers, and provides `/health`.
- **`routes/chat.py`**: Exposes `POST /api/ask`. Coordinates configured dense/lexical retrieval, local LLM generation, and response serialization.
- **`routes/documents.py`**: Exposes `POST /api/upload`, `GET /api/docs`, and `DELETE /api/doc/{id}`.
- **`routes/sources.py`**: Exposes managed-folder sync/status endpoints. The
  hash manifest detects additions, edits, and removals without a filesystem
  watcher, which keeps the offline workstation flow explicit and predictable.
- **`services/embedder.py`**: Reads supported local formats, cleans whitespace, generates overlapping chunks with metadata (`doc_id`, `filename`, `category`, `page_number`, `chunk_index`), and embeds with the configured multilingual model.
- **`services/retriever.py`**: Retains the legacy pgvector adapter; the active path uses persistent FAISS/BM25 indexes with category metadata filtering.
- **`services/llm.py`**: Runs the local Qwen3-4B GGUF adapter, formats deterministic
  source labels, validates citations, enforces insufficient-evidence behavior,
  and scores answer confidence.

---

## 🔒 Security & Data Isolation
- **Data Persistence**: SQLite metadata, FAISS dense files, BM25 files, uploaded originals, and the managed-folder hash manifest live below the configured local data directory.
- **Zero Hallucination Grounding**: System prompts explicitly prevent LLM speculation outside retrieved chunks.
- **Network Boundaries**: In production, FastAPI API endpoints are restricted behind internal Docker network bridges or reverse proxies (Nginx / Hetzner VPS firewall).
