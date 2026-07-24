# DocMind Setup & Deployment Guide 🚀

This document covers developer onboarding, local environment configuration, Docker container deployment, and production VPS hosting.

---

## 📋 Prerequisites

- **Python**: 3.11 or higher
- **Node.js**: 20.x or higher (npm 10+)
- **Docker & Docker Compose**: (For containerized deployment)
- **Groq API Key**: Obtain a free API key from [console.groq.com](https://console.groq.com)

---

## 💻 Local Environment Setup

### Step 1: Clone Repository & Configuration
```bash
git clone https://github.com/your-org/docmind.git
cd docmind

# Create environment file from template
cp .env.example .env
```
Edit `.env` and insert your `GROQ_API_KEY`:
```env
GROQ_API_KEY=gsk_your_groq_api_key_here
GROQ_MODEL=llama-3.1-8b-instant
NEXTAUTH_SECRET=docmind-super-secret-key-change-me
```

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
