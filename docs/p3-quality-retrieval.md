# DocMind P3 Quality Retrieval

P3 adds the Quality profile without changing the Fast API contract.

## Quality flow

```text
question
  -> Qwen dense FAISS candidates
  -> BM25 lexical candidates
  -> Reciprocal Rank Fusion (RRF)
  -> optional local BGE reranker
  -> final top-5 source chunks
```

BM25 uses a persistent Unicode-aware tokenizer and stores its postings in
`data/indexes/quality/bm25.json`. Dense and lexical rankings are never compared
by raw score; RRF combines their rank positions with `rrf_k=60`.

Set `DOCMIND_RERANKER_MODEL_PATH` to a locally cached
`BAAI/bge-reranker-v2-m3` CrossEncoder directory to enable CPU reranking. If it
is absent, Quality mode still returns RRF-ranked results and does not download
anything.

## API behavior

Send `{"retrieval_profile": "quality"}` to `POST /api/ask`. The response keeps
the same answer/source shape and reports `retrieval_profile: "quality"`.
Quality requires a ready Qwen dense index and BM25 index; otherwise the API
returns `501` rather than silently claiming that the profile is active.

## Validation

- BM25 persistence and reload are tested.
- RRF ordering is tested for shared evidence.
- Quality top-k and retrieval-profile metadata are tested.
- Optional reranker scoring is tested with a local deterministic double.
- Fast and Quality API routing are tested.
- Backend checks: `ruff check .` passed; `pytest` reports **31 passed**.
