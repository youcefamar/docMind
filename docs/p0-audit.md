# DocMind P0 Baseline Audit

Status: baseline complete on `main`

## Current public contracts

The existing frontend depends on these FastAPI routes:

- `GET /health`
- `POST /api/ask`
- `POST /api/upload`
- `GET /api/docs`
- `DELETE /api/doc/{doc_id}`
- `GET /api/models`

The response shapes currently expose an answer, confidence fields, and source
cards. The next API revision will preserve those routes while adding retrieval
profile, ingestion status, and machine-validatable citations.

## Confirmed prototype assumptions

- `backend/services/embedder.py` uses `all-MiniLM-L6-v2` and a 384-dimensional
  fallback vector.
- `backend/services/retriever.py` writes directly to PostgreSQL/pgvector.
- Chunking is character-based (`600` characters with `100` overlap).
- Uploads are processed synchronously inside the request handler.
- `backend/services/llm.py` can use a local GGUF model but still contains a
  Groq fallback.
- Model loading previously happened during module import, which is unsafe for
  offline startup and test collection.

## Product v1 target

The frozen research configuration is implemented behind stable service
interfaces:

```text
local file
  -> extractor
  -> normalized blocks
  -> token-aware chunks (320 / 48)
  -> Qwen3-Embedding-0.6B
  -> FAISS dense index + BM25 index
  -> Fast or Quality retrieval profile
  -> Qwen3-4B-Instruct-2507
  -> validated citations
```

Recommended local artifact layout for the single shared PC:

```text
data/
  documents/<document-id>/original-file
  metadata.sqlite
  indexes/<embedding-revision>/dense.faiss
  indexes/<embedding-revision>/chunks.jsonl
  indexes/<embedding-revision>/bm25.pkl
models/
```

SQLite is recommended for document/job metadata because the first product is a
single offline server. PostgreSQL can remain an optional future deployment
choice if concurrent multi-user workloads require it.

## P0 exit criteria

- Shared domain contracts exist independently of pgvector and Groq.
- Importing the backend does not download or load a Hugging Face model.
- The documented backend test command runs with coverage installed.
- The offline startup path and artifact layout are recorded.
- P1 can implement ingestion without changing the chat route contract.

## Validation recorded

- `python -m pytest`: **13 passed** with coverage enabled.
- `python -m ruff check .`: **passed**.
- Backend import no longer loads a Hugging Face model or initializes the legacy
  database unless explicitly enabled with `DOCMIND_INIT_LEGACY_DB=true`.
- Existing document listing returns an empty list when the legacy PostgreSQL
  service is unavailable, allowing the local API and test suite to start
  without Docker.
