# P6 — Local CPU profiling

`backend/scripts/profile_local.py` measures the local runtime without network
calls. It records model artifact sizes, model load time, query embedding,
FAISS, BM25, RRF, optional reranking, generation, end-to-end latency, and peak
process working-set memory. GPU VRAM is reported as unavailable because this
deployment is CPU-only.

Download duration is deliberately marked `not measured` when artifacts are
already cached; downloading is a one-time setup/API operation and should not be
mixed with offline query latency.

## Reproduce the profile

Run from `backend/` after the local models are cached:

```powershell
.\.venv\Scripts\python.exe scripts/profile_local.py --profile both --repetitions 3
```

To synchronize a source corpus before rebuilding, use an explicit source path:

```powershell
.\.venv\Scripts\python.exe scripts/profile_local.py `
  --source-dir "D:\Projects\docMind\data\Nouveau dossier" `
  --sync --rebuild-indexes --max-index-chunks 300 --index-batch-size 32 --profile both
```

`--max-index-chunks` is intentionally opt-in. A limited rebuild is useful for
bounded latency experiments, but its result must not be described as a
full-corpus indexing result. The JSON report is written to
`data/profiling/profile_local.json`, which is ignored from Git because it may
contain local paths and machine-specific measurements.

Dense rebuilds persist after each batch to
`data/indexes/fast/dense_rebuild.checkpoint.json`. Re-running the same command
resumes from the last completed batch; changing the stored chunks automatically
invalidates that checkpoint.

## P6.2 — full-corpus and reranker profile

P6.2 makes the full-corpus scope explicit and protects the active application
indexes. Run this from `backend/` for a retrieval/indexing profile:

```powershell
.\.venv\Scripts\python.exe scripts/profile_local.py `
  --full-corpus --isolated-indexes --rebuild-indexes `
  --profile both --repetitions 3 --skip-generation --skip-llm-load
```

The command reads every stored chunk, writes FAISS and BM25 files below
`data/profiling/runs/<run-id>/indexes`, and leaves `data/indexes/` unchanged.
It prints progress as `[P6.2]` batches and records the corpus document/chunk/page
counts, document status counts, extraction failures, index scope, and isolated
index path in the JSON report. `--full-corpus` intentionally rejects chunk
limits and document-only rebuilds.

If the BGE reranker has been downloaded locally, include either
`--reranker-path "C:\\models\\bge-reranker-v2-m3"` or set
`DOCMIND_RERANKER_MODEL_PATH`. The report then includes a reranker benchmark
with the candidate count and warm latency distribution. Without local weights,
the report records `not_configured`; it must not be presented as a reranker
measurement.

For a retrieval-only run, `--skip-generation --skip-llm-load` avoids loading the
4B generator and keeps the full-corpus memory measurement focused on extraction,
embedding, and retrieval. Generation latency remains covered by the P6.1
component profile.

### P6.2 feasibility result on the current local corpus

The stored catalog contained **36 documents and 1,325 extracted chunks** when
the isolated run started. The first 32-chunk embedding batch took **185,127 ms**
on the four-core CPU and the worker used approximately **1.63 GB** of working
memory. That projects to roughly **2.1 hours** for the complete rebuild at the
observed rate, before retrieval repetitions. The run was stopped after the first
completed batch to keep the laptop usable; its checkpoint remains under the
isolated `data/profiling/runs/<run-id>/` directory for a deliberate resume.

Resume that exact run (after deciding to spend the required time) by passing its
run directory, for example:

```powershell
.\.venv\Scripts\python.exe scripts/profile_local.py `
  --full-corpus --isolated-indexes --rebuild-indexes `
  --profile-run-dir "data/profiling/runs/20260728T180540Z-552" `
  --profile both --repetitions 3 --skip-generation --skip-llm-load
```

This is a deployment constraint, not a completed full-corpus latency result. The
active `data/indexes/` files were not modified. The next optimization should be
background/incremental indexing or a faster CPU embedding runtime before claiming
full-corpus P6.2 timings. P6.3 now provides the background worker and safe
incremental path for normal new-document uploads; full rebuilds remain resumable
maintenance work.

## P6.3 — background and incremental indexing

Normal uploads and re-index requests now return after extraction and queue their
embedding/index work on a single local worker. New documents append only their
own vectors when the active FAISS mapping is consistent. Replacements, deletes,
stale mappings, and interrupted rebuilds use the atomic full-rebuild path. The
queue state is included in `GET /api/runtime/status`, and the Knowledge Base UI
refreshes documents while they are `processing`.

## Measurement captured on 2026-07-28

The first completed end-to-end run used the existing 19-chunk indexed corpus.
Both local model artifacts were available:

The `.env` LLM path still points at a placeholder, so the profiler explicitly
used the downloaded repository GGUF instead of changing `.env`.
The runtime resolver now follows the selected local model in
`backend/models/models_config.json` when an environment path is missing, so a
fresh offline restart uses the downloaded artifact as well.

| Component | Result |
|---|---:|
| Qwen3-Embedding-0.6B artifact | 1,151.55 MB |
| Embedding model load | 865.8 ms |
| Qwen3-4B Q4 GGUF artifact | 2,381.59 MB |
| LLM load | 3,127.2 ms |
| Dense rebuild (19 chunks, CPU) | 26,969 ms |
| Query embedding | 759.6 ms |
| FAISS search | 8.9 ms |
| BM25 search | 0.07 ms |
| RRF fusion | 0.03 ms |
| Fast retrieval | 537.3 ms |
| Quality retrieval (without reranker) | 494.6 ms |
| Local generation | 39,996 ms / 107 completion tokens / 2.68 tokens/s |
| Measured end-to-end sample | 25,438 ms / 135 completion tokens / 5.42 tokens/s |
| Peak process working set | 5,349.55 MB |

A later three-sample warm Fast run on the same 19-chunk index measured a
median query embedding of **310.0 ms**, FAISS search of **4.66 ms**, and full
Fast retrieval of **281.9 ms** (p95: 481.4 ms, 5.1 ms, and 342.3 ms
respectively). The single-sample generation values above remain separate
because repeating a 25–40 second CPU generation is intentionally expensive.

The later checkpointed experiment reached 96/300 chunks before it was stopped;
the checkpoint was valid and resumable during that experiment. The 19-chunk
baseline was restored afterward, so no partial checkpoint is left active. The
27.0-second 19-chunk rebuild
shows that company-scale indexing should run as a background maintenance job,
not inside an upload request. The new batch builder provides that recovery path.

These are CPU measurements on the development laptop, not Kaggle GPU results.
The 4B model is close to the six-gigabyte operating budget once the embedding
model and runtime are loaded, so memory margin should be rechecked after a
full-corpus rebuild. Time-to-first-token was not measured because the current
generation path is non-streaming.

The broader sync experiment extracted 1,234 chunks from 35 documents before
the full embedding rebuild exceeded the bounded command window. Several PPTX,
XLSX, and encrypted PDF files returned explicit extraction failures; they are
not silently counted as indexed. This is an extraction/data-quality finding,
not a retrieval-latency result.

## Interpretation

Query embedding and local generation dominate the user-visible latency. FAISS,
BM25, and RRF are comparatively small on the current corpus. Quality mode is
therefore reasonable as an opt-in profile while the reranker remains unloaded;
the default should be selected only after repeating the profile on the actual
company corpus and a warm multi-query sample.
