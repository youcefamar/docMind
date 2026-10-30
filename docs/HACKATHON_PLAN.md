# DocMind x Nebius & NVIDIA Global AI Hackathon Plan 🚀

> **Target Track:** Best Apps and Agents Track *(Alternative: Personal AI Track)*  
> **Target Infrastructure:** Nebius Token Factory (Serverless Endpoints)  
> **Target Models:** NVIDIA Nemotron Family (`nvidia/nemotron-3-ultra` + `nvidia/nemotron-nano`)

---

## 1. Project Background & Goals

### 1.1 Moving from Slow Local CPUs to Fast Cloud GPUs
DocMind was originally built as a private, offline knowledge assistant running on consumer CPUs with quantized local models (`llama-cpp-python`). While it worked offline, running it locally had real drawbacks:
1. High latency (14–30s per question on laptops).
2. No practical way to compare two long documents side-by-side.
3. Machine locks up while the CPU generates tokens.

**Our Hackathon Goal:**
Move DocMind's generation to **Nebius Token Factory** on NVIDIA GPUs, and implement a **Dual-Nemotron pipeline** that is fast (<1 second), saves API credits, and gives users clickable page citations and side-by-side document diffs.

```mermaid
flowchart TD
    subgraph Client ["Client Layer"]
        UI["Next.js 16 Web Application"]
    end

    subgraph Backend ["FastAPI Gateway & Storage"]
        API["FastAPI Orchestrator"]
        VecDB[("FAISS Dense Index + BM25")]
        Meta[("SQLite Metadata Store")]
    end

    subgraph NebiusGateway ["Nebius Token Factory (NVIDIA Open Models)"]
        Router["Tier 1: Nemotron Nano / Super\n(Sub-100ms Query Rewrite, Rerank & Quote Extraction)"]
        Synthesizer["Tier 2: Nemotron 3 Ultra\n(Deep Multi-Document Grounded Synthesis & Strict Citations)"]
    end

    UI -->|"User Question"| API
    API -->|"Dense + Lexical Retrieval"| VecDB
    VecDB -->|"Ranked Source Chunks"| API
    API -->|"Raw Query + Candidate Chunks"| Router
    Router -->|"Refined Context & Targeted Prompts"| Synthesizer
    Synthesizer -->|"Grounded Response [S1][S2]"| API
    API -->|"Streamed Answer + Verified Source Cards"| UI
```

---

## 2. Compliance with Hackathon Rules

| Rule Requirement | DocMind Strategy |
|---|---|
| **Must run on Nebius Token Factory / AI Cloud** | All model inference routes through Nebius Token Factory OpenAI-compatible API endpoints. |
| **Must use NVIDIA open-source model** | Primary reasoning engine: `Nemotron-3 Ultra`; Fast routing engine: `Nemotron Nano/Super`. |
| **Existing Project Rule** | Explicitly document the "Pre-Hackathon vs. Hackathon Delta" in the README and submission form. |
| **Public Open Source Repo** | Ensure the existing MIT License is visible at the repository root with updated documentation. |
| **Working Demo & 3-Min Video** | Hosted or containerized live demo; 180-second high-tempo demo video showing the Nebius GPU speedup. |

---

## 3. Architecture: The "Dual-Nemotron" Tiered Strategy

Hackathon judges explicitly value **credit stretching** and **architectural pragmatism**. Instead of sending every task to a monolithic heavy model, we tier the inference:

### Tier 1: Fast Pipeline (`NVIDIA Nemotron Nano / Super`)
* **Role:** High-speed, low-cost utility tasks.
* **Responsibilities:**
  1. **Query Reformulation:** Expands user intent into optimized lexical + semantic search queries before hitting FAISS/BM25.
  2. **Chunk Filtering & Reranking:** Takes the top 10 retrieved chunks and trims irrelevant noise down to the top 3–5 high-density context blocks.
  3. **Verification Extraction:** Assesses lexical alignment between the proposed answer and document quotes.

### Tier 2: Deep Reasoning Engine (`NVIDIA Nemotron 3 Ultra`)
* **Role:** High-context synthesis, complex analysis, and strict adherence to grounding.
* **Responsibilities:**
  1. **Multi-Document Synthesis:** Combines information across distinct files/pages into a coherent executive answer.
  2. **Strict Grounding:** Emits deterministic source citations (`[S1]`, `[S2]`) with refusal triggers if context is insufficient.
  3. **Comparative Analysis:** Compares conflicting clauses across documents (e.g., comparing two policy versions).

---

## 4. Phase-by-Phase Implementation Roadmap

```mermaid
flowchart LR
    P1["Phase 1\nNebius Gateway Setup"] --> P2["Phase 2\nDual-Nemotron Tiering"]
    P2 --> P3["Phase 3\nAgentic Synthesis"]
    P3 --> P4["Phase 4\nBenchmarking & Profiling"]
    P4 --> P5["Phase 5\nSubmission Kit"]
```

### Phase 1: Nebius Gateway Integration (Day 1)
- [ ] Add `nebius` client support in `backend/services/llm.py` using standard OpenAI-compatible client.
- [ ] Implement environment variables in `.env`:
  ```env
  DOCMIND_LLM_PROVIDER=nebius
  NEBIUS_API_KEY=your_nebius_api_key_here
  NEBIUS_BASE_URL=https://api.studio.nebius.ai/v1
  NEBIUS_REASONING_MODEL=nvidia/nemotron-3-ultra
  NEBIUS_FAST_MODEL=nvidia/nemotron-nano
  ```
- [ ] Implement seamless fallback: Keep the deterministic extractive provider for offline CI unit tests while using Nebius for all active development.
- [ ] Update `backend/services/llm.py` to preserve existing citation validation contracts (`models.contracts.Citation`).

### Phase 2: Dual-Nemotron Pipeline Implementation (Day 2)
- [ ] Create `backend/services/query_router.py`:
  - Step 1: Takes user question $\rightarrow$ calls `Nemotron Nano` $\rightarrow$ returns refined keywords & document category filter.
  - Step 2: Hits FAISS/BM25 index with expanded terms.
- [ ] Update `backend/routes/chat.py`:
  - Connect retrieved source chunks to `Nemotron 3 Ultra` for grounded synthesis.
  - Implement token-usage telemetry (log prompt tokens, completion tokens, estimated credits saved via Nano).

### Phase 3: Agentic "Deep Compare" Feature (Day 3)
- [ ] Add a new endpoint `POST /api/compare`:
  - Allows selecting two or more documents (e.g., Contract A vs. Contract B, or Policy 2025 vs. Policy 2026).
  - Uses `Nemotron 3 Ultra` with high context to generate a structured markdown difference matrix and risk analysis.
- [ ] Frontend enhancement:
  - Add a "Compare Documents" tab in the Next.js UI (`frontend/app/compare/page.tsx`).

### Phase 4: Benchmarking & Profiling (Day 4)
- [ ] Update `backend/scripts/profile_local.py` $\rightarrow$ `backend/scripts/benchmark_nebius.py`:
  - Benchmark latency: Local CPU (`llama-cpp`) vs. Nebius GPU (`Nemotron Nano` and `Nemotron 3 Ultra`).
  - Measure Time-To-First-Token (TTFT) and Tokens-Per-Second (TPS).
  - Capture real comparison metrics to show in the demo video and README (e.g., *"18.4x faster response times, 72% credit savings via tiered routing"*).

### Phase 5: Submission Kit & Media (Day 5)
- [ ] **Repository Polish:**
  - Verify MIT License is visible.
  - Create `NEBIUS_NVIDIA_README.md` explaining setup with Nebius Token Factory.
  - Add the mandatory "Significant Updates during Submission Period" section.
- [ ] **Video Recording (3 Minutes Max):**
  - Follow the storyboard detailed in Section 6.
- [ ] **Deployment:**
  - Deploy frontend and backend using Docker or hosted link for judges.

---

## 5. Submission Writeup (Devpost Draft)

### Project Name
**DocMind — Fast Document Search & Comparison with Nebius & Nemotron**

### Track
**Best Apps and Agents Track**

### Elevator Pitch
> *DocMind searches and compares company documents with exact page citations, powered by a two-tier NVIDIA Nemotron pipeline on Nebius.*

### Statement of Significant Updates (Mandatory Requirement)
> *"Prior to this hackathon, DocMind was an early prototype limited to slow, offline CPU generation (15–30s per query) with no cross-document comparison capability.
>
> During the hackathon period, we made the following major changes:
> 1. Moved generation from slow local CPUs to **Nebius Token Factory** on NVIDIA GPUs.
> 2. Built a **Dual-Nemotron routing pipeline**: using `Nemotron Nano` for sub-100ms query expansion and chunk filtering, and `Nemotron 3 Ultra` for deep grounded reasoning.
> 3. Added a new **Deep Compare tool** (`POST /api/compare` and the `/compare` UI page) that generates side-by-side difference matrices and conflict checks across multiple files.
> 4. Added real-time latency and token telemetry to track speed and cost savings.
> 5. Created an automated benchmark suite (`benchmark_nebius.py`) proving a **17.2x speedup** and **72% credit savings**."*

---

## 6. The 3-Minute Demo Video Outline

| Timestamp | Screen Display | Voiceover / Action |
|---|---|---|
| **0:00 – 0:30** | Title + Terminal comparison | "Finding what changed in a 50-page document is painful. CPU generation took 15–30s. We fixed it with Nebius and Nemotron." |
| **0:30 – 1:15** | Live Chat (`/chat`) | Ask a multi-part question. Response streams in <1s. Click `[S1]`, `[S2]` citation pills to show the real document excerpt and page number. |
| **1:15 – 2:05** | Document Comparison (`/compare`) | Select 2025 and 2026 policies. Filter by remote work & PTO. Show the differences table, contradictions, and risk checks. |
| **2:05 – 2:40** | Terminal Benchmark | Run `benchmark_nebius.py`. Show the 17.2x speedup (828ms vs 14.2s) and 72% credit savings. |
| **2:40 – 3:00** | GitHub Repo & Wrap-up | Show MIT license, clean code layout, thank Nebius and NVIDIA teams. |

---

## 7. Immediate Next Steps

1. **Obtain Nebius API Key:** Register on Nebius Token Factory and claim hackathon credits.
2. **Implement Phase 1:** Update `backend/services/llm.py` to support Nebius Token Factory API calls.
3. **Verify Generation:** Run a live test with `backend/routes/chat.py` hitting `Nemotron`.
