"""Environment-backed product and runtime configuration.

Business-changing values belong here rather than in routes or frontend
components. Defaults keep a fresh checkout runnable, while every value can be
changed through the local `.env` file without editing Python or TypeScript.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _csv(value: str, fallback: tuple[str, ...]) -> tuple[str, ...]:
    values = tuple(item.strip() for item in value.split(",") if item.strip())
    return values or fallback


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


@dataclass(frozen=True)
class RuntimeSettings:
    data_dir: Path
    source_dir: Path
    sync_on_startup: bool
    categories: tuple[str, ...]
    default_category: str
    supported_extensions: tuple[str, ...]
    max_file_size_mb: int
    chunk_size_chars: int
    chunk_overlap_chars: int
    fast_top_k: int
    quality_final_k: int
    quality_candidate_k: int
    suggested_prompts: tuple[str, ...]

    @classmethod
    def from_environment(cls) -> "RuntimeSettings":
        default_categories = ("General", "HR", "Tech", "Finance", "Legal", "Operations")
        categories = _csv(os.getenv("DOCMIND_CATEGORIES", ",".join(default_categories)), default_categories)
        default_category = os.getenv("DOCMIND_DEFAULT_CATEGORY", categories[0]).strip() or categories[0]
        if default_category not in categories:
            categories = (default_category, *categories)

        extensions = _csv(
            os.getenv("DOCMIND_SUPPORTED_EXTENSIONS", ".pdf,.docx,.pptx,.xlsx,.xls,.txt,.md"),
            (".pdf", ".docx", ".pptx", ".xlsx", ".xls", ".txt", ".md"),
        )
        normalized_extensions = tuple(
            extension if extension.startswith(".") else f".{extension}"
            for extension in extensions
        )
        default_prompts = (
            "What information is available in the indexed documents?",
            "Summarize the most relevant evidence for my question.",
        )
        prompts = tuple(
            prompt.strip()
            for prompt in os.getenv("DOCMIND_SUGGESTED_PROMPTS", "").split("|")
            if prompt.strip()
        ) or default_prompts
        default_data_dir = Path(__file__).resolve().parents[2] / "data"
        return cls(
            data_dir=Path(os.getenv("DOCMIND_DATA_DIR", str(default_data_dir))),
            source_dir=Path(
                os.getenv("DOCMIND_SOURCE_DIR", str(default_data_dir / "knowledge"))
            ),
            sync_on_startup=os.getenv("DOCMIND_SYNC_ON_STARTUP", "false").lower()
            in {"1", "true", "yes", "on"},
            categories=categories,
            default_category=default_category,
            supported_extensions=normalized_extensions,
            max_file_size_mb=max(1, _int_env("DOCMIND_MAX_FILE_SIZE_MB", 50)),
            chunk_size_chars=max(1, _int_env("DOCMIND_CHUNK_SIZE_CHARS", 600)),
            chunk_overlap_chars=max(0, _int_env("DOCMIND_CHUNK_OVERLAP_CHARS", 100)),
            fast_top_k=max(1, _int_env("DOCMIND_FAST_TOP_K", 5)),
            quality_final_k=max(1, _int_env("DOCMIND_QUALITY_FINAL_K", 5)),
            quality_candidate_k=max(1, _int_env("DOCMIND_QUALITY_CANDIDATE_K", 30)),
            suggested_prompts=prompts,
        )


settings = RuntimeSettings.from_environment()
