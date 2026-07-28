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
  --sync --rebuild-indexes --max-index-chunks 300 --profile both
```

`--max-index-chunks` is intentionally opt-in. A limited rebuild is useful for
bounded latency experiments, but its result must not be described as a
full-corpus indexing result. The JSON report is written to
`data/profiling/profile_local.json`, which is ignored from Git because it may
contain local paths and machine-specific measurements.

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
