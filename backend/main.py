import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Load environment variables
load_dotenv()
logging.basicConfig(
    level=os.getenv("DOCMIND_LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

from routes.chat import router as chat_router  # noqa: E402
from routes.config import router as config_router  # noqa: E402
from routes.documents import router as docs_router  # noqa: E402
from routes.models import router as models_router  # noqa: E402
from routes.sources import router as sources_router  # noqa: E402
from routes.status import router as status_router  # noqa: E402

app = FastAPI(
    title="DocMind API",
    description="Offline Internal Knowledge Assistant API with local Qwen generation",
    version="1.0.0"
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, error: Exception):
    """Keep API failures machine-readable while retaining the traceback locally."""
    logging.getLogger("docmind.api").exception(
        "[API] unhandled error method=%s path=%s",
        request.method,
        request.url.path,
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error. Check the backend terminal logs.",
            "code": "internal_server_error",
        },
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
app.include_router(config_router)
app.include_router(docs_router)
app.include_router(models_router)
app.include_router(status_router)
app.include_router(sources_router)

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
