# 2. LLM Engine Selection: Local GGUF (`llama-cpp-python`)

> Superseded by P4: Groq is no longer a supported runtime dependency or
> fallback. This record is retained as historical context for the prototype.

- **Status**: Accepted
- **Date**: 2026-07-25
- **Deciders**: AI Engineering Team

---

## Context & Problem Statement

DocMind requires an LLM inference engine to process retrieved document context chunks and synthesize concise, grounded natural language responses. Enterprise privacy requires 100% offline local inference support using quantized `.gguf` weights, while allowing optional cloud acceleration via Groq API.

---

## Decision Drivers

- **Data Privacy**: 100% offline inference capability with no external data transmission.
- **Quantization Efficiency**: 4-bit quantized GGUF weights (`Q4_K_M`) fit comfortably in standard RAM (4GB - 6GB VRAM/RAM).
- **Format Standard**: `.gguf` format supported natively via `llama-cpp-python`.

---

## Decision Outcome

**Chosen Option**: **Local GGUF Models via `llama-cpp-python`** (e.g. `llama-3.1-8b-instruct.Q4_K_M.gguf`).

### Key Implementation Features
- **Local Path**: Looks for `.gguf` model files under `backend/models/` or via `GGUF_MODEL_PATH` in `.env`.
- **CPU & GPU Acceleration**: Utilizes multi-threaded CPU execution (`n_threads=os.cpu_count()`) or Metal/CUDA offloading when available.
- **Fallback**: Secondary fallback to Groq API or direct matching context snippets if no `.gguf` file is present.
