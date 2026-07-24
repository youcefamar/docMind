from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from services.embedder import EmbeddingService
from services.retriever import VectorStoreService
from services.llm import LLMService

router = APIRouter(prefix="/api", tags=["Chat"])

class ChatMessage(BaseModel):
    sender: str  # "user" or "bot" / "assistant"
    content: str

class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, example="What is the remote work policy?")
    category: Optional[str] = Field("All", example="HR")
    chat_history: Optional[List[Dict[str, str]]] = Field(default=[], description="Multi-turn conversation history")

class SourceResponse(BaseModel):
    doc_id: str
    filename: str
    category: str
    page_number: int
    total_pages: int
    excerpt: str
    similarity: float

class AskResponse(BaseModel):
    answer: str
    confidence_score: float
    confidence_label: str
    sources: List[SourceResponse]

# Dependency singletons
embedder_service = EmbeddingService()
retriever_service = VectorStoreService()
llm_service = LLMService()

@router.post("/ask", response_model=AskResponse)
async def ask_question(request: AskRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        # 1. Embed query text
        query_embeddings = embedder_service.generate_embeddings([request.question])
        
        # 2. Retrieve top matching chunks from ChromaDB
        sources = retriever_service.search(
            query_embedding=query_embeddings,
            category=request.category,
            top_k=4
        )

        # 3. Generate answer via Groq LLM
        answer, confidence_score, confidence_label = llm_service.generate_answer(
            question=request.question,
            sources=sources,
            chat_history=request.chat_history
        )

        return AskResponse(
            answer=answer,
            confidence_score=confidence_score,
            confidence_label=confidence_label,
            sources=[SourceResponse(**src) for src in sources]
        )

    except Exception as e:
        print(f"[API Chat Error] {e}")
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")
