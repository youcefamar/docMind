# DocMind — RAG System Architecture & Framework Analysis 🧠📄

> **Overview**: This document provides a complete technical breakdown of docMind's Retrieval-Augmented Generation (RAG) system and inspects every AI framework and library used in the codebase.

---

## 🔍 Framework & Library Inspection

### Question: Are frameworks like LangChain, LlamaIndex, LangGraph, MCP, or AI Agent frameworks used?

**No.** docMind deliberately does **not** use high-level AI orchestration frameworks (LangChain, LlamaIndex, LangGraph, Model Context Protocol / MCP, AutoGen, CrewAI, etc.). 

Instead, docMind is built **100% custom from scratch** using low-level, specialized Python libraries:

| Subsystem | Tool / Library | Role & Rationale |
|---|---|---|
| **Document Extraction** | `pypdf`, `python-docx`, `python-pptx`, `openpyxl` | Native multi-format parsing (PDF, DOCX, PPTX, XLSX, XLS, TXT, MD) with structural section & page location extraction |
| **Embeddings** | `sentence-transformers` | Multilingual dense vector embeddings (Target: `Qwen3-Embedding-0.6B`) |
| **Dense Vector Index** | `faiss-cpu` | High-performance local vector similarity search (`faiss.IndexFlatIP` with L2 normalization for Cosine Similarity) |
| **Lexical Index** | Custom Native Python (`math`, `json`, `re`) | Persistent Okapi BM25 sparse keyword search index with term frequency, IDF, and document length normalization |
| **Cross-Encoder Reranker** | `sentence-transformers` (`CrossEncoder`) | Deep semantic re-scoring of candidate passages using `BAAI/bge-reranker-v2-m3` |
| **Local LLM Engine** | `llama-cpp-python` | Offline CPU-compatible LLM inference using GGUF quantized models (Target: Qwen3-4B GGUF) |
| **Metadata & Storage** | SQLite (`sqlite3`) | Persistent storage for document records, background jobs, section blocks, and text chunks |
| **API Framework** | `fastapi`, `pydantic` | High-performance asynchronous REST API framework |

---

### Why Custom Architecture Over Frameworks?

1. **Air-Gapped Privacy & Security**: Higher-level frameworks often default to or obscure cloud API endpoints. docMind guarantees 100% offline, local CPU execution with zero data leakage.
2. **Elimination of Abstraction Bloat**: Avoids complex "black box" chain abstractions, volatile API changes, and hidden prompt wrappers.
3. **Exact Citation Control**: Enables exact positional source tracking (`[S1]`, `[S2]`) directly mapped to pages, slides, or sheet names.
4. **Custom Hybrid Fusion & Reranking**: Allows direct implementation of Reciprocal Rank Fusion (RRF) and Cross-Encoder re-scoring without framework limitations.

---

## 🏗️ How docMind's RAG System is Built

The RAG pipeline operates across 5 key phases:

```mermaid
flowchart TD
    A[Document Upload / Knowledge Folder] --> B[Phase 1: Ingestion & Validation]
    B --> C[Phase 2: Structural Extraction & Chunking]
    C --> D[(SQLite Metadata Store)]
    C --> E1[(FAISS Dense Vector Index)]
    C --> E2[(BM25 Lexical Inverted Index)]
    
    F[User Question] --> G[Phase 3: Dual Retrieval & Fusion]
    E1 --> G
    E2 --> G
    G --> H[Reciprocal Rank Fusion RRF]
    H --> I[Cross-Encoder Reranker BGE-v2-m3]
    
    I --> J[Phase 4: Grounded Local Generation]
    J --> K[Llama-cpp Local Qwen LLM]
    
    K --> L[Phase 5: Post-Processing & Citation Validation]
    L --> M[Remove <think> Tags & Validate [S1] Labels]
    M --> N[Return Answer + Verified Source Cards + Confidence Score]
```

---

### Phase 1: Ingestion & Validation
* **Source Files:** [`backend/services/ingestion.py`](file:///D:/Projects/docMind/backend/services/ingestion.py)
* **File Signature Verification:** Validates magic byte headers (e.g., `%PDF-` for PDFs, `PK` for Office Open XML `.docx`/`.pptx`/`.xlsx`, `\xd0\xcf\x11\xe0` for legacy `.xls`) rather than relying solely on file extensions.
* **Content Hash Deduplication:** Calculates SHA-256 hashes of uploads to prevent duplicate indexing.
* **File Size & Limits:** Enforces file size limits (default 50MB) and filename path-traversal safety checks.

---

### Phase 2: Extraction, Chunking & Persistence
* **Source Files:** [`backend/services/embedder.py`](file:///D:/Projects/docMind/backend/services/embedder.py), [`backend/services/metadata_store.py`](file:///D:/Projects/docMind/backend/services/metadata_store.py)
* **Structural Text Extraction:** Extracts plain text along with exact structural coordinates (`location_type`: `"page"`, `"slide"`, or `"sheet"`; `location_value`: `"1"`, `"2"`, etc.).
* **Overlapping Chunking:** Splits document text into manageable chunks while maintaining sentence/heading boundaries and overlapping context.
* **Metadata Persistence:** Stores document records, jobs, and chunk records in SQLite (`metadata.sqlite`).
* **Dual Indexing:**
  * **Dense Index ([`backend/services/dense_index.py`](file:///D:/Projects/docMind/backend/services/dense_index.py)):** Generates dense vector embeddings using `sentence-transformers` and stores them in a FAISS `IndexFlatIP` index with L2 vector normalization.
  * **Sparse BM25 Index ([`backend/services/bm25_index.py`](file:///D:/Projects/docMind/backend/services/bm25_index.py)):** Builds a custom inverted index storing term frequencies, posting lists, and document length statistics for Okapi BM25 keyword matching.

---

### Phase 3: Dual Retrieval & Hybrid Fusion
* **Source Files:** [`backend/routes/chat.py`](file:///D:/Projects/docMind/backend/routes/chat.py), [`backend/services/quality_retriever.py`](file:///D:/Projects/docMind/backend/services/quality_retriever.py), [`backend/services/reranker.py`](file:///D:/Projects/docMind/backend/services/reranker.py)
* **Retrieval Profiles:**
  * **Fast Mode:** Performs direct dense vector search via FAISS (`top_k=5`).
  * **Quality Mode (Hybrid RAG):**
    1. Executes dense FAISS search and sparse BM25 search concurrently (fetching up to `candidate_k=30` matches each).
    2. **Reciprocal Rank Fusion (RRF):** Fuses the ranked lists using:
       $$RRF\_Score(d) = \sum_{m \in M} \frac{1}{k + r_m(d)} \quad (k=60)$$
       This combines semantic and keyword ranks without comparing incompatible raw similarity/BM25 score scales.
    3. **Cross-Encoder Reranking:** Passes the fused candidates through `BAAI/bge-reranker-v2-m3` using `sentence-transformers` `CrossEncoder` to re-score query-passage relevance and return the top `final_k=5` results.

---

### Phase 4: Grounded Local LLM Answer Synthesis
* **Source Files:** [`backend/services/llm.py`](file:///D:/Projects/docMind/backend/services/llm.py)
* **Offline Local LLM Engine:** Executes GGUF models locally via `llama-cpp-python` (e.g. Qwen3-4B GGUF). No cloud APIs or network requests are made.
* **Deterministic Source Context Formatting:** Constructs a system prompt appending retrieved passages with positional source tags:
  ```text
  [S1] Filename: policy.pdf (Page 3)
  Excerpt: Remote work is permitted up to 2 days per week...

  [S2] Filename: handbook.docx (Page 12)
  Excerpt: Core working hours are 9 AM to 5 PM...
  ```

---

### Phase 5: Post-Processing & Citation Validation
* **Source Files:** [`backend/services/llm.py`](file:///D:/Projects/docMind/backend/services/llm.py)
* **Reasoning Tag Cleanup (`strip_thinking_content`):** Strips `<think>...</think>` internal reasoning blocks emitted by local GGUF models before sending answers to the user interface.
* **Positional Citation Sanitization (`sanitize_citation_labels`):** Validates generated source tags (`[S1]`, `[S2]`) against the actual source array, removing hallucinated or out-of-range labels (`[S99]`).
* **Lexical Support Verification (`citation_is_supported`):** Performs lexical overlap analysis between the LLM answer and the source chunk excerpt to flag citations as supported or unsupported.
* **Confidence Scoring:** Computes confidence scores and assigns human-readable labels (`HIGH`, `MEDIUM`, `LOW`) based on chunk similarity scores, citation presence, and answer content.
