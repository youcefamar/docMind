# DocMind Setup & Deployment Guide 🚀

This document covers developer onboarding, local environment configuration, Docker container deployment, and production VPS hosting.

---

## 📋 Prerequisites

- **Python**: 3.11 or higher
- **Node.js**: 20.x or higher (npm 10+)
- **Docker & Docker Compose**: (For containerized deployment)
- **Local model weights**: cache a Qwen3-4B GGUF file locally before starting the offline server.

---

## 💻 Local Environment Setup

### Step 1: Clone Repository & Configuration
```bash
git clone https://github.com/your-org/docmind.git
cd docmind

# Create environment file from template
cp .env.example .env
```
Edit `.env` with local model paths (no API key is required):
```env
DOCMIND_LLM_MODEL_PATH=./backend/models/qwen3-4b-instruct-q4_k_m.gguf
DOCMIND_EMBEDDING_MODEL_PATH=C:/models/Qwen3-Embedding-0.6B
DOCMIND_RERANKER_MODEL_PATH=C:/models/bge-reranker-v2-m3
NEXTAUTH_SECRET=docmind-super-secret-key-change-me
```

Alternatively, after starting the backend once, use the interactive Swagger
page at `http://127.0.0.1:8000/docs`: call `GET /api/models/`, then
`POST /api/models/download` with `{"model_id":"qwen3-4b-q4"}`. Poll the model
status endpoint and call `/api/models/select` when the download completes.

For `POST /api/ask` in Postman, choose **Body → raw → JSON** and ensure the
header is `Content-Type: application/json`. Do not send the JSON as form-data or
as a quoted text string; FastAPI will otherwise return `422 model_attributes_type`.

---

### Step 2: Backend Setup (FastAPI)

1. Navigate to the `backend/` directory:
   ```bash
   cd backend
   ```
2. Create and activate a Python virtual environment:
   ```bash
   # Windows (PowerShell)
   python -m venv venv
   .\venv\Scripts\Activate.ps1

   # Linux / macOS
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Launch the FastAPI server:
   ```bash
   uvicorn main:app --reload --port 8000
   ```
   Verify backend status by visiting `http://localhost:8000/docs` in your browser.

---

### Step 3: Frontend Setup (Next.js 15)

1. Open a new terminal tab and navigate to `frontend/`:
   ```bash
   cd frontend
   ```
2. Install npm packages:
   ```bash
   npm install
   ```
3. Run dev server:
   ```bash
   npm run dev
   ```
4. Access the web interface at `http://localhost:3000`.

---

## 🐳 Docker Deployment (Production / VPS)

To launch both frontend and backend as containerized services with persistent storage:

```bash
# Ensure .env file exists in root directory
docker-compose up --build -d
```

### Useful Docker Commands:
- **View Logs**:
  ```bash
  docker-compose logs -f
  ```
- **Stop Containers**:
  ```bash
  docker-compose down
  ```
- **Rebuild Containers**:
  ```bash
  docker-compose up --build -d --force-recreate
  ```

---

## 📓 Week 1 RAG Notebook Prototype

To run and inspect the line-by-line RAG pipeline in Jupyter:
```bash
cd notebooks
jupyter notebook rag_pipeline_demo.ipynb
```
