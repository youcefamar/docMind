# DocMind — Internal Knowledge Assistant 🧠📄

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
| **Frontend** | Next.js 15 (App Router) + Tailwind CSS + NextAuth.js | Modern, responsive, enterprise-ready UI with custom design tokens & authentication |
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
├── frontend/                  # Next.js 15 App Router Frontend
│   ├── app/
│   │   ├── page.tsx          # Interactive Chat Interface
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

## 🗓️ 4-Week Execution Plan

- [x] **Week 1 — Core RAG Pipeline (Notebook Prototype)**
  - PDF loading via `pypdf` -> Chunking -> Vector embedding via `sentence-transformers` -> Indexing in the local retrieval store.
  - Query the local FAISS/BM25 indexes -> Retrieve top matching chunks -> Synthesize answer with the configured local LLM -> Citation extraction.
  - Notebook available in `notebooks/rag_pipeline_demo.ipynb`.

- [x] **Week 2 — FastAPI Backend Services**
  - `POST /api/upload`: Validate and store PDF, DOCX, PPTX, XLSX, XLS, TXT, and MD files locally, extract chunks, and persist metadata.
  - `POST /api/ask`: Takes question + chat history + category filter, retrieves sources, calls the local generation service, and assesses confidence.
  - `GET /api/docs`: Catalogs uploaded documents with page and chunk metrics.
  - `DELETE /api/doc/{id}`: Removes document vectors cleanly from vector store.

- [x] **Week 3 — Next.js 15 Frontend & Design System**
  - Dark mode glassmorphism theme, glowing indigo highlights, Inter font typography.
  - Interactive multi-turn chat window with category filter pills, clear session action, and instant suggested prompts.
  - Source Cards showing document name, page number, match score percentage, and excerpt quotes.
  - Admin page for PDF drag-and-drop uploads, category assignment, document search, and removal.

- [x] **Week 4 — NextAuth Integration & Docker Deployment**
  - Protected API routes and authentication using NextAuth.js.
  - Containerized production builds with `docker-compose.yml`.

---

## ⚡ Quickstart Guide

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

#### Start Frontend (Next.js 15):
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:3000` in your browser.

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

Set `DOCMIND_LLM_MODEL_PATH` to a cached Qwen3-4B instruct GGUF file. No hosted
LLM or API key is required. Without weights, development uses a deterministic
extractive fallback; do not use that fallback for measured quality claims.

The backend logs each question's retrieval profile, source count, citation
count, model backend, and stage latency in the terminal. Set
`DOCMIND_LOG_QUERIES=true` only when you also want the question text printed.

### 2. Upload Document
`POST /api/upload` (Form Data)
- `files`: File list (`.pdf`, `.docx`, `.pptx`, `.xlsx`, `.xls`, `.txt`, `.md`)
- `category`: A category returned by `GET /api/config/` (or `All` for chat)

The response includes `status`. When the local embedding model is ready, upload
returns after extraction with `processing` while a background worker embeds and
updates FAISS/BM25; the Knowledge Base status changes to `indexed` when complete.
Replacements and deletions use a safe full-corpus rebuild in the same worker.

The backend terminal prints upload diagnostics for each file. Look for
`[UPLOAD] extraction complete`, `[UPLOAD] embedding/indexing start`,
`[EMBED] complete`, and `[INDEX] ... complete` to see where time is spent. If a
request fails before FastAPI can produce a normal response, the API returns a
JSON error telling you to check those terminal logs; the frontend also accepts
plain-text proxy errors instead of attempting to parse them as JSON.

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
`removed`, and `failed`) plus per-file failure diagnostics. Files are copied into the local data store and tracked
by a hash manifest. A first-level folder matching a configured category (for
example `knowledge/HR/handbook.pdf`) is assigned that category; other files use
`DOCMIND_DEFAULT_CATEGORY`.

### 9. Local profiling

Run `backend/scripts/profile_local.py` to measure local model loading, query
embedding, FAISS/BM25/RRF retrieval, optional reranking, generation, end-to-end
latency, artifact sizes, and peak CPU memory. The methodology and the first
CPU-only measurements are recorded in [docs/p6-local-profiling.md](docs/p6-local-profiling.md).
For a safe full-corpus run, use `--full-corpus --isolated-indexes
--rebuild-indexes`; the profile writes temporary FAISS/BM25 artifacts under
`data/profiling/runs/` and leaves the active indexes unchanged. Add
`--reranker-path` only when the BGE reranker is available locally.
