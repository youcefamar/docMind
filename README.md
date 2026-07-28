# DocMind — Internal Knowledge Assistant 🧠📄

> **Problem**: Employees waste hours searching through bulky PDFs.  
> **Solution**: DocMind allows employees to ask questions in plain natural language and receive instant, grounded answers accompanied by exact source document citations and page numbers.

> **Current implementation status:** Research v1 and backend milestones P1–P4
> are implemented. The backend ingests local documents, retrieves with Fast or
> Quality profiles, and generates locally with grounded citation validation.

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
│   │   └── documents.py      # POST /upload, GET /docs, DELETE /doc
│   ├── services/
│   │   ├── embedder.py       # Extraction, chunking, and embedding boundary
│   │   ├── ingestion.py      # Validation and document lifecycle
│   │   ├── metadata_store.py # SQLite metadata/jobs/chunks
│   │   ├── dense_index.py    # Persistent FAISS Fast retrieval
│   │   ├── runtime.py        # Shared local runtime services
│   │   ├── retriever.py      # Legacy pgvector adapter (P2 replacement)
│   │   └── llm.py            # Local Qwen GGUF generation + citation validation
│   ├── models/contracts.py   # Shared ingestion/retrieval/citation contracts
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
  - PDF loading via `pypdf` -> Chunking -> Vector embedding via `sentence-transformers` -> Indexing in ChromaDB.
  - Query ChromaDB -> Retrieve top matching chunks -> Synthesize answer with a prototype LLM -> Citation extraction.
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
data directory:
```bash
DOCMIND_DATA_DIR=../data
```

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
  "category": "HR",
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

### 2. Upload Document
`POST /api/upload` (Form Data)
- `files`: File list (`.pdf`, `.docx`, `.pptx`, `.xlsx`, `.xls`, `.txt`, `.md`)
- `category`: String (`HR`, `Tech`, `Finance`, `Legal`, `Operations`, `General`)

The response includes `status`. New documents are `partially_indexed` until the
P2 FAISS/BM25 indexer is connected.

### 3. List Catalog
`GET /api/docs`

### 4. Delete Document
`DELETE /api/doc/{doc_id}`

### 5. Re-index Document
`POST /api/doc/{doc_id}/reindex`
