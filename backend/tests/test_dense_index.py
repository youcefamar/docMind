from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pytest
from models.contracts import (
    ChunkRecord,
    DocumentBlock,
    DocumentRecord,
    DocumentStatus,
    RetrievalProfile,
)
from services.dense_index import DenseIndexService
from services.embedder import QwenEmbeddingService
from services.metadata_store import MetadataStore


class KeywordEmbedder:
    embedding_dimension = 3
    model_name = "test-keyword"
    is_ready = True

    def generate_embeddings(self, texts):
        vectors = []
        for text in texts:
            lower = text.lower()
            vectors.append(
                [1.0, 0.0, 0.0]
                if "cat" in lower
                else [0.0, 1.0, 0.0]
                if "dog" in lower
                else [0.0, 0.0, 1.0]
            )
        return vectors


def add_document(store: MetadataStore, document_id: str, filename: str, category: str, text: str):
    now = datetime.now(timezone.utc)
    store.save_document(
        DocumentRecord(
            id=document_id,
            filename=filename,
            sha256=document_id.ljust(64, "0"),
            size_bytes=len(text),
            category=category,
            status=DocumentStatus.INDEXED,
            original_path=str(Path(filename)),
            chunk_count=1,
            total_pages=1,
            created_at=now,
            updated_at=now,
        )
    )
    store.replace_content(
        document_id,
        [
            DocumentBlock(
                id=f"{document_id}:page:1",
                document_id=document_id,
                block_type="page",
                text=text,
                location_type="page",
                location_value="1",
            )
        ],
        [
            ChunkRecord(
                id=f"{document_id}:chunk:1",
                document_id=document_id,
                block_id=f"{document_id}:page:1",
                text=text,
                token_count=2,
                chunk_index=0,
                location_type="page",
                location_value="1",
            )
        ],
    )


def test_dense_index_retrieves_and_persists_chunk_mapping(tmp_path: Path):
    store = MetadataStore(tmp_path / "metadata.sqlite")
    add_document(store, "doc-cat", "cats.md", "Animals", "Cats are quiet.")
    add_document(store, "doc-dog", "dogs.md", "Animals", "Dogs are loyal.")
    service = DenseIndexService(tmp_path / "indexes", KeywordEmbedder(), store)

    assert service.rebuild_from_store() == 2
    results = service.search("Tell me about cats", top_k=1)
    restored = DenseIndexService(tmp_path / "indexes", KeywordEmbedder(), store)

    assert results[0].document_id == "doc-cat"
    assert results[0].retrieval_profile is RetrievalProfile.FAST
    query_vector = service.embedder.generate_embeddings(["Tell me about cats"])[0]
    assert service.search_vector(query_vector, top_k=1)[0].document_id == "doc-cat"
    assert restored.search("Tell me about dogs", top_k=1)[0].document_id == "doc-dog"


def test_dense_index_applies_category_filter(tmp_path: Path):
    store = MetadataStore(tmp_path / "metadata.sqlite")
    add_document(store, "doc-cat", "cats.md", "Animals", "Cats are quiet.")
    add_document(store, "doc-other", "other.md", "Other", "Cats appear in this unrelated note.")
    service = DenseIndexService(tmp_path / "indexes", KeywordEmbedder(), store)
    service.rebuild_from_store()

    results = service.search("cats", category="Animals", top_k=5)

    assert [result.document_id for result in results] == ["doc-cat"]


def test_dense_index_appends_new_document_without_rebuilding_existing_vectors(tmp_path: Path):
    store = MetadataStore(tmp_path / "metadata.sqlite")
    add_document(store, "doc-cat", "cats.md", "Animals", "Cats are quiet.")
    service = DenseIndexService(tmp_path / "indexes", KeywordEmbedder(), store)
    assert service.rebuild_from_store() == 1

    add_document(store, "doc-dog", "dogs.md", "Animals", "Dogs are loyal.")

    assert service.upsert_document("doc-dog") == 2
    assert service.search("dogs", top_k=1)[0].document_id == "doc-dog"


def test_dense_index_batched_rebuild_resumes_from_checkpoint(tmp_path: Path):
    store = MetadataStore(tmp_path / "metadata.sqlite")
    add_document(store, "doc-cat", "cats.md", "Animals", "Cats are quiet.")
    add_document(store, "doc-dog", "dogs.md", "Animals", "Dogs are loyal.")
    service = DenseIndexService(tmp_path / "indexes", KeywordEmbedder(), store)
    checkpoint = tmp_path / "indexes" / "rebuild.checkpoint.json"

    def stop_after_first_batch(completed, _total, _elapsed, _resumed):
        if completed == 1:
            raise RuntimeError("stop for resume test")

    with pytest.raises(RuntimeError, match="stop for resume test"):
        service.rebuild_batched(
            store.list_chunks(),
            batch_size=1,
            checkpoint_path=checkpoint,
            progress_callback=stop_after_first_batch,
        )

    assert checkpoint.is_file()
    resumed = DenseIndexService(tmp_path / "indexes", KeywordEmbedder(), store)
    assert resumed.rebuild_batched(
        store.list_chunks(), batch_size=1, checkpoint_path=checkpoint
    ) == 2
    assert not checkpoint.exists()
    assert resumed.search("dogs", top_k=1)[0].document_id == "doc-dog"


def test_qwen_adapter_normalizes_model_embeddings():
    class FakeModel:
        def encode(self, texts, **kwargs):
            assert kwargs["normalize_embeddings"] is True
            return np.asarray([[3.0, 4.0] for _ in texts])

    service = QwenEmbeddingService(model=FakeModel(), embedding_dimension=2)

    vector = service.generate_embeddings(["query"])[0]

    assert np.isclose(np.linalg.norm(vector), 1.0)
