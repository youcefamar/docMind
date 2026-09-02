# DocMind — Internal Knowledge Assistant

> **Problem**: Employees waste hours searching through bulky PDFs.  
> **Solution**: DocMind allows employees to ask questions in plain natural language and receive instant, grounded answers accompanied by exact source document citations and page numbers.

> **Current implementation status:** Research v1 and backend milestones P1–P5
> are implemented. The backend ingests local documents, synchronizes a managed
> knowledge folder, retrieves with Fast or Quality profiles, and generates
> locally with grounded citation validation.

---

## 🚀 Tech Stack

| Layer | Tool | Rationale |
|---|---|---|
| **Frontend** | Next.js 16 (App Router) + TypeScript 6 + Tailwind CSS + NextAuth.js | Modern, responsive, enterprise-ready UI with custom design tokens & authentication |
| **Backend** | FastAPI (Python 3.11) | High-performance async API framework for chunking, embedding & retrieval |
| **LLM Inference** | Local Qwen3-4B target | Offline CPU-compatible generation (P4) |
| **Embeddings** | Qwen3-Embedding-0.6B target | Frozen multilingual research winner (P2) |
| **Metadata** | SQLite | Local document, job, block, and chunk persistence (P1) |
| **Retrieval** | FAISS + BM25 target | Dense Fast mode and hybrid Quality mode (P2/P3) |
| **Extraction** | `pypdf`, `python-docx`, `python-pptx`, `openpyxl` | Page, slide, sheet, and text extraction |
| **Infra & DevOps** | Docker + Docker Compose | One-command full-stack container deployment |

---

## 📂 Folder Structure

```
docmind/
├── frontend/                  # Next.js 16 App Router Frontend
│   ├── app/
│   │   ├── page.tsx          # Workspace Overview Dashboard
│   │   ├── chat/page.tsx     # Interactive Chat Interface
│   │   ├── admin/page.tsx    # PDF Upload & Vector Management
│   │   ├── login/page.tsx    # NextAuth Login Screen
│   │   ├── layout.tsx        # App Shell Layout
│   │   ├── globals.css       # Design System & Dark Mode Styling
│   │   └── api/auth/         # NextAuth API Routes
│   ├── components/
│   │   ├── ChatWindow.tsx    # Multi-turn Chat & Category Filter
│   │   ├── SourceCard.tsx    # Verified Citation Cards & Page Quotes
│   │   ├── UploadPanel.tsx   # PDF Drag-and-Drop & Catalog Table
│   │   └── Navbar.tsx        # Top Header Navigation Bar
│   ├── Dockerfile
│   └── package.json
│
├── backend/                   # FastAPI Backend
│   ├── main.py               # Application Entrypoint & CORS
│   ├── routes/
│   │   ├── chat.py           # POST /api/ask Endpoint
│   │   ├── config.py         # GET /api/config/ Product configuration
│   │   ├── documents.py      # POST /upload, GET /docs, DELETE /doc
│   │   └── sources.py        # Managed knowledge-folder sync/status
│   ├── services/
│   │   ├── embedder.py       # Extraction, chunking, and embedding boundary
│   │   ├── ingestion.py      # Validation and document lifecycle
│   │   ├── metadata_store.py # SQLite metadata/jobs/chunks
│   │   ├── dense_index.py    # Persistent FAISS Fast retrieval
│   │   ├── folder_sync.py    # Managed knowledge-folder reconciliation
│   │   ├── indexing_queue.py  # Background CPU indexing worker
│   │   ├── runtime.py        # Shared local runtime services
│   │   ├── retriever.py      # Legacy pgvector adapter (P2 replacement)
│   │   └── llm.py            # Local Qwen GGUF generation + citation validation
│   ├── models/contracts.py   # Shared ingestion/retrieval/citation contracts
│   ├── scripts/profile_local.py # Repeatable CPU profiling harness
│   ├── Dockerfile
│   └── requirements.txt
│
├── notebooks/                 # Week 1 RAG Prototyping
│   └── rag_pipeline_demo.ipynb # Line-by-line RAG prototype
│
├── docker-compose.yml         # One-command full container deployment
└── .env.example               # Environment variables template
```

---

##  Quickstart Guide

### 1. Environment Setup
No cloud API key is required for the P1 ingestion path. Optionally set the local
data and managed knowledge-folder directories:
```bash
DOCMIND_DATA_DIR=../data
DOCMIND_SOURCE_DIR=../data/knowledge
DOCMIND_SYNC_ON_STARTUP=false
```

Drop supported files into `DOCMIND_SOURCE_DIR` (including subfolders). Use the
Knowledge Base screen's **Sync knowledge folder** action, or call the sync API,
to detect new/changed files and remove files deleted from that folder. Set
`DOCMIND_SYNC_ON_STARTUP=true` to queue one scan when the backend starts. The
sync is explicit and hash-based; temporary download suffixes are ignored and a
file that changes while it is being read is retried on the next sync.

### 2. Local Development

#### Start Backend (FastAPI):
```bash
cd backend
python -m venv venv
# On Windows: venv\Scripts\activate | On Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```
FastAPI Swagger documentation will be available at `http://localhost:8000/docs`.

#### Start Frontend (Next.js 16):
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:3000` for the workspace overview. The document chat is
available at `http://localhost:3000/chat`.

The Chat screen saves the current conversation, selected category, and retrieval
profile in versioned browser local storage on that same machine. Moving between
Chat and Knowledge Base—or refreshing the page—restores the conversation
without sending it anywhere. **Clear Chat** removes the previous stored
conversation. Before a question is sent, the frontend limits saved history to
the newest messages and a character budget; the backend applies its own
`DOCMIND_CHAT_HISTORY_MAX_TURNS` and `DOCMIND_CHAT_HISTORY_MAX_CHARACTERS`
limits too. This protects the local GGUF context window even when a long chat
is restored from the browser.

Chat requests use a frontend proxy at `/api/backend/ask`. It returns structured
JSON if FastAPI is unavailable, and the UI retries one temporary `503` response
to tolerate a short backend reload window without showing a raw `Internal
Server Error` page.

---

## 🐳 Docker Deployment (One-Command)

Deploy both Next.js frontend and FastAPI backend with persistent vector storage:
```bash
docker-compose up --build -d
```
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`

---

## 🛠️ API Reference

### 1. Ask Question
`POST /api/ask`
```json
{
  "question": "What is the annual leave policy?",
  "category": "All",
  "chat_history": [
    { "sender": "user", "content": "Hi DocMind" },
    { "sender": "bot", "content": "Hello! How can I assist you today?" }
  ]
}
```

`retrieval_profile` can be `fast` (dense FAISS) or `quality` (dense + BM25 +
RRF and optional local BGE reranking). The response includes `sources` and
validated `citations` such as `[S1]`. If evidence is missing, the local runtime
returns `I don't know based on the provided documents.`

Fast cosine scores and Quality RRF scores use different numeric scales. Keep
their refusal and confidence gates separate through `DOCMIND_MIN_SOURCE_SCORE`,
`DOCMIND_FAST_MEDIUM_SCORE`, `DOCMIND_FAST_HIGH_SCORE`,
`DOCMIND_QUALITY_MIN_SOURCE_SCORE`, `DOCMIND_QUALITY_MEDIUM_SCORE`, and
`DOCMIND_QUALITY_HIGH_SCORE`. The defaults in `.env.example` are calibrated for
the current local profiles; adjust the Quality values if you install a reranker
whose score scale differs. Grouped model citations such as `[S1, S2]` are
normalized into separate validated citations before the response is returned.

Set `DOCMIND_LLM_MODEL_PATH` to a cached Qwen3-4B instruct GGUF file. No hosted
LLM or API key is required. Without weights, development uses a deterministic
extractive fallback; do not use that fallback for measured quality claims.

The backend logs each question's retrieval profile, source count, citation
count, model backend, and stage latency in the terminal. Set
`DOCMIND_LOG_QUERIES=true` only when you also want the question text printed.
Qwen `<think>...</think>` blocks are removed by the backend before a response
is returned to the API or rendered in the frontend.

### 2. Upload Document
`POST /api/upload` (Form Data)
- `files`: File list (`.pdf`, `.docx`, `.pptx`, `.xlsx`, `.xls`, `.txt`, `.md`)
- `category`: A category returned by `GET /api/config/` (or `All` for chat)

The response includes `status`. When the local embedding model is ready, upload
returns after extraction with `processing` while a background worker embeds and
updates FAISS/BM25; the Knowledge Base status changes to `indexed` when complete.
Replacements and deletions use a safe full-corpus rebuild in the same worker.

The backend terminal prints upload diagnostics for each file. Look for
`[UPLOAD] extraction complete ✅`, `[INDEX_QUEUE] 🚀 started`, `[EMBED] complete ✅`,
and `[INDEX_QUEUE] 🎉 all queued indexing work is finished`. That final 🎉 line
means every queued document is ready to search. If a request fails before
FastAPI can produce a normal response, the API returns a JSON error telling you
to check those terminal logs; the frontend also accepts plain-text proxy errors
instead of attempting to parse them as JSON.

### 3. List Catalog
`GET /api/docs`

Document statuses may be `processing` while the local background index worker
embeds a new upload. `GET /api/runtime/status` includes `indexing_queue` with
the active document, pending count, and last worker error.

### 4. Delete Document
`DELETE /api/doc/{doc_id}`

### 5. Re-index Document
`POST /api/doc/{doc_id}/reindex`

### 6. Public runtime configuration

`GET /api/config/` returns the configured categories, supported extensions,
upload limit, and retrieval defaults used by the frontend. Change these values
through `.env`; do not edit frontend arrays or route code.

### 7. Local model management

`GET /api/models/` lists the registered Hugging Face GGUF models and their
download status. Start a download with `POST /api/models/download`:

```json
{"model_id": "qwen3-4b-q4"}
```

Poll `GET /api/models/qwen3-4b-q4` until `download_status` is `completed`, then
select it with `POST /api/models/select`:

```json
{"model_id": "qwen3-4b-q4"}
```

Downloads are stored locally and use a temporary file until complete. The
server must have internet access only during this setup step; inference remains
local and offline afterwards.

### 8. Managed knowledge folder

`POST /api/sources/sync` queues a scan and returns `202`; poll
`GET /api/sources/status` for counts (`discovered`, `indexed`, `unchanged`,
`removed`, `failed`, and `queued`) plus per-file failure diagnostics. The scan
finishes after local extraction; documents can remain `processing` while the
single index worker embeds them. New files are queued for incremental indexing.
If a scan contains a replacement or removal, it queues one safe full-catalog
rebuild for the entire scan, never one rebuild per file. Files are copied into
the local data store and tracked by a source-root-bound hash manifest; a legacy
or different-root manifest is ignored rather than deleting documents. A
first-level folder matching a configured category (for example
`knowledge/HR/handbook.pdf`) is assigned that category; other files use
`DOCMIND_DEFAULT_CATEGORY`.

The terminal prints `📂`, `📄`, `📥`, `✅`, `⏳`, and `❌` messages for the scan,
each source file, queued indexing, and failures. Successful frontend polling
requests (`GET /api/docs`, source status, and runtime status) are intentionally
hidden from the terminal so these progress messages stay readable; their errors
remain visible.

#### Make the managed folder the source of truth

For a one-time migration from an old mixed catalog, stop the backend first and
run a dry run:

```powershell
cd backend
.venv\Scripts\python.exe scripts\retain_knowledge_folder.py
```

The script requires a version-2 `sync_manifest.json`, reports the documents it
would remove, and makes no changes without `--confirm`. Once the dry run is
correct, run it with confirmation:

```powershell
.venv\Scripts\python.exe scripts\retain_knowledge_folder.py --confirm
```

It copies the SQLite catalog, originals, manifest, and index files to a
timestamped `data/backups/knowledge-catalog-migration-*` directory before
removing untracked records. Restart the backend and run one folder sync to
create the clean index from the retained documents.

### 9. Local profiling

Run `backend/scripts/profile_local.py` to measure local model loading, query
embedding, FAISS/BM25/RRF retrieval, optional reranking, generation, end-to-end
latency, artifact sizes, and peak CPU memory. The methodology and the first
CPU-only measurements are recorded in [docs/p6-local-profiling.md](docs/p6-local-profiling.md).
For a safe full-corpus run, use `--full-corpus --isolated-indexes
--rebuild-indexes`; the profile writes temporary FAISS/BM25 artifacts under
`data/profiling/runs/` and leaves the active indexes unchanged. Add
`--reranker-path` only when the BGE reranker is available locally.
