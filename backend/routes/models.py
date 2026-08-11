"""Local Hugging Face model registry and download lifecycle endpoints."""

from __future__ import annotations

import hashlib
import json
import shutil
import urllib.request
from pathlib import Path
from threading import Lock
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

try:
    from huggingface_hub import hf_hub_download

    HAS_HUGGINGFACE_HUB = True
except ImportError:  # pragma: no cover - dependency is optional at import time
    hf_hub_download = None
    HAS_HUGGINGFACE_HUB = False


router = APIRouter(prefix="/api/models", tags=["Models"])
MODELS_DIR = Path(__file__).resolve().parents[1] / "models"
DOWNLOADS_DIR = MODELS_DIR / ".downloads"
CONFIG_PATH = MODELS_DIR / "models_config.json"
download_progress: dict[str, dict[str, Any]] = {}
download_lock = Lock()


class DownloadRequest(BaseModel):
    model_id: str


class SelectModelRequest(BaseModel):
    model_id: str


def _load_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        raise HTTPException(status_code=500, detail="models_config.json configuration file missing.")
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise HTTPException(status_code=500, detail="Invalid models_config.json.") from error


def _save_config(config_data: dict[str, Any]) -> None:
    temporary_path = CONFIG_PATH.with_suffix(".json.tmp")
    temporary_path.write_text(json.dumps(config_data, indent=2), encoding="utf-8")
    temporary_path.replace(CONFIG_PATH)


def _find_model(config: dict[str, Any], model_id: str) -> dict[str, Any]:
    model = next((item for item in config.get("models", []) if item.get("id") == model_id), None)
    if not model:
        raise HTTPException(status_code=404, detail=f"Model ID '{model_id}' not found.")
    return model


def _target_path(model: dict[str, Any]) -> Path:
    filename = Path(str(model.get("filename", ""))).name
    if not filename or filename != str(model.get("filename")) or not filename.lower().endswith(".gguf"):
        raise HTTPException(status_code=500, detail="Model registry contains an unsafe filename.")
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    return MODELS_DIR / filename


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file_handle:
        for block in iter(lambda: file_handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _set_progress(model_id: str, status: str, **extra: Any) -> None:
    with download_lock:
        download_progress[model_id] = {"status": status, **extra}


def _download_task(model: dict[str, Any]) -> None:
    model_id = str(model["id"])
    target_path = _target_path(model)
    temporary_path = target_path.with_suffix(target_path.suffix + ".part")
    _set_progress(model_id, "downloading", filename=target_path.name)
    try:
        if target_path.exists():
            _set_progress(model_id, "completed", filename=target_path.name)
            return

        repo_id = model.get("repo_id")
        source_filename = str(model.get("source_filename") or model["filename"])
        revision = model.get("revision", "main")
        if repo_id and HAS_HUGGINGFACE_HUB:
            DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
            cached_path = Path(
                hf_hub_download(
                    repo_id=str(repo_id),
                    filename=source_filename,
                    revision=str(revision),
                    local_dir=str(DOWNLOADS_DIR / model_id),
                )
            )
            shutil.move(str(cached_path), str(temporary_path))
        else:
            url = model.get("url")
            if not url:
                raise RuntimeError("Model has no Hugging Face repo_id or download URL.")
            urllib.request.urlretrieve(str(url), str(temporary_path))

        expected_sha256 = model.get("sha256")
        if expected_sha256 and _sha256(temporary_path).lower() != str(expected_sha256).lower():
            raise RuntimeError("SHA-256 checksum does not match the model registry.")
        temporary_path.replace(target_path)
        _set_progress(
            model_id,
            "completed",
            filename=target_path.name,
            size_bytes=target_path.stat().st_size,
            sha256=_sha256(target_path),
        )
    except Exception as error:  # background task errors must be visible to the UI
        temporary_path.unlink(missing_ok=True)
        _set_progress(model_id, "failed", error=str(error))


def _model_status(model: dict[str, Any], active_id: str | None) -> dict[str, Any]:
    target_path = _target_path(model)
    downloaded = target_path.is_file()
    progress = download_progress.get(model["id"], {})
    status = progress.get("status", "completed" if downloaded else "not_downloaded")
    result = {
        "id": model["id"],
        "name": model.get("name", model["id"]),
        "filename": target_path.name,
        "repo_id": model.get("repo_id"),
        "revision": model.get("revision", "main"),
        "url": model.get("url"),
        "size_mb": model.get("size_mb", 0),
        "actual_size_mb": round(target_path.stat().st_size / (1024 * 1024), 1)
        if downloaded
        else 0,
        "recommended": model.get("recommended", False),
        "description": model.get("description", ""),
        "downloaded": downloaded,
        "is_active": model["id"] == active_id,
        "download_status": status,
    }
    result.update({key: value for key, value in progress.items() if key != "status"})
    return result


@router.get("/")
async def get_models_config() -> dict[str, Any]:
    config = _load_config()
    active_id = config.get("active_model_id")
    return {
        "active_model_id": active_id,
        "models_dir": str(MODELS_DIR.resolve()),
        "models": [_model_status(model, active_id) for model in config.get("models", [])],
    }


@router.get("/{model_id}")
async def get_model_status(model_id: str) -> dict[str, Any]:
    config = _load_config()
    return _model_status(_find_model(config, model_id), config.get("active_model_id"))


@router.post("/download")
async def download_model(request: DownloadRequest, background_tasks: BackgroundTasks) -> dict[str, Any]:
    config = _load_config()
    target_model = _find_model(config, request.model_id)
    target_path = _target_path(target_model)
    current = download_progress.get(request.model_id, {})
    if target_path.exists():
        _set_progress(request.model_id, "completed", filename=target_path.name)
        return {"model_id": request.model_id, "status": "completed", "message": "Model is already downloaded."}
    if current.get("status") == "downloading":
        return {"model_id": request.model_id, **current, "message": "Download is already running."}
    background_tasks.add_task(_download_task, target_model)
    _set_progress(request.model_id, "queued", filename=target_path.name)
    return {
        "model_id": request.model_id,
        "status": "queued",
        "message": "Download queued. Poll GET /api/models/{model_id} for status.",
    }


@router.post("/select")
async def select_active_model(request: SelectModelRequest) -> dict[str, Any]:
    config = _load_config()
    target_model = _find_model(config, request.model_id)
    file_path = _target_path(target_model)
    if not file_path.exists():
        raise HTTPException(status_code=400, detail="Download the model before selecting it.")
    config["active_model_id"] = request.model_id
    _save_config(config)

    from services.runtime import llm_service

    llm_service.model_path = str(file_path)
    llm_service._init_local_model()
    return {
        "message": f"Selected local model '{target_model.get('name', request.model_id)}'.",
        "active_model_id": request.model_id,
        "filename": file_path.name,
        "model_ready": llm_service.model_ready,
    }
