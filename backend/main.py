import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from routes.chat import router as chat_router
from routes.documents import router as docs_router
from routes.models import router as models_router

app = FastAPI(
    title="DocMind API",
    description="Internal Knowledge Assistant API powered by FastAPI, pgvector & Local GGUF LLMs",
    version="1.0.0"
)

# CORS setup for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(chat_router)
app.include_router(docs_router)
app.include_router(models_router)

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
