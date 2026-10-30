# DocMind — Fast Document Search & Comparison with Nebius & Nemotron 🚀

> **Hackathon Submission:** Nebius & NVIDIA Global AI Hackathon  
> **Track:** Best Apps and Agents Track *(Alternative: Personal AI Track)*  
> **Infrastructure:** Nebius Token Factory (High-Performance NVIDIA GPU Cloud)  
> **Models:** `NVIDIA Nemotron Nano` (Tier 1 Router) & `NVIDIA Nemotron 3 Ultra` (Tier 2 Reasoning)  
> **License:** MIT Open Source License

---

## 1. What DocMind Is & Why We Built It

DocMind is an internal knowledge assistant for company files (PDFs, Word documents, slides, spreadsheets). Instead of manually searching through 50-page handbooks or contracts, you ask a question in plain English and get an answer backed by clickable citations that take you straight to the exact page.

### The Problem with Most RAG Setups
1. **Local CPU inference is painfully slow:** In our initial prototype, running a 4B model locally on a consumer CPU took 14 to 30 seconds per question. Your laptop fans spin up, and waiting that long ruins the workflow.
2. **Sending everything to a massive frontier model burns money:** Shoveling 30 raw text chunks into an expensive cloud model wastes API credits. Much of that text is just noise that dilutes the answer.
3. **Single-question search isn't enough:** Real work usually involves asking what *changed* between two files — like comparing the 2025 vs 2026 employee handbook or two versions of a contract. Standard RAG systems struggle with cross-document comparisons.

### How We Fixed It: Two Nemotron Models on Nebius
We split the workload between two specialized NVIDIA Nemotron models hosted on Nebius Token Factory:

```mermaid
flowchart TD
    subgraph Client ["Frontend"]
        UI["Next.js 16 UI\n(Chat + Document Compare)"]
    end

    subgraph Backend ["DocMind Backend"]
        API["FastAPI Orchestrator"]
        Search[("Hybrid FAISS + BM25")]
    end

    subgraph Nebius ["Nebius Token Factory"]
        Router["Tier 1: Nemotron Nano (~68ms)\n• Cleans up messy queries\n• Adds search keywords\n• Detects category & filters noise"]
        Reasoning["Tier 2: Nemotron 3 Ultra (~760ms)\n• Writes grounded answer with [S1]/[S2] citations\n• Synthesizes cross-document diff tables"]
    end

    UI -->|"User Question"| API
    API -->|"Raw query"| Router
    Router -->|"Expanded keywords"| API
    API -->|"Hybrid search"| Search
    Search -->|"Top relevant chunks"| API
    API -->|"Clean context"| Reasoning
    Reasoning -->|"Streamed answer + citations"| API
    API -->|"Live response with telemetry"| UI
```

---

## 2. Real Benchmark Numbers

We benchmarked the whole pipeline using `backend/scripts/benchmark_nebius.py`:

| Setup | Model | Hardware | Latency | TTFT | Tokens / Sec | What It Means |
|---|---|---|---|---|---|---|
| **Local Baseline** | `qwen3-4b-q4_k_m.gguf` | Intel CPU (Consumer Laptop) | 14,250 ms | 1,820 ms | 11.4 tps | Painfully slow, locks up your machine |
| **Tier 1 Router** | `nvidia/nemotron-nano` | NVIDIA GPU (Nebius Token Factory) | 68.4 ms | 38.2 ms | 118.5 tps | Fast enough to run on every single query |
| **Tier 2 Reasoning** | `nvidia/nemotron-3-ultra` | NVIDIA GPU (Nebius Token Factory) | 760.5 ms | 112.0 ms | 88.4 tps | Deep synthesis with strict citations |
| **Dual-Nemotron Pipeline** | **Tier 1 + Tier 2** | **NVIDIA GPU (Nebius Token Factory)** | **828.9 ms** | **38.2 ms** | **88.4 tps** | **17.2x faster, 72% credit savings** |

> **Key Takeaway:** The Dual-Nemotron pipeline cuts latency from **14.2 seconds down to 0.8 seconds** (17.2x faster). By letting Nemotron Nano filter out noisy chunks before calling the larger model, we also save **72% of inference credits**.

---

## 3. What We Built for the Hackathon

### 1. Two-Tier Nemotron Pipeline & Live Telemetry
- **Tier 1 (`nvidia/nemotron-nano`):** Takes whatever messy question the user types and reformulates it in under 70ms. It adds helpful synonyms for lexical BM25 search and detects the right document category (HR, Tech, Legal, Finance).
- **Tier 2 (`nvidia/nemotron-3-ultra`):** Takes only the cleanest chunks, answers the question, and tags every fact with `[S1]`, `[S2]` citation pills. If the docs don't have the answer, it tells you directly instead of hallucinating.
- **Live Telemetry:** Every response shows the exact routing time, generation speed (tokens/sec), and estimated credit savings right in the UI.

### 2. Side-by-Side Document Comparison (`/compare`)
- Select two or more documents from your uploaded files.
- Type in what you want to focus on (e.g., *"remote work rules, PTO days, and equipment budgets"*).
- Nemotron 3 Ultra reads both documents and outputs:
  - An executive summary of the update.
  - A side-by-side **Key Differences Matrix** table.
  - A **Contradiction Analysis** flagging conflicting rules.
  - A **Risk Assessment** highlighting compliance concerns.

### 3. Graceful Offline Fallback
- If `NEBIUS_API_KEY` isn't set, the app doesn't crash or throw unhandled errors. It automatically switches to deterministic local responses so tests and CI run cleanly without an internet connection.

---

## 4. Statement of Significant Updates (Hackathon Requirement)

In accordance with Hackathon rules regarding existing repositories:

> *"Prior to this hackathon, DocMind was a proof-of-concept limited to slow, offline CPU generation (15–30s per question) with no way to compare documents.
>
> During the hackathon period, we made the following major changes:
> 1. Moved generation from slow local CPUs to **Nebius Token Factory** on NVIDIA GPUs.
> 2. Built a **Dual-Nemotron routing pipeline**: using `Nemotron Nano` for sub-100ms query expansion and chunk filtering, and `Nemotron 3 Ultra` for deep grounded reasoning.
> 3. Added a new **Deep Compare tool** (`POST /api/compare` and the `/compare` UI page) that generates side-by-side difference matrices and conflict checks across multiple files.
> 4. Added real-time latency and token telemetry to track speed and cost savings.
> 5. Created an automated benchmark suite (`benchmark_nebius.py`) proving a **17.2x speedup** and **72% credit savings**."*

---

## 5. Quickstart & Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- Nebius Token Factory API Key

### Step 1: Set up your environment
Copy `.env.example` to `.env` in the backend:

```env
# LLM Provider Configuration
DOCMIND_LLM_PROVIDER=nebius

# Nebius Token Factory & NVIDIA Nemotron Configuration
NEBIUS_API_KEY=your_nebius_api_key_here
NEBIUS_BASE_URL=https://api.studio.nebius.ai/v1
NEBIUS_REASONING_MODEL=nvidia/nemotron-3-ultra
NEBIUS_FAST_MODEL=nvidia/nemotron-nano
DOCMIND_NEBIUS_TIMEOUT=60.0
```

### Step 2: Start the Backend
```bash
cd backend
python -m venv .venv
# On Windows: .venv\Scripts\activate | On Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
python main.py
```
FastAPI will run at `http://localhost:8000` (Swagger docs at `http://localhost:8000/docs`).

### Step 3: Start the Frontend
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:3000` in your browser.

### Step 4: Run the Benchmark
```bash
cd backend
python scripts/benchmark_nebius.py --repetitions 3
```

---

## 6. Repository Layout

```text
docMind/
├── backend/
│   ├── routes/
│   │   ├── chat.py             # Dual-Nemotron search & chat
│   │   ├── compare.py          # Document comparison endpoint (/api/compare)
│   │   ├── documents.py        # File upload and indexing handlers
│   │   └── status.py           # Health check and telemetry
│   ├── services/
│   │   ├── query_router.py     # Nemotron Nano router (<100ms)
│   │   ├── comparison.py       # Nemotron 3 Ultra multi-doc comparison
│   │   ├── llm.py              # Nebius Token Factory client
│   │   └── runtime.py          # Service singletons
│   └── scripts/
│       ├── benchmark_nebius.py # Speed & token benchmark
│       └── generate_demo_voiceover.py # Demo audio generator
├── frontend/
│   ├── app/
│   │   ├── chat/               # Chat UI with clickable citation pills
│   │   └── compare/            # Cross-document comparison tab
│   └── components/
│       ├── ChatWindow.tsx      # Conversation view with citations
│       └── Navbar.tsx          # Navigation bar with Compare tab
├── demo/
│   └── sample_documents/       # 2025 vs 2026 policy docs for quick testing
└── docs/
    ├── HACKATHON_PLAN.md       # Implementation roadmap
    ├── DEMO_STORYBOARD.md      # 3-minute video script & visual cues
    └── SUBMISSION.md           # Devpost submission writeup
```
