import json
import os
import urllib.request

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/models", tags=["Models"])

MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "models")
CONFIG_PATH = os.path.join(MODELS_DIR, "models_config.json")

# In-memory download progress state tracker
download_progress = {}

class DownloadRequest(BaseModel):
    model_id: str

class SelectModelRequest(BaseModel):
    model_id: str

def _load_config():
    if not os.path.exists(CONFIG_PATH):
        raise HTTPException(status_code=500, detail="models_config.json configuration file missing.")
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def _save_config(config_data):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=2)

@router.get("/")
async def get_models_config():
    """
    Returns the JSON configuration, list of models, download status on disk, and active model.
    """
    config = _load_config()
    active_id = config.get("active_model_id")

    models_info = []
    for m in config.get("models", []):
        file_path = os.path.join(MODELS_DIR, m["filename"])
        downloaded = os.path.exists(file_path)
        actual_size_mb = round(os.path.getsize(file_path) / (1024 * 1024), 1) if downloaded else 0

        models_info.append({
            "id": m["id"],
            "name": m["name"],
            "filename": m["filename"],
            "url": m["url"],
            "size_mb": m["size_mb"],
            "actual_size_mb": actual_size_mb,
            "recommended": m.get("recommended", False),
            "description": m.get("description", ""),
            "downloaded": downloaded,
            "is_active": (m["id"] == active_id),
            "download_status": download_progress.get(m["id"], "idle" if downloaded else "not_downloaded")
        })

    return {
        "active_model_id": active_id,
        "models_dir": os.path.abspath(MODELS_DIR),
        "models": models_info
    }

def _download_task(model_id: str, url: str, target_filename: str):
    target_path = os.path.join(MODELS_DIR, target_filename)
    download_progress[model_id] = "downloading"
    print(f"[Model Downloader] Starting download for '{model_id}' from {url}...")

    try:
        def progress_hook(count, block_size, total_size):
            if total_size > 0:
                percent = int(count * block_size * 100 / total_size)
                download_progress[model_id] = f"downloading_{percent}%"

        urllib.request.urlretrieve(url, target_path, reporthook=progress_hook)
        download_progress[model_id] = "completed"
        print(f"[Model Downloader] Successfully downloaded '{model_id}' to {target_path}")
    except Exception as e:
        download_progress[model_id] = f"failed: {str(e)}"
        print(f"[Model Downloader Error] Failed downloading '{model_id}': {e}")

@router.post("/download")
async def download_model(request: DownloadRequest, background_tasks: BackgroundTasks):
    """
    Triggers asynchronous download of specified GGUF model weights from HuggingFace.
    """
    config = _load_config()
    target_model = next((m for m in config.get("models", []) if m["id"] == request.model_id), None)

    if not target_model:
        raise HTTPException(status_code=404, detail=f"Model ID '{request.model_id}' not found in configuration.")

    file_path = os.path.join(MODELS_DIR, target_model["filename"])
    if os.path.exists(file_path):
        return {"message": f"Model '{target_model['name']}' is already downloaded.", "status": "completed"}

    background_tasks.add_task(_download_task, request.model_id, target_model["url"], target_model["filename"])
    return {
        "message": f"Download initiated for '{target_model['name']}'.",
        "model_id": request.model_id,
        "status": "downloading"
    }

@router.post("/select")
async def select_active_model(request: SelectModelRequest):
    """
    Switches the active model in models_config.json.
    """
    config = _load_config()
    target_model = next((m for m in config.get("models", []) if m["id"] == request.model_id), None)

    if not target_model:
        raise HTTPException(status_code=404, detail=f"Model ID '{request.model_id}' not found in configuration.")

    file_path = os.path.join(MODELS_DIR, target_model["filename"])
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=400,
            detail=f"Model file '{target_model['filename']}' is not downloaded yet. Download it first via POST /api/models/download."
        )

    config["active_model_id"] = request.model_id
    _save_config(config)

    # Trigger re-initialization of LLMService if active
    from routes.chat import llm_service
    llm_service.model_path = file_path
    llm_service._init_local_model()

    return {
        "message": f"Successfully switched active local model to '{target_model['name']}'",
        "active_model_id": request.model_id,
        "filename": target_model["filename"]
    }
