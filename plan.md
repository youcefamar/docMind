# DocMind: Research v1 Closeout and Product Integration Plan

## 1. Final direction

DocMind is a CV-quality, local-first Retrieval-Augmented Generation application for small companies that need to search internal documents without sending their data to an external LLM service.

The project will not begin a separate “research v2” phase now. The roadmap is:

```text
DOCMIND RESEARCH v1
        │
        ↓
Freeze the current winning stack
        │
        ├── Run the locked 12-question TEST once
        └── Run the existing 4 no-answer questions
        │
        ↓
Close research v1
        │
        ↓
PRODUCT INTEGRATION
        │
        ├── production extraction interfaces
        ├── embedding and indexing services
        ├── Fast retrieval mode
        ├── Quality retrieval mode
        ├── local Qwen generation
        ├── validated citations
        └── API and UI integration
        │
        ↓
FUTURE FEATURE WORK
        │
        ├── XLSX and table QA
        ├── OCR and scanned documents
        ├── harder/larger gold benchmark
        ├── Arabic support
        └── feature-specific validation
```

The priority is to finish the frozen v1 evaluation and build the product. New model searches, benchmark expansion, OCR, tables, and Arabic must not block the first application integration.

## 2. Target deployment constraints

### Target laptop

- CPU: Intel i7 11th generation, 4 cores
- Memory: 20 GB RAM
- GPU: none
- Local generator budget: approximately 6 GB maximum
- Normal operation: fully offline
- Models and packages: downloaded before deployment and cached or transferred locally

### Initial product assumptions

- The application runs on one trusted laptop or local shared server.
- Anyone with access to that machine can initially use the chatbot.
- Product v1 focuses on the file types validated by research v1: PDF, PPTX, and DOCX.
- Simple TXT and Markdown ingestion may be added during integration if it does not delay the measured core pipeline.
- XLSX/table reasoning, OCR/scans, Arabic, direct database querying, and fine-grained access control are future features.
- Product v1 must not claim support for capabilities that have not been validated.

### Local knowledge architecture

A shared folder is not itself the database. The local product will separate:

- original file storage;
- extracted document blocks and metadata;
- dense and lexical search indexes;
- the local LLM runtime;
- the API and web application.

Direct SQL database access is not part of product v1. A future connector must use read-only database roles and a separate security design.

## 3. Research v1 history

Research v1 has already completed the major model-selection work. This history must be preserved in the research report and portfolio documentation.

### Completed corpus and evaluation work

- [x] Cleaned a 44-file company-like corpus.
- [x] Extracted PDF content page by page.
- [x] Extracted PPTX content slide by slide.
- [x] Extracted DOCX paragraphs and tables.
- [x] Produced stable extraction and chunk artifacts.
- [x] Compared small, medium, and large token-aware chunks.
- [x] Built DEV and TEST gold-evidence splits.
- [x] Added evidence-unit-aware retrieval metrics.
- [x] Identified and corrected multi-evidence fragmentation cases.

### Completed retrieval work

- [x] Compared BM25 sparse retrieval.
- [x] Compared dense retrieval across BGE-M3, multilingual-E5-large, and Qwen3-Embedding-0.6B.
- [x] Compared dense-only and Dense + BM25 hybrid retrieval.
- [x] Used Reciprocal Rank Fusion for hybrid results.
- [x] Evaluated `BAAI/bge-reranker-v2-m3`.
- [x] Measured the trade-off between first-rank quality and complete-evidence preservation.
- [x] Selected Qwen3-Embedding-0.6B as the strongest tested DEV embedding.
- [x] Selected medium chunks of approximately 320 tokens with 48-token overlap.
- [x] Selected a quality-oriented hybrid and reranked retrieval profile.
- [x] Retained dense-only retrieval as the simpler profile.

### Completed generation work

- [x] Froze retrieved contexts before comparing generators.
- [x] Evaluated Qwen3-4B-Instruct-2507.
- [x] Evaluated Phi-4-mini.
- [x] Evaluated Granite-3.3-2B.
- [x] Evaluated xLAM-7B.
- [x] Compared correctness proxies, groundedness, citations, language behavior, latency, throughput, and observed GPU memory.
- [x] Selected Qwen3-4B as the current DEV quality winner.
- [x] Selected Phi-4-mini as the current DEV efficiency alternative.

### Current DEV findings

- `Qwen/Qwen3-Embedding-0.6B` was the strongest tested embedding on this corpus.
- Medium chunks around 320 tokens with 48-token overlap were preferred.
- Dense + BM25 + RRF + BGE reranking was selected as the quality-oriented retrieval path.
- The selected hybrid and reranked configuration achieved `CompleteEvidence@5 = 1.0000` on the 46-question DEV retrieval benchmark.
- `Qwen/Qwen3-4B-Instruct-2507` was the strongest tested generator.
- Qwen3-4B achieved an automatic DEV quality score of `0.7173`.
- Qwen3-4B won 34 of 46 DEV generation questions.
- Phi-4-mini was the efficiency-oriented alternative.

These are corpus-conditional DEV findings, not universal claims.

## 4. Frozen research v1 configuration

No additional embedding models, rerankers, chunk configurations, or generative LLMs will be tested during research v1.

```yaml
retrieval:
  embedding: Qwen/Qwen3-Embedding-0.6B
  chunk_size_tokens: 320
  chunk_overlap_tokens: 48
  dense: true
  bm25: true
  fusion: rrf
  reranker: BAAI/bge-reranker-v2-m3
  rerank_top_n: 30
  final_k: 5

generation:
  model: Qwen/Qwen3-4B-Instruct-2507
  quantization: 4bit
  citations: inline
  language_policy: same_as_question
```

This configuration was frozen for the final TEST and no-answer evaluations. Weaknesses discovered after freezing were recorded as limitations rather than fixed by retuning the experiment.

## 5. Research v1 closeout

The final research tasks are complete. Research v1 is now closed and no further model-selection work is required before product integration.

### R4.1 — locked 12-question TEST — completed

The existing 12-question answerable TEST set was run exactly once with the frozen configuration.

Report retrieval metrics:

- EvidenceRecall@1
- EvidenceRecall@3
- EvidenceRecall@5
- CompleteEvidence@5

Recorded results:

- EvidenceRecall@1: `0.7500`
- EvidenceRecall@3: `1.0000`
- EvidenceRecall@5: `1.0000`
- CompleteEvidence@5: `1.0000`

Freeze the resulting top-5 TEST contexts and run Qwen3-4B generation over them.

Report:

- semantic correctness proxy;
- gold-answer coverage;
- groundedness proxy;
- citation presence;
- citation validity;
- citation support;
- language compliance;
- response length/verbosity;
- generation latency and throughput in the Kaggle environment.

Do not use TEST results to change the configuration.

### R4.2 — four no-answer questions — completed

The existing four no-answer questions were run with the same frozen stack.

Measure:

- refusal accuracy;
- false-answer/hallucination rate;
- citation presence on unsupported answers;
- unsupported-citation rate.

Recorded results:

- refusal accuracy: `4/4`
- false-answer rate: `0/4`
- unsupported-citation rate: `0/4`
- French refusal-language issues: `2/4`

Manually inspect all four raw answers. The current prompt may contain a conflict between the fixed refusal wording and the same-language response policy, so the report must describe observed behavior without changing the frozen prompt.

### R4.3 — close research v1 — completed

Update the final research report with:

- corpus description;
- extraction methodology;
- chunking comparison;
- gold benchmark construction;
- DEV/TEST split;
- embedding comparison;
- BM25, dense, and hybrid retrieval;
- evidence-aware metrics;
- RRF and reranker experiments;
- frozen-context generator comparison;
- French/English results;
- efficiency results;
- frozen architecture;
- locked TEST results;
- no-answer results;
- known limitations.

The final report contains the frozen TEST and no-answer results. Research v1 is complete; subsequent work belongs to product integration or future feature validation.

## 6. Product v1 architecture

Notebook code must not be copied directly into the backend. The measured behavior will be implemented behind focused, testable production components:

```text
Document ingestion
    ↓
Extraction
    ↓
Chunking
    ↓
Embedding
    ↓
FAISS dense index
    +
BM25 lexical index
    ↓
Retrieval profile selection
    ↓
Optional RRF and reranking
    ↓
Context assembly
    ↓
Local Qwen generation
    ↓
Citation validation and response metadata
```

### Component responsibilities

#### Document ingestion

- validate extension, MIME/signature, file size, and filename;
- calculate a stable document hash;
- detect duplicates and replacements;
- store the original file locally;
- create an ingestion status: queued, processing, indexed, partially indexed, or failed;
- retain structured failure details.

#### Extraction

- preserve document ID and version;
- preserve page, slide, paragraph, and table-location metadata;
- return a shared normalized block structure;
- support PDF, PPTX, and DOCX first;
- allow future extractors to be added without changing retrieval or routes.

#### Chunking

- use the frozen 320-token target and 48-token overlap initially;
- retain block and source-location relationships;
- generate stable chunk IDs;
- keep enough metadata to reconstruct citations;
- record tokenizer/model revision used for chunk sizing.

#### Embedding

- use `Qwen/Qwen3-Embedding-0.6B`;
- normalize document and query embeddings consistently;
- process documents in batches;
- persist model revision and embedding dimension;
- operate from a local model directory after installation.

#### Indexing

- maintain a FAISS dense index and chunk-ID mapping;
- maintain a BM25 lexical index over the same chunk IDs;
- support atomic rebuild or safe incremental updates;
- remove/re-index all affected entries when a document is replaced or deleted;
- persist enough metadata to reload indexes after application restart.

#### Retrieval

- expose Fast and Quality profiles through one interface;
- return ranked chunks with trace metadata;
- keep RRF and reranking modular;
- prevent profile-specific behavior from leaking into API routes.

#### Context assembly

- deduplicate overlapping evidence;
- keep the selected rank and score metadata;
- enforce the generator context budget;
- label sources deterministically as `[S1]`, `[S2]`, and so on;
- retain the mapping from source label to document location.

#### Local generation

- run Qwen3-4B locally without hosted inference;
- use a CPU-compatible quantized runtime for the target laptop;
- use deterministic grounded-answer behavior initially;
- answer in the question language where the model can do so reliably;
- return an explicit insufficient-evidence result when the context does not support an answer.

#### Citation validation

- reject citation labels that were not provided in the context;
- map every valid citation to a known chunk and document;
- return filename, page/slide/section, excerpt, and ranking metadata;
- distinguish citation presence from actual citation support in tests.

## 7. Runtime profiles

Both profiles use the same ingestion, chunks, embeddings, model, and response contract.

### Fast mode

```text
Question
  ↓
Qwen3-Embedding-0.6B
  ↓
Dense FAISS retrieval
  ↓
Top-K context
  ↓
Qwen3-4B
```

Priorities:

- lower latency;
- lower operational complexity;
- useful default for normal queries;
- no BM25, RRF, or reranker cost.

### Quality mode

```text
Question
  ↓
Qwen3-Embedding-0.6B
  ├── Dense FAISS
  └── BM25
        ↓
       RRF
        ↓
BGE-reranker-v2-m3
        ↓
Top-5 context
        ↓
Qwen3-4B
```

Priorities:

- maximum measured retrieval quality;
- stronger first-rank evidence;
- preservation of complete top-5 evidence;
- higher latency and resource cost.

The reranker must be optional and configurable. Enabling or disabling it must not require changes to ingestion, indexing, routes, or generation.

## 8. Backend integration plan

The current repository already contains FastAPI routes and embedding, retrieval, and LLM services. Integration begins with a read-only audit of the active code path, then replaces prototype assumptions in small PR-sized steps.

Expected existing areas:

- `backend/main.py`
- `backend/routes/chat.py`
- `backend/routes/documents.py`
- `backend/routes/models.py`
- `backend/services/embedder.py`
- `backend/services/retriever.py`
- `backend/services/llm.py`
- `backend/tests/`
- `backend/pyproject.toml`

### P0 — baseline and design audit — completed

- confirm current endpoint contracts and frontend dependencies;
- identify stale ChromaDB, pgvector, Groq, and local-GGUF assumptions;
- decide the production artifact layout for original files, metadata, FAISS, BM25, and model weights;
- define shared document, block, chunk, retrieval-result, citation, and ingestion-job models;
- make the existing test command runnable;
- record the intended offline startup path.

### P1 — production ingestion and extraction — completed

- [x] create clean extractor boundaries for validated formats;
- [x] implement stable document/chunk metadata;
- [x] add duplicate, replace, delete, and re-index behavior;
- [x] add ingestion status and structured errors;
- [x] add extraction fixtures and targeted tests.

### P2 — embedding and Fast mode — implemented

- [x] integrate the local Qwen3 embedding adapter with local-only loading;
- [x] build persistent FAISS index and metadata mapping;
- [x] implement dense retrieval;
- [x] implement Fast mode end to end;
- [x] add retrieval trace output and tests.

Runtime validation with the actual Qwen weights remains a deployment check and
requires setting `DOCMIND_EMBEDDING_MODEL_PATH` to a cached local model.

### P3 — Quality mode — implemented

- [x] add a persistent BM25 index over the same chunks;
- [x] implement Reciprocal Rank Fusion;
- [x] add the optional BGE reranker;
- [x] implement Quality mode behind the same retrieval interface;
- [x] verify evidence ordering and top-5 coverage behavior.

Runtime reranker profiling remains a P6 deployment check; Quality mode falls
back to RRF ordering when local BGE weights are not configured.

### P4 — local generation and citations — implemented

- [x] implement the local Qwen3-4B GGUF runtime adapter;
- [x] remove hosted inference as a requirement;
- [x] assemble deterministic source-labelled prompts;
- [x] validate model-produced citation labels;
- [x] implement insufficient-evidence behavior;
- [x] return validated citation metadata through a backward-compatible API extension.

P4 uses `llama-cpp-python` with a cached local GGUF file configured through
`DOCMIND_LLM_MODEL_PATH`. Missing weights use a deterministic extractive
fallback for development only; no cloud provider is contacted. A registry-based
Hugging Face setup API now downloads the approved Qwen3 GGUF artifact atomically,
exposes progress, and loads it only after explicit selection. Product settings
such as categories, supported formats, file limits, chunk defaults, and
retrieval top-k values are environment-backed and served to the frontend from
`GET /api/config/`.

### P5 — API and frontend integration

Status: implemented and covered by backend tests plus the Next.js production build.

- keep routes thin and delegate work to services;
- preserve working upload, list, ask, and delete flows;
- add ingestion status to the knowledge-base UI;
- allow Fast/Quality profile selection;
- display filename and page/slide citation cards;
- show indexing, failure, no-evidence, and local-model-loading states;
- use the planned sidebar, chat, knowledge-base, and overview layout without copying the reference designs literally.

P5 also includes the managed knowledge-folder workflow. `DOCMIND_SOURCE_DIR`
is scanned explicitly through `POST /api/sources/sync` (and optionally once at
startup), with hash-based add/change detection, deletion reconciliation, a
persistent manifest, and status counts exposed at `GET /api/sources/status`.
This keeps shared offline-folder operation reliable without introducing a
platform-specific file watcher.

### P6 — local deployment profiling

Status: profiling harness implemented in `backend/scripts/profile_local.py`;
first CPU-only measurements are recorded in `docs/p6-local-profiling.md`.
Dense rebuilds now run in persisted batches with restart checkpoints, and
folder synchronization exposes per-file extraction failures for diagnosis.

#### P6.1 — component and warm-query profiling — implemented

- [x] measure local model artifacts and load time;
- [x] measure query embedding, FAISS, BM25, RRF, generation, and end-to-end latency;
- [x] record peak process RSS and distinguish CPU laptop results from Kaggle GPU results;
- [x] persist resumable dense-index checkpoints and bounded profiling output.

#### P6.2 — safe full-corpus profile and optional reranker benchmark — tooling implemented

- [x] require an explicit `--full-corpus` flag for an unbounded rebuild;
- [x] build full-corpus profiling indexes in an isolated run directory;
- [x] report document, chunk, page, status, and extraction-failure counts;
- [x] expose an optional local reranker path and record candidate count and latency;
- [x] run an isolated feasibility pass and record the measured first-batch cost;
- [ ] complete the full-corpus run after indexing throughput is optimized for the target laptop.

The isolated profile cannot replace the active application indexes. This keeps a
long CPU measurement or interrupted rebuild from taking the chatbot offline.

#### P6.3 — background and incremental indexing — implemented

- [x] return uploads after extraction instead of blocking the HTTP request on CPU embedding;
- [x] serialize local index work through a single background worker;
- [x] append vectors for new documents when the active dense index is consistent;
- [x] keep replacement and deletion operations on the safe full-rebuild path;
- [x] expose queue state through runtime status and poll document status in the UI.

Run the integrated application on the target laptop and measure components separately:

- model download and disk size;
- model load time;
- cold-start latency;
- warm-query latency;
- query embedding latency;
- FAISS retrieval latency;
- BM25 latency;
- RRF latency;
- reranker latency;
- generation latency;
- time to first token, if measurable;
- tokens per second;
- peak CPU RAM;
- peak GPU VRAM only when a GPU is used;
- dense and lexical index sizes;
- full end-to-end query latency.

Existing Kaggle GPU timing must not be presented as laptop CPU timing.

The previous reranker measurement must be interpreted correctly: approximately 9–14 seconds covered an entire 46-question finalist configuration, about 1,380 query-passage pairs. It was not 9–14 seconds per individual query.

Local results will determine which profile becomes the default. If the reranker is too slow on CPU, Quality mode may remain an explicit opt-in profile.

### P7 — hardening and portfolio delivery

- run `ruff` formatting/lint checks;
- run backend unit and integration tests with coverage;
- run the Next.js build/type-safety check;
- validate Docker Compose configuration and container builds;
- test a fully offline startup after caches and model files are prepared;
- document model licenses and exact revisions;
- document limitations and unsupported file types;
- add screenshots, architecture diagrams, result tables, and a short demo script;
- publish only measured latency and quality claims.

## 9. Frontend product plan

### Main workspace

- left navigation for Chat, Knowledge Base, Overview, and Settings;
- central chat with local-model and retrieval-profile status;
- question input and grounded response rendering;
- compact citation cards linked to the original document location;
- clear insufficient-evidence responses.

### Knowledge Base

- drag-and-drop upload;
- file name, type, size, status, and indexed date;
- processing, indexed, partially indexed, and failed states;
- retry, delete, replace, and re-index actions;
- supported-format information that matches actual backend behavior.

### Overview

- indexed document and chunk counts;
- recent ingestion activity;
- active embedding and generator revisions;
- active retrieval profile;
- average measured local query latency;
- index health and failed jobs.

Avoid vanity metrics until real telemetry exists.

## 10. Future feature work

These are independent product/research features. They are not blockers for research v1 closure or initial product integration.

### F1 — XLSX and table QA

- add spreadsheet ingestion;
- preserve sheet, row, column, and table metadata;
- compare Markdown tables;
- compare row-wise text with repeated headers;
- compare schema plus row chunks;
- evaluate DuckDB/text-to-SQL only where structured aggregation is genuinely required;
- never make text-to-SQL mandatory for every spreadsheet question.

### F2 — OCR and scanned documents

- add OCR as a separate extraction capability;
- detect pages with insufficient embedded text;
- keep OCR evaluation separate from retrieval evaluation;
- test image-only PDFs;
- test low-resolution and rotated scans;
- test French and Arabic scans;
- test scanned tables;
- expose partial/failed OCR status instead of silently indexing empty content.

### F3 — harder and larger gold benchmark

- add answerable and no-answer questions;
- add multi-evidence and multi-document questions;
- add near-duplicate passages and harder distractors;
- add lexical mismatch and paraphrased questions;
- add spelling mistakes;
- use new benchmark cases to validate new features rather than delay product v1.

### F4 — Arabic support

- test Arabic PDF and DOCX extraction;
- test right-to-left reading order;
- test Arabic Unicode normalization variants;
- test Arabic question to Arabic evidence;
- test Arabic question to French evidence;
- test French question to Arabic evidence;
- test mixed-language queries and documents;
- evaluate retrieval and generation separately;
- do not claim full Arabic support before these tests pass.

### F5 — access control and data connectors

- add local accounts or company SSO;
- add document-level and department-level filters;
- add audit logs;
- design read-only SQL/database connectors;
- add backup, restore, retention, and operational policies.

## 11. Acceptance criteria

### Research v1 closure

- the frozen configuration is documented;
- the locked 12-question TEST is run exactly once;
- TEST retrieval and generation metrics are recorded;
- the existing four no-answer questions are run;
- all no-answer outputs are manually inspected;
- weaknesses are documented without retuning;
- the final report distinguishes DEV selection from TEST evidence;
- research v1 is marked complete.

### Product v1

- normal operation requires no internet connection;
- validated PDF, PPTX, and DOCX files can be indexed;
- new documents can be indexed without restarting the application;
- Fast mode works end to end;
- Quality mode works end to end or is explicitly disabled by configuration;
- Qwen3-4B runs locally within the target machine’s resource budget;
- answers contain validated citations mapped to source locations;
- unsupported questions can produce an insufficient-evidence response;
- deletion and replacement keep both indexes consistent;
- backend tests, frontend build, and applicable Docker checks pass;
- local CPU performance and memory results are documented;
- the README states current limitations without claiming XLSX, OCR, Arabic, or database support.

## 12. Documentation and CV output

After product integration, documentation must include:

- offline laptop quickstart;
- architecture diagram for ingestion and query paths;
- research v1 methodology and final frozen configuration;
- DEV and locked TEST result tables;
- no-answer observations;
- Fast versus Quality profile comparison;
- local CPU performance measurements;
- model names, revisions, quantization, and licenses;
- known limitations and future features;
- deployment notes for a local shared server.

Suggested CV statement, to be updated with local profiling numbers:

> Built and evaluated an offline RAG assistant for heterogeneous internal documents, comparing token-aware chunking, multilingual embeddings, BM25/dense hybrid retrieval, reranking, and quantized local LLMs; integrated Fast and Quality retrieval profiles with local generation, validated citations, and measured CPU deployment performance.

Do not claim production Arabic, OCR, or spreadsheet support until the corresponding future features are implemented and validated.

## 13. Immediate next actions

1. Resume the isolated P6.2 full-corpus profile after confirming the background index worker is suitable for daily uploads.
2. Run P7 hardening checks before portfolio claims.
3. Treat XLSX, OCR, Arabic, and benchmark expansion as independent future features.

