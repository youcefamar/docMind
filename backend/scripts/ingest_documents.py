import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.embedder import DocumentProcessor, EmbeddingService
from services.retriever import VectorStoreService

DATA_DOCS_DIR = os.getenv("DATA_DOCS_DIR", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "documents")))
SUPPORTED_EXTENSIONS = ('.pdf', '.docx', '.xlsx', '.xls', '.pptx', '.txt', '.md')

def batch_ingest():
    print(f"📁 Scanning document repository at: {DATA_DOCS_DIR}")
    if not os.path.exists(DATA_DOCS_DIR):
        print(f"Directory {DATA_DOCS_DIR} does not exist.")
        return

    doc_processor = DocumentProcessor()
    embedder_service = EmbeddingService()
    retriever_service = VectorStoreService()

    total_files = 0
    total_chunks = 0

    for root, dirs, files in os.walk(DATA_DOCS_DIR):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in SUPPORTED_EXTENSIONS:
                file_path = os.path.join(root, file)
                
                # Determine category: if in subfolder, use subfolder name. If in root data/documents, use "General"
                rel_path = os.path.relpath(file_path, DATA_DOCS_DIR)
                parts = rel_path.split(os.sep)
                category = parts[0] if len(parts) > 1 else "General"

                print(f"\nProcessing '{file}' [Type: {ext.upper()} | Category: {category}]...")
                try:
                    with open(file_path, "rb") as f:
                        file_bytes = f.read()

                    chunks = doc_processor.extract_chunks(
                        file_bytes=file_bytes,
                        filename=file,
                        category=category
                    )

                    if not chunks:
                        print(f"⚠️ No readable text extracted from {file}.")
                        continue

                    texts = [c["text"] for c in chunks]
                    embeddings = embedder_service.generate_embeddings(texts)
                    retriever_service.add_document_chunks(chunks, embeddings)

                    total_files += 1
                    total_chunks += len(chunks)
                    print(f"✅ Indexed {len(chunks)} chunks from '{file}' into pgvector!")
                except Exception as e:
                    print(f"❌ Error processing '{file}': {e}")

    print(f"\n==========================================")
    print(f"🎉 Batch Ingestion Complete!")
    print(f"Total Files Processed: {total_files}")
    print(f"Total Vector Chunks Indexed: {total_chunks}")
    print(f"==========================================\n")

if __name__ == "__main__":
    batch_ingest()
