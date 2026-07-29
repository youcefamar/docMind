from services.embedder import EmbeddingService, PDFProcessor


def test_pdf_processor_text_cleaning():
    processor = PDFProcessor()
    raw = "  Hello   World \n\n This is   a test.  "
    cleaned = processor._clean_text(raw)
    assert cleaned == "Hello World This is a test."

def test_pdf_processor_chunking():
    processor = PDFProcessor(chunk_size=50, overlap=10)
    text = "Sentence one is here. Sentence two is longer and details policy information."
    chunks = processor._chunk_text(text)
    assert len(chunks) >= 2
    assert all(len(c) <= 50 for c in chunks)

def test_embedding_service_generation():
    service = EmbeddingService()
    texts = ["What is the PTO policy?", "Remote work guidelines"]
    embeddings = service.generate_embeddings(texts)
    assert len(embeddings) == 2
    assert isinstance(embeddings[0], list)
    assert len(embeddings[0]) == 384


def test_embedding_service_has_no_import_time_model_side_effect():
    service = EmbeddingService()

    assert service.model is None


def test_local_model_load_uses_current_embedding_dimension_api(monkeypatch):
    class FakeSentenceTransformer:
        def __init__(self, *_args, **_kwargs):
            pass

        def get_embedding_dimension(self):
            return 1024

    monkeypatch.setattr("services.embedder.SentenceTransformer", FakeSentenceTransformer)
    service = EmbeddingService()

    service.load_local_model("C:/models/Qwen3-Embedding-0.6B")

    assert service.embedding_dimension == 1024
