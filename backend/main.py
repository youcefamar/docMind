import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from routes.chat import router as chat_router
from routes.documents import router as docs_router

app = FastAPI(
    title="DocMind API",
    description="Internal Knowledge Assistant API powered by FastAPI, ChromaDB & Groq (Llama 3.1 8B)",
    version="1.0.0"
)

# CORS setup for Next.js frontend
allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    os.getenv("FRONTEND_URL", "*")
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permissive for local dev / Docker setup
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(chat_router)
app.include_router(docs_router)

@app.get("/", tags=["Health"])
async def root():
    return {
        "app": "DocMind Backend API",
        "status": "online",
        "version": "1.0.0",
        "docs_url": "/docs"
    }

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
