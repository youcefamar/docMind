# DocMind P1 Ingestion

P1 is implemented on `main`. It establishes the local ingestion boundary that
P2's FAISS/BM25 indexers will consume.

## Runtime flow

```text
multipart upload
  -> filename, size, extension, and signature validation
  -> SHA-256 duplicate/replacement decision
  -> original stored under data/documents/<document-id>/
  -> extractor produces stable page blocks and chunks
  -> metadata.sqlite stores document, job, block, and chunk records
  -> partially_indexed (until P2 attaches a vector indexer)
```

`DocumentIngestionService.ingest` accepts an optional indexer callback. P2 can
attach FAISS/BM25 indexing without changing upload validation, extraction, or
the API response contract.

## Lifecycle behavior

- Same filename and same SHA-256: idempotent duplicate response.
- Same filename with different content: rejected unless `replace=true`.
- Replacement preserves the document ID and replaces the original/chunks.
- `reindex(document_id)` reads the locally stored original and reruns extraction.
- Delete removes the metadata records and local original file.
- Failures are persisted with a machine-readable error code and detail.

## API behavior

- `POST /api/upload` now uses local ingestion and returns `status`.
- New successful uploads are `partially_indexed` until vector indexing exists.
- `GET /api/docs` reads the local catalog, including status and errors.
- `DELETE /api/doc/{doc_id}` removes the local document and extracted metadata.

## Validation

- Backend Ruff checks pass.
- Backend test suite: **21 passed**.
- Tests cover extraction, signatures, duplicate detection, replacement,
  re-indexing, deletion, and API upload/catalog/delete behavior.
