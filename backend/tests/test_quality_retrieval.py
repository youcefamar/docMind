from pathlib import Path

from services.bm25_index import BM25IndexService
from services.dense_index import DenseIndexService
from services.metadata_store import MetadataStore
from services.quality_retriever import QualityRetriever, reciprocal_rank_fusion
from services.reranker import LocalReranker
from tests.test_dense_index import KeywordEmbedder, add_document


def test_bm25_retrieves_and_reloads_persisted_lexical_index(tmp_path: Path):
    store = MetadataStore(tmp_path / "metadata.sqlite")
    add_document(store, "doc-cat", "cats.md", "Animals", "Cats are quiet.")
    add_document(store, "doc-dog", "dogs.md", "Animals", "Dogs are loyal.")
    index = BM25IndexService(tmp_path / "indexes", store)

    assert index.rebuild_from_store() == 2
    assert index.search_ids("quiet cats", top_k=1)[0][0] == "doc-cat:chunk:1"

    restored = BM25IndexService(tmp_path / "indexes", store)
    assert restored.search_ids("loyal dogs", top_k=1)[0][0] == "doc-dog:chunk:1"


def test_rrf_prefers_documents_supported_by_both_rankers():
    fused = reciprocal_rank_fusion(
        [
            [("dense-only", 0.99), ("shared", 0.80)],
            [("shared", 4.0), ("lexical-only", 3.0)],
        ],
        rrf_k=60,
        top_k=3,
    )

    assert fused[0][0] == "shared"
    assert [chunk_id for chunk_id, _score in fused] == ["shared", "dense-only", "lexical-only"]


def test_quality_retriever_returns_quality_profile_and_final_k(tmp_path: Path):
    store = MetadataStore(tmp_path / "metadata.sqlite")
    add_document(store, "doc-cat", "cats.md", "Animals", "Cats are quiet.")
    add_document(store, "doc-dog", "dogs.md", "Animals", "Dogs are loyal.")
    dense = DenseIndexService(tmp_path / "dense", KeywordEmbedder(), store)
    bm25 = BM25IndexService(tmp_path / "bm25", store)
    dense.rebuild_from_store()
    bm25.rebuild_from_store()

    results = QualityRetriever(dense, bm25).search("quiet cats", final_k=1)

    assert len(results) == 1
    assert results[0].document_id == "doc-cat"
    assert results[0].retrieval_profile.value == "quality"
    assert results[0].rank == 1


def test_optional_reranker_can_score_local_pairs():
    class FakeReranker:
        def predict(self, pairs, **kwargs):
            return [len(passage) for _question, passage in pairs]

    reranker = LocalReranker(model=FakeReranker())

    scores = reranker.score("question", ["short", "a longer passage"])

    assert scores == [5.0, 16.0]
