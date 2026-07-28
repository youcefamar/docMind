# P4 — Local generation and citation validation

P4 replaces the prototype hosted-LLM assumption with a local-only generation
boundary. The target runtime is a cached Qwen3-4B instruct GGUF model loaded by
`llama-cpp-python` on CPU.

## Runtime behavior

1. Retrieval returns ranked chunks.
2. The service labels them deterministically as `[S1]`, `[S2]`, and so on.
3. The local model receives only the labelled context and the user question.
4. Citation labels are parsed and mapped back to the exact chunk/document.
5. Unknown labels (for example `[S99]`) are ignored and never become source
   metadata.
6. Empty or low-score context returns `I don't know based on the provided
   documents.`

The API adds a `citations` array to `POST /api/ask`. Each item contains the
source ID, chunk/document identity, location, excerpt, and a conservative
lexical `supported` signal. This signal is a transparent check, not a semantic
entailment proof.

## Offline configuration

```env
DOCMIND_LLM_MODEL_PATH=C:/models/qwen3-4b-instruct-q4_k_m.gguf
DOCMIND_LLM_CONTEXT_TOKENS=4096
DOCMIND_LLM_THREADS=4
DOCMIND_LLM_MAX_TOKENS=600
DOCMIND_MIN_SOURCE_SCORE=0.20
```

The service performs no download and makes no hosted API call. If the model
file is absent, a deterministic extractive fallback is used for development;
this fallback must not be used for measured CV performance claims.

## Terminal observability

Each `POST /api/ask` writes stage logs containing the retrieval profile, source
count, citation count, active LLM backend, and retrieval/generation/total
latencies. Question text is hidden by default. Use `DOCMIND_LOG_QUERIES=true`
for local debugging when printing the question is acceptable.

## Model download API

The model registry in `backend/models/models_config.json` points to the
Qwen3-4B GGUF artifact on Hugging Face. Downloads are explicit setup actions,
not runtime inference:

```text
GET  /api/models/
POST /api/models/download   {"model_id":"qwen3-4b-q4"}
GET  /api/models/qwen3-4b-q4
POST /api/models/select      {"model_id":"qwen3-4b-q4"}
```

The downloader uses the Hugging Face cache, writes through a temporary file,
rejects unsafe filenames, and exposes queued/downloading/completed/failed
status. After selection, the already-downloaded file is loaded by the local
LLM service; no request is sent to Hugging Face for answering questions.

## Tests

`backend/tests/test_llm.py` covers unknown citation rejection, source overlap,
prompt labelling, no-source refusal, low-score refusal, and the no-weights
fallback. API tests verify citations are returned with the existing source
contract.

Product settings such as categories, upload extensions, size limits, and
retrieval top-k values are environment-backed and exposed safely through
`GET /api/config/`; the frontend consumes that endpoint instead of duplicating
business configuration.
