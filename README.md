# DocMind — Internal Knowledge Assistant 🧠📄

> **Problem**: Employees waste hours searching through bulky PDFs.  
> **Solution**: DocMind allows employees to ask questions in plain natural language and receive instant, grounded answers accompanied by exact source document citations and page numbers.

---

## 🚀 Tech Stack

| Layer | Tool | Rationale |
|---|---|---|
| **Frontend** | Next.js 15 (App Router) + Tailwind CSS + NextAuth.js | Modern, responsive, enterprise-ready UI with custom design tokens & authentication |
| **Backend** | FastAPI (Python 3.11) | High-performance async API framework for chunking, embedding & retrieval |
| **LLM Inference** | Groq (`llama-3.1-8b-instant`) | Ultra-fast, zero-latency open LLM inference |
| **Embeddings** | `sentence-transformers` (`all-MiniLM-L6-v2`) | Local, free, high-speed dense vector representations |
| **Vector DB** | ChromaDB / pgvector | Persistent local or PostgreSQL vector storage |
| **PDF Parsing** | `pypdf` | Lightweight page-by-page text extraction |
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
│   │   ├── embedder.py       # pypdf parsing & chunking
│   │   ├── retriever.py      # ChromaDB query & similarity search
│   │   └── llm.py            # Groq Llama 3.1 8B prompt engineering & confidence
│   ├── db/chroma/            # Persistent Chroma Vector Store
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
  - Query ChromaDB -> Retrieve top matching chunks -> Synthesize answer with Groq LLM -> Citation extraction.
  - Notebook available in `notebooks/rag_pipeline_demo.ipynb`.

- [x] **Week 2 — FastAPI Backend Services**
  - `POST /api/upload`: Upload single/multiple PDFs, extract text, chunk, embed, & save to ChromaDB under category metadata.
  - `POST /api/ask`: Takes question + chat history + category filter, retrieves sources, calls Groq LLM, assesses confidence.
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
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Provide your Groq API key:
```env
GROQ_API_KEY=gsk_your_actual_groq_api_key
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

### 2. Upload Document
`POST /api/upload` (Form Data)
- `files`: File list (`.pdf`)
- `category`: String (`HR`, `Tech`, `Finance`, `Legal`, `Operations`, `General`)

### 3. List Catalog
`GET /api/docs`

### 4. Delete Document
`DELETE /api/doc/{doc_id}`
