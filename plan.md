# DocMind: Offline Multilingual RAG Research and Implementation Plan

## 1. Project decision

DocMind will be developed as a CV-quality personal project for a small company that wants to search internal documents without sending data to the internet or to a hosted LLM.

The project has two deliberately separate tracks:

1. **Research track:** build a reproducible Kaggle benchmark to compare ingestion strategies, multilingual embeddings, rerankers, and small open-weight local LLMs on messy documents.
2. **Product track:** integrate the best validated combination into this repository as an offline document-ingestion and question-answering platform.

The benchmark winner must satisfy both quality and laptop constraints. A model that scores well but cannot run acceptably on the target machine is not a winner.

## 2. Scope and constraints

### Target machine

- CPU: Intel i7 11th generation, 4 cores
- Memory: 20 GB RAM
- GPU: none
- LLM model budget: approximately 6 GB maximum on disk/RAM
- Inference: local CPU inference
- Internet: unavailable during normal operation
- Model and package downloads: performed before deployment, then transferred/cached locally

### Languages

- English
- French
- Arabic
- Mixed-language and code-switched questions should be treated as an evaluation target, not assumed to work automatically.

### Initial product scope

- Upload and index text-oriented company files:
  - PDF
  - DOCX
  - PPTX
  - XLSX
  - TXT
  - Markdown
- Ask questions over the indexed knowledge base.
- Return an answer with source filename, location metadata, excerpt, and a citation.
- Support adding new files and replacing/re-indexing files.
- Run entirely on a local computer or a shared local server.
- Initially assume that anyone who can access the trusted machine may use the chatbot.
- Defer department-level permissions and direct relational-database querying until the document chatbot is reliable.

### Important terminology correction

The first version should not describe a shared folder as “the database.” The local server should provide four separate responsibilities:

- an original-file store;
- an extracted/normalized document store;
- a vector and lexical search index;
- the API and local web application.

Later, a read-only database connector can be added as a separate source type. Allowing an LLM to write arbitrary SQL or access business tables is a security project of its own and is not required to prove the document RAG idea.

## 3. Success criteria

The final CV version should demonstrate measurable engineering decisions, not only a chat screen.

### Retrieval quality

- Recall@k and MRR/nDCG for English, French, Arabic, and mixed-language queries.
- Retrieval performance with and without lexical search.
- Retrieval performance with and without reranking.
- Table-aware and page-aware evidence retrieval.

### Answer quality

- Citation correctness: cited chunks actually support the answer.
- Citation completeness: important claims have supporting citations.
- Groundedness/hallucination rate.
- Correct “I do not know” behavior when evidence is absent.
- Cross-language answer quality and language preservation.

### System quality

- Indexing success rate by file type.
- OCR success rate on scanned pages.
- Query p50/p95 latency on the laptop.
- Peak RAM and model/index disk size.
- Cold-start and warm-start behavior.
- Repeatable offline setup.

The project should record these metrics in versioned JSON/CSV artifacts so the README can state concrete results.

## 4. Research track: Kaggle benchmark

### 4.1 Build the benchmark before choosing the final model

Do not begin by fine-tuning an LLM. First establish a baseline and a test harness:

1. Parse and normalize documents.
2. Create chunks with stable metadata.
3. Retrieve evidence using a simple dense baseline.
4. Generate an answer using a small local model or a deterministic extractive baseline.
5. Score retrieval, citations, answer grounding, latency, and memory.

This prevents a better-looking answer from hiding a broken retriever.

### 4.2 Dataset families

Use public datasets as controlled stress tests, then add a small private-like corpus created from permitted documents.

#### Layout and extraction

- DocLayNet for multi-column pages, headers, footers, tables, figures, and section structure.
- PubLayNet or DocBank as an easier layout baseline.
- FUNSD and SROIE for forms and OCR-noisy scans.
- A small hand-made set of rotated, low-resolution, image-only, and password-protected PDFs.

#### Tables and office documents

- TAT-QA and FinQA for prose plus table reasoning.
- WikiTableQuestions for less-structured tables.
- Hand-created DOCX, PPTX, XLSX, TXT, and Markdown fixtures with repeated headings, merged cells, bullets, and notes.

#### Multilingual retrieval

- MIRACL subsets for English, French, and Arabic passage retrieval.
- NoMIRACL-style robustness tests for retrieval errors and unsupported questions.
- A small mixed-language set where the question language differs from the document language.
- Synthetic code-switching only as an additional stress test, clearly labelled as synthetic.

#### Enterprise-like questions

- Multi-document questions requiring evidence from more than one file.
- Ambiguous questions with several similarly named documents.
- Unanswerable questions.
- Queries containing spelling mistakes, abbreviations, Arabic normalization differences, and French/English mixing.

Each dataset must have a license note and a small downloadable manifest. Kaggle notebooks must not depend on an internet call at evaluation time.

### 4.3 Ingestion variants to compare

Compare strategies using the same benchmark questions:

1. Plain text extraction with fixed-size chunks.
2. Page/section-aware chunks.
3. Structure-aware chunks that retain headings.
4. Parent-child retrieval: small searchable child chunks linked to larger answer context.
5. Table-to-Markdown representation.
6. Table-row-to-natural-language representation.
7. OCR text only.
8. OCR plus layout-aware extraction where feasible.

Every chunk must retain:

- document ID and version;
- source filename;
- file type;
- page, slide, sheet, or table location;
- heading path;
- language;
- chunk index;
- extraction method;
- text hash;
- timestamps and processing status.

### 4.4 Embedding candidates

Evaluate a small, practical candidate set instead of every model on Hugging Face:

- `intfloat/multilingual-e5-small` as a fast CPU baseline.
- `BAAI/bge-m3` as a larger multilingual and hybrid-retrieval candidate.
- One current multilingual E5/GTE-sized alternative selected by the benchmark date.
- Optionally a smaller Arabic-focused model, only if Arabic results justify the added pipeline complexity.

All candidates must be evaluated in the same dimensions:

- language-specific retrieval;
- cross-language retrieval;
- long/chunked document behavior;
- CPU indexing throughput;
- query latency;
- RAM and disk footprint;
- license suitability for a portfolio/company demonstration.

Do not run separate embedding models per language by default. Prefer one shared multilingual embedding space unless experiments show a clear, maintainable gain from a language router.

### 4.5 Reranker candidates

Use reranking only after first-stage retrieval:

- Start with `BAAI/bge-reranker-v2-m3` as a multilingual candidate.
- Compare against one smaller CPU-friendly reranker or no reranker.
- Measure whether the quality gain justifies laptop latency.

The planned production default is hybrid retrieval plus optional reranking, not mandatory reranking for every query.

### 4.6 Local LLM candidates

The final generator must be open-weight, downloaded from Hugging Face before deployment, and runnable locally as a quantized model.

Start with models in the 1.5B–4B class and quantize to GGUF or another CPU-friendly format. Candidate examples include:

- Qwen3 4B instruct, with thinking disabled for normal RAG responses.
- A smaller Qwen instruct model as the speed baseline.
- Gemma 3 4B IT if its license and Arabic/French evaluation are acceptable.
- One multilingual-focused model only if its license permits the intended use; Aya Expanse is a useful research comparison but its non-commercial research license should not be treated as a company-deployment default.

The benchmark must compare:

- grounded answer accuracy;
- Arabic, French, and English response quality;
- citation formatting reliability;
- refusal/unknown behavior;
- tokens per second and time to first token;
- peak RAM;
- prompt/context length behavior.

The generator should be loaded through `llama.cpp`/`llama-cpp-python` or an equivalent offline runtime. Hosted Groq inference must not be required by the finished offline mode.

### 4.7 Research experiment matrix

Every experiment should be represented by a config rather than hard-coded notebook cells:

```yaml
embedding_model: intfloat/multilingual-e5-small
reranker_model: null
chunking_strategy: structure_parent_child
retrieval_mode: dense
llm_model: qwen3-4b-instruct-q4
top_k: 8
rerank_k: 20
language: ar
```

Save for every run:

- git commit or notebook version;
- model names and exact revisions;
- dataset manifest and split;
- chunking parameters;
- metrics;
- latency and memory;
- representative failure examples.

### 4.8 Research gates

Use staged elimination:

1. **Extraction gate:** reject strategies that lose page/sheet/slide content or fail common formats.
2. **Retrieval gate:** keep only candidates that meet a minimum recall target in all three languages.
3. **Grounding gate:** reject generators that frequently invent unsupported answers.
4. **Resource gate:** reject models that exceed the laptop memory/latency budget.
5. **Robustness gate:** test scans, tables, malformed text, unanswerable questions, and mixed languages.

Fine-tuning is optional. Attempt LoRA or contrastive fine-tuning only after the baseline benchmark identifies a repeatable weakness and enough licensed examples exist. The first claim should be “evaluated and optimized RAG pipeline,” not “fine-tuned model,” unless training materially improves held-out results.

## 5. Product architecture after research

### 5.1 Recommended offline deployment

For the first product version, run these services on the same trusted machine:

```text
Browser
  -> Next.js local UI
  -> FastAPI local API
     -> ingestion workers
     -> multilingual embedder
     -> lexical index (BM25)
     -> vector index (pgvector or a local embedded alternative)
     -> local GGUF LLM
     -> local file/object store
```

The current repository already has FastAPI, Next.js, and PostgreSQL/pgvector concepts. The implementation should reconcile the current ChromaDB wording with the actual pgvector path instead of maintaining two competing designs.

For a small shared server, PostgreSQL with pgvector is a reasonable default because it supports durable metadata, filtering, backups, and future multi-user access. For a single-laptop demo, an embedded index can be retained as a development option if it makes setup materially simpler. The API should hide this choice behind a vector-store interface.

### 5.2 Ingestion pipeline

1. Validate file signature, extension, size, and duplicate hash.
2. Store the original file locally.
3. Detect the format.
4. Extract text and structural metadata.
5. Run OCR only for pages/slides with insufficient extracted text.
6. Normalize Unicode and Arabic text without destroying source text.
7. Detect language per document/section/chunk.
8. Convert tables to a searchable representation while retaining the original table metadata.
9. Create parent and child chunks.
10. Generate embeddings.
11. Build/update dense and BM25 indexes.
12. Mark the document as indexed, failed, or partially indexed with an error report.

Indexing should be asynchronous from the user’s perspective. The UI should show queued, processing, indexed, and failed states.

### 5.3 Query pipeline

1. Validate the question and preserve conversation history limits.
2. Detect query language and normalize only the search copy.
3. Retrieve dense candidates.
4. Retrieve BM25 candidates.
5. Merge and deduplicate candidates.
6. Apply metadata filters such as document/category/language when requested.
7. Rerank the best candidates when enabled.
8. Expand child hits into parent context without exceeding the LLM context budget.
9. Ask the local LLM to answer only from the supplied evidence.
10. Require structured output containing answer, citations, confidence, and an explicit unknown state.
11. Validate that cited chunk IDs exist and belong to the retrieved evidence.
12. Return the answer and source cards to the frontend.

The system must prefer “I could not find enough evidence” over a plausible unsupported answer.

## 6. Backend implementation plan

### Phase A: establish clean boundaries

Expected areas to revise:

- `backend/main.py`
- `backend/routes/chat.py`
- `backend/routes/documents.py`
- `backend/routes/models.py`
- `backend/services/embedder.py`
- `backend/services/retriever.py`
- `backend/services/llm.py`
- `backend/tests/`
- `backend/pyproject.toml`

Add explicit interfaces/models for:

- document records and versions;
- ingestion jobs;
- extracted blocks;
- chunks and citations;
- retrieval results;
- model configuration;
- benchmark/evaluation results.

Keep routes thin. Move parsing, indexing, retrieval, and generation decisions into services that can be tested without HTTP.

### Phase B: replace format-specific assumptions

Create format adapters behind a common extractor interface. Each adapter returns normalized blocks with location metadata. Begin with PDF, DOCX, PPTX, XLSX, TXT, and Markdown. Add OCR as a separate fallback adapter rather than forcing OCR through every document.

Do not silently claim that an uploaded file is indexed if extraction or embedding fails. Store a structured failure reason.

### Phase C: implement retrieval variants

Add:

- dense retrieval;
- BM25 retrieval;
- hybrid fusion;
- optional reranking;
- metadata filtering;
- parent-child context expansion;
- deterministic result tracing for debugging.

The production default should be selected from benchmark evidence and stored in a versioned configuration file, not hidden in route code.

### Phase D: local generation

Replace the hosted-LLM dependency in offline mode with a local model adapter. Keep provider selection behind an interface so experiments can run without changing routes.

The adapter must support:

- model path and checksum;
- quantization/runtime configuration;
- maximum context;
- maximum output tokens;
- temperature/seed;
- streaming later, after correctness is stable;
- structured answer/citation output.

### Phase E: reliability and test coverage

Add tests for:

- every supported extractor;
- Arabic RTL and Unicode normalization;
- multilingual language detection;
- tables and merged cells;
- duplicate/re-index behavior;
- OCR fallback;
- hybrid retrieval ordering;
- citation validation;
- unknown-answer behavior;
- model-loading failures;
- API health and ingestion status.

Use small fixture documents checked into a test-only fixture directory. Do not commit company data or downloaded model weights.

## 7. Frontend plan based on the provided designs

Use the references as a visual direction, not as a literal copy.

### Main workspace

- Left sidebar:
  - workspace/user indicator;
  - Chat;
  - Knowledge Base;
  - Overview;
  - Settings.
- Center chat:
  - assistant status and active model;
  - conversation;
  - compact source/citation cards;
  - question input and language-aware placeholder.
- Knowledge Base panel:
  - drag-and-drop upload;
  - supported-format note;
  - file name, type, size, status, language, indexed date;
  - retry/delete/re-index actions.

### Overview page

Show measurable system information:

- total indexed documents;
- chunks and source types;
- recent ingestion activity;
- average query latency;
- model and embedding revision;
- index health;
- failed jobs requiring attention.

Avoid vanity metrics until real telemetry exists.

### Interaction requirements

- Never imply that a file is searchable before indexing succeeds.
- Make citations clickable to the source location when local preview is available.
- Show “evidence found” and “not enough evidence” states clearly.
- Preserve the clean light UI direction from the reference images, with restrained accent colors and high readability.
- Keep the chat usable on a laptop screen before adding complex responsive behavior.

## 8. Security and offline operation

Phase one can assume trusted-machine access, but it must still avoid unsafe defaults:

- no hosted LLM calls in offline mode;
- no hard-coded production secrets;
- configurable bind address;
- configurable model directory;
- file size and count limits;
- path traversal protection;
- allowed MIME/signature validation;
- safe deletion and re-indexing;
- logs that never print document contents or secrets.

Phase two may add:

- local user accounts or company SSO;
- role/department metadata;
- document-level access filters;
- audit logs;
- read-only database connectors;
- backup/restore and retention policies.

## 9. Documentation and CV deliverables

Update documentation after implementation, not before the architecture is proven:

- README quickstart for offline laptop mode;
- architecture diagram with ingestion and query paths;
- benchmark methodology and dataset licenses;
- experiment table with final metrics;
- model-card and license notes;
- limitations and failure cases;
- deployment/runbook for a shared local server;
- short CV project description with quantified results.

Suggested final CV statement:

> Built and evaluated an offline multilingual RAG assistant for messy enterprise documents, comparing structure-aware extraction, hybrid retrieval, multilingual embeddings, reranking, and quantized local LLMs across English, French, and Arabic; added citations, OCR fallback, local indexing, and measurable quality/latency benchmarks.

Replace this with actual measured numbers only after the benchmark is complete.

## 10. Milestones

### Milestone 0 — baseline and repository cleanup

- Confirm current routes and frontend proxy behavior.
- Make the test command runnable.
- Remove stale ChromaDB/Groq-only assumptions from documentation and configuration.
- Define model/config/artifact directories and ignore downloaded weights.

### Milestone 1 — benchmark harness

- Create dataset manifests and fixture corpus.
- Implement common extraction/chunking output.
- Implement baseline dense retrieval and metric reporting.
- Produce the first Kaggle result artifact.

### Milestone 2 — messy document ingestion

- Add office formats, tables, OCR fallback, Arabic normalization, and status tracking.
- Measure extraction loss and indexing throughput.

### Milestone 3 — retrieval experiments

- Compare embedding candidates.
- Add BM25 and hybrid retrieval.
- Evaluate optional reranking.
- Select a provisional retrieval stack.

### Milestone 4 — local LLM experiments

- Compare quantized candidates within the 6 GB constraint.
- Measure groundedness, citation correctness, multilingual behavior, and CPU latency.
- Select a provisional generator.

### Milestone 5 — product integration

- Implement the selected adapters and configuration.
- Add ingestion job status and traceable citations.
- Remove the required dependency on hosted inference.

### Milestone 6 — frontend and portfolio polish

- Implement the sidebar/chat/knowledge-base/overview layout.
- Add empty, loading, processing, failure, and no-evidence states.
- Add screenshots, architecture diagram, benchmark tables, and a concise demo script.

### Milestone 7 — hardening

- Run backend lint/tests/coverage.
- Run frontend build/type checks.
- Run Docker Compose configuration and build checks.
- Test fully offline after model/package caches are prepared.

## 11. Acceptance criteria before calling the project complete

- The complete query path works without internet access.
- At least PDF, DOCX, PPTX, XLSX, TXT, and Markdown are indexed or explicitly reported unsupported with a clear reason.
- Scanned PDFs have an OCR path and a visible processing result.
- English, French, and Arabic benchmark results are reported separately.
- The selected embedding and LLM fit the laptop resource budget.
- Answers include validated source citations.
- Unsupported questions produce an explicit insufficient-evidence response.
- New uploads do not require restarting the application.
- Tests and frontend build pass using documented commands.
- The README explains the measured limitations instead of claiming perfect accuracy.

## 12. Decisions made for the next step

- Work will continue on `feature/local-rag-research-platform`.
- The next repository change is limited to this `plan.md`.
- No application code, secrets, downloaded model weights, or company data will be changed or committed as part of this planning step.
- Research will begin with text and common office documents, then add OCR and layout complexity in controlled stages.
- The primary goal is a defensible, measurable offline RAG system for a CV portfolio; direct database querying and fine-tuning are optional follow-up work.

