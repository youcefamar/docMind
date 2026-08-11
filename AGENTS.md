# DocMind — Agent Operating Rules

> Read this file first. Read it every time. It is the highest-priority instruction in this repository.

---

## 1. Project Mission & Current Architecture

DocMind is an **offline internal knowledge assistant**. Employees ask questions in plain language and receive grounded answers with exact source citations and page numbers. No cloud LLM. No external API key required for inference.

### Frozen production pipeline (do not casually replace any stage)

```
Document ingestion (PDF / DOCX / PPTX / XLSX / TXT / MD)
  → text extraction per page/slide/sheet   [services/embedder.py → DocumentProcessor]
  → ~600-char chunks with 100-char overlap  [settings: DOCMIND_CHUNK_SIZE_CHARS]
  → Qwen3-Embedding-0.6B (1024-dim, local) [services/embedder.py → QwenEmbeddingService]
  → FAISS flat IP index + BM25 JSON index  [services/dense_index.py, services/bm25_index.py]
  → SQLite metadata (documents/blocks/chunks/jobs) [services/metadata_store.py]

Query path:
  Fast profile   → dense FAISS cosine → top-5
  Quality profile → dense (candidate_k=30) + BM25 (candidate_k=30) → RRF → optional BGE reranker → top-5
  Both profiles  → Qwen3-4B GGUF (local, CPU) → grounded answer with [S1]/[S2] citation labels
```

These choices are **research results**, not defaults. If you think a stage should change, open a discussion — don't silently swap models, chunk sizes, or retrieval strategies.

### Key files at a glance

| Path | Purpose |
|------|---------|
| `backend/main.py` | FastAPI app, CORS, route registration |
| `backend/routes/` | `chat`, `config`, `documents`, `models`, `sources`, `status` |
| `backend/services/runtime.py` | Shared singletons: embedder, dense/BM25 index, LLM, folder sync |
| `backend/services/ingestion.py` | Document lifecycle, validation, atomic writes |
| `backend/services/metadata_store.py` | SQLite persistence — source of truth for document/chunk state |
| `backend/services/llm.py` | Qwen GGUF generation, `<think>` stripping, citation sanitization |
| `backend/models/contracts.py` | Pydantic v2 contracts shared by all layers |
| `backend/services/settings.py` | Env-backed frozen dataclass — all tunables live here |
| `frontend/` | Next.js 16 App Router, TypeScript 6, Tailwind CSS |
| `notebooks/` | Week-1 prototype — research artifact, not production code |
| `data/` | Local persistence root (SQLite, FAISS, BM25, originals) — never commit |

---

## 2. Agent Startup Protocol

Before touching any file, do this **once**, in order, and stop as soon as you have enough context:

1. `git status` — know what branch you're on and what's dirty.
2. Inspect the root tree one level deep.
3. Re-read this file (`AGENTS.md`).
4. Read only the **relevant** README sections or `docs/` files for the task.
5. Find the actual implementation with targeted `grep`/search — do not recursively read the whole repo.
6. Read the relevant tests to understand expected behaviour.
7. Identify the source of truth (see §3).
8. Write a short internal execution plan before modifying anything.
9. Modify only what serves the task.

**Do not dump notebooks, generated JSON, full datasets, or large fixture files into your context. Never read files you don't need.**

---

## 3. Source-of-Truth Hierarchy

When sources conflict, investigate rather than blindly following either:

```
1. User request
2. AGENTS.md  ← you are here
3. Executable code + passing tests + live config
4. Current architecture docs (docs/)
5. Research notebooks and experiment artifacts
6. Comments, old READMEs, stale planning docs
```

Working code + green tests beat documentation. If they disagree, find out why before touching anything.

---

## 4. Git Workflow (Solo Repository)

This is a solo project. There is no PR review requirement.

```
main is the normal working branch.
No feature branch is required unless doing a risky multi-step change.
If branching: feature/x, fix/x, chore/x, docs/x — merge and delete when done.
Never force-push unless explicitly asked.
Never commit: secrets, .env, model weights (.gguf), FAISS index files,
              BM25 JSON indexes, SQLite files, generated embeddings, or large caches.
```

### ⚠️ Agent commit/push rules — read carefully

**The agent MUST NOT run `git commit`, `git push`, or `git merge` autonomously.**

The user owns the git history. The agent's job is to make code changes, run quality gates, and report what's ready. The user decides when and what to commit.

**Only exceptions** — the agent may run git commands without explicit instruction when:
- The user says "commit this", "push this", or similar direct instruction.
- The user's request is *only* about a git operation (e.g. "create a branch", "check status").

In all other cases: make the changes → run the gates → stop → tell the user what to commit.

Quality gates to run before telling the user to commit:

```bash
# Backend
cd backend && .venv/Scripts/python.exe -m ruff check .
cd backend && .venv/Scripts/python.exe -m pytest tests/ -q

# Frontend (when frontend files changed)
cd frontend && npm run build
```

All gate checks must pass. Do not tell the user to commit with failing tests or lint errors.

---

## 5. Research Protection

DocMind deliberately freezes experimental variables. Agents must honour this:

- **DEV split** can be used for iteration and tuning.
- **Held-out TEST split** must never silently become tuning data.
- **Frozen experiment contexts** remain frozen. If you change a model, chunk size, prompt, or reranker, that is a **new experiment** — create a new experiment config, don't overwrite the result.
- Preserve: random seeds, evaluation metrics, input manifests, model IDs, and all experiment parameters.
- Never edit benchmark output files to make results look better.
- `scripts/profile_local.py` writes profiling runs to `data/profiling/runs/`. Leave the active indexes untouched during profiling unless `--rebuild-indexes` is explicitly passed.

---

## 6. Production vs. Experiment Boundary

```
notebooks/          ← research artifact, not importable production code
data/profiling/     ← experiment output, not production state
research artifacts  ≠ production runtime code
```

Promote research code into reusable modules deliberately. Production app code must never import from notebooks or generated experiment output directly.

---

## 7. Architecture Discipline

- **Prefer existing abstractions.** DocMind uses lower-level components intentionally — no LangChain, LangGraph, or LlamaIndex unless explicitly requested with a clear justification.
- **Add a dependency only when it solves a demonstrated gap** that cannot be closed with what is already installed.
- **Keep layers separable:** extraction, chunking, embedding, indexing, retrieval, reranking, generation, storage, and API are distinct concerns. Keep them that way.
- Avoid giant god-modules. Keep functions small and focused.
- No unnecessary frameworks. No over-engineering.

---

## 8. Configuration vs. Code

```
Runtime or deployment choice?   → DOCMIND_* env var in .env
Secret or credential?           → env var, never in code
Experiment parameter?           → versioned experiment config file
Stable algorithm invariant?     → code constant is fine
User or business behaviour?     → config when it genuinely varies
```

Do not push every value into config. Config hell is as bad as hardcoding hell.

**Never edit `.env` or real secrets.** Use `.env.example` as the template.

---

## 9. RAG-Specific Correctness Rules

Any change to the pipeline must preserve:

- Document and source identity (stable `doc_id`, `chunk_id`)
- Page / slide / section metadata attached to every chunk
- Deterministic IDs where the current code produces them
- Citation provenance: `[S1]` labels must map to real retrieved sources, never invented ones
- Retrieval/generation separation — generation must only see what retrieval returns
- Explicit refusal when evidence is insufficient (`I don't know based on the provided documents.`)
- Same-language output preference
- Explicit handling of extraction failure (empty text → `IngestionError`, not silent skip)
- Atomic index writes (`.tmp` rename pattern already used — keep it)
- Reproducible indexing: same chunks + same model = same index

---

## 10. Testing Strategy

Match the test type to the change:

| Change type | Required tests |
|-------------|----------------|
| Extractor / parser | Extraction fixtures; test malformed / empty docs |
| Chunking | Boundary tests; metadata carried through; benchmark check |
| Retrieval | Retrieval metric test with known fixtures |
| LLM / generation | Grounding test; citation validation; no-answer path |
| API route | API contract test via `httpx` / `TestClient` |
| Storage / metadata | Persistence and round-trip tests |
| Bug fix | Regression test that would have caught the bug |
| Config / settings | Settings parsing test with env overrides |

Run targeted tests first, full suite near completion. Do not commit with red tests.

---

## 11. Debugging Rules

No random patching.

```
1. Reproduce the failure with a minimal case.
2. Isolate the layer (extraction / indexing / retrieval / generation / API).
3. Determine the root cause.
4. Write a regression test that would have caught it.
5. Implement the smallest general fix.
6. Verify related paths are not broken.
```

---

## 12. Token-Efficient Agent Behaviour

- Search before reading. Use grep/search to find relevant code, then read only those files.
- Inspect relevant slices of large files, not entire files.
- Never dump datasets, notebooks, or generated JSON into context without a specific need.
- Don't re-read files you already understand unless they changed.
- Reuse existing utilities. Check `services/`, `models/contracts.py`, and `services/settings.py` before writing new helpers.
- Avoid verbose planning documents for small tasks.
- Don't generate large repo summaries.
- Inspect `git diff` rather than re-reading every modified file.
- Stop investigating once you have enough evidence to implement safely.
- Run targeted tests first; run the full suite only near completion.

---

## 13. Planning Rules

**Small fix** → investigate → fix → regression test → commit.

**Large change** → write a compact plan containing:
- Objective
- Affected components
- Dependencies and risks
- Implementation sequence
- Tests required
- Data / migration risks

No 40-step ceremonial plans. No placeholder TODO comments left in committed code.

---

## 14. Coding Style

- Functions small and focused — one responsibility.
- Clear, self-documenting names. No abbreviations for non-obvious concepts.
- Pydantic v2 models for all API contracts — update `models/contracts.py` when contracts change.
- `from __future__ import annotations` at the top of every service file.
- Structured logging with `logging.getLogger("docmind.<module>")`. No bare `print()` in services (allowed only for one-off scripts).
- Timezone-aware datetimes: always `datetime.now(timezone.utc)`, never `datetime.utcnow()`.
- Atomic file writes: write to `.tmp`, then `os.replace()`. Already established — keep it.
- No secrets, credentials, or model weights in code or committed files.

---

## 15. Completion Gate

Before reporting done, verify every item:

```
□ Requested behaviour is implemented
□ Root cause is addressed (not just symptoms)
□ No unrelated refactoring snuck in
□ Regression / unit tests written and passing
□ Ruff lint passes (cd backend && ruff check .)
□ Frontend build passes when frontend files changed (cd frontend && npm run build)
□ Generated artifacts reviewed (no accidental data files staged)
□ Docs updated if a public contract or API changed
□ git diff reviewed — nothing unintended staged
□ No secrets, model weights, or large binary files introduced
□ Benchmark and experiment invariants preserved
□ No TODO / placeholder comments left in committed code
```

Final response to the user must only contain:

```
Changed:    <concise list of what was modified>
Verified:   <tests run, lint result>
Decisions:  <non-obvious choices made and why>
Remaining:  <only if a real issue is left open>
```
