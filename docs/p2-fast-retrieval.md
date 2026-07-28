# DocMind P2 Fast Retrieval

P2 adds the dense Fast profile on top of the P1 ingestion metadata.

## Runtime configuration

Set `DOCMIND_EMBEDDING_MODEL_PATH` to a locally cached
`Qwen/Qwen3-Embedding-0.6B` SentenceTransformers directory. The adapter uses
CPU inference and `local_files_only=True`; it never downloads weights during
API startup.

If the path is not configured, uploads remain `partially_indexed` and the API
does not claim that Fast retrieval is available. The old pgvector path remains
only as a transitional fallback for previously indexed documents.

## Fast flow

```text
question
  -> Qwen3-Embedding-0.6B (normalized vectors)
  -> FAISS IndexFlatIP cosine search
  -> chunk-ID mapping
  -> SQLite chunk/document metadata
  -> top-5 source results
```

The persistent artifacts are stored under:

```text
data/indexes/fast/dense.faiss
data/indexes/fast/dense_mapping.json
```

The mapping records the embedding dimension, model revision, and ordered chunk
IDs. Rebuilds are written through temporary files and replaced atomically.
Document upload, replacement, and deletion rebuild the index from the current
SQLite chunks so stale vectors are not retained.

## API contract

`POST /api/ask` accepts `retrieval_profile`, defaulting to `fast`, and returns
the selected profile plus ranked source metadata. `quality` intentionally
returns `501` until P3 is implemented.

## Validation

- FAISS persistence and reload are covered by deterministic tests.
- Category filtering is tested after dense search.
- Qwen output normalization is tested with a fake local model.
- Fast API routing is tested with a deterministic dense-index double.
- Backend checks: `ruff check .` passed; `pytest` reports **26 passed**.
