import io
import uuid
import datetime
from typing import List, Dict, Any, Optional
import pypdf

# Initialize sentence-transformers model lazily or fall back gracefully
try:
    from sentence_transformers import SentenceTransformer
    EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
    _model = SentenceTransformer(EMBEDDING_MODEL_NAME)
except Exception as e:
    print(f"[Embedder] Notice: SentenceTransformer init deferred/fallback mode: {e}")
    _model = None

class PDFProcessor:
    def __init__(self, chunk_size: int = 600, overlap: int = 100):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def extract_chunks_from_pdf(
        self, 
        file_bytes: bytes, 
        filename: str, 
        category: str = "General",
        doc_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Parses a PDF from bytes, extracts text page by page, splits into overlapping chunks,
        and returns a list of formatted chunk dictionaries.
        """
        if not doc_id:
            doc_id = str(uuid.uuid4())
            
        pdf_reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        num_pages = len(pdf_reader.pages)
        chunks = []
        global_chunk_idx = 0

        for page_idx, page in enumerate(pdf_reader.pages):
            page_num = page_idx + 1
            raw_text = page.extract_text() or ""
            cleaned_text = self._clean_text(raw_text)

            if not cleaned_text:
                continue

            page_chunks = self._chunk_text(cleaned_text)
            for idx_in_page, chunk_text in enumerate(page_chunks):
                chunks.append({
                    "id": f"{doc_id}_p{page_num}_c{idx_in_page}",
                    "doc_id": doc_id,
                    "filename": filename,
                    "category": category,
                    "page_number": page_num,
                    "total_pages": num_pages,
                    "chunk_index": global_chunk_idx,
                    "text": chunk_text,
                    "created_at": datetime.datetime.utcnow().isoformat()
                })
                global_chunk_idx += 1

        return chunks

    def _clean_text(self, text: str) -> str:
        """Clean extra whitespaces and non-printable characters."""
        lines = [line.strip() for line in text.splitlines()]
        cleaned = " ".join(line for line in lines if line)
        return cleaned

    def _chunk_text(self, text: str) -> List[str]:
        """Splits clean text into overlapping segments."""
        if len(text) <= self.chunk_size:
            return [text]

        chunks = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = start + self.chunk_size
            chunk = text[start:end]
            
            # Try to snap to the nearest space or sentence boundary if possible
            if end < text_len:
                last_space = chunk.rfind(" ")
                if last_space > self.chunk_size // 2:
                    end = start + last_space
                    chunk = text[start:end]

            chunks.append(chunk.strip())
            start = end - self.overlap if (end - self.overlap) > start else end

        return chunks


class EmbeddingService:
    def __init__(self):
        self.model = _model

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generates vector embeddings for a list of text strings.
        Uses sentence-transformers if available, or deterministic pseudo-vectors as fallback.
        """
        if self.model is not None:
            embeddings = self.model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
            return embeddings.tolist()
        else:
            # Deterministic fallback vector calculation (384 dimensions)
            return [self._fallback_vector(t) for t in texts]

    def _fallback_vector(self, text: str, dim: int = 384) -> List[float]:
        import hashlib
        import math
        vec = []
        for i in range(dim):
            h = hashlib.sha256(f"{text}_{i}".encode('utf-8')).hexdigest()
            val = (int(h[:8], 16) / 0xffffffff) * 2.0 - 1.0
            vec.append(val)
        # Normalize
        norm = math.sqrt(sum(x*x for x in vec)) or 1.0
        return [x / norm for x in vec]
