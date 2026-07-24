# 2. LLM Provider Selection: Groq (Llama 3.1 8B)

- **Status**: Accepted
- **Date**: 2026-07-25
- **Deciders**: AI Engineering Team

---

## Context & Problem Statement

DocMind requires an LLM inference engine to process retrieved document context chunks and synthesize concise, grounded natural language responses for employees. The inference solution must provide low latency, high accuracy in following system prompts (such as strictly citing page numbers and stating "I don't know"), and cost efficiency.

---

## Decision Drivers

- **Inference Speed**: Instant response generation to keep chat interaction fluid (<500ms TTFT).
- **Cost**: Generous free tier and cost-effective API pricing.
- **Instruction Following**: Strong adherence to system prompts for zero-hallucination RAG grounding.

---

## Considered Options

1. **Groq LPU Acceleration with `llama-3.1-8b-instant` (Selected)**
2. **OpenAI API (`gpt-4o-mini`)**
3. **Local Ollama / Llama.cpp**

---

## Decision Outcome

**Chosen Option**: **Groq API with Meta Llama 3.1 8B (`llama-3.1-8b-instant`)**.

### Positive Consequences
- **Ultra-Fast Token Generation**: Groq LPUs deliver ~800+ tokens/sec, resulting in near-instant response times for employees.
- **Cost Efficiency**: Free tier available with low production cost.
- **Excellent RAG Grounding**: Llama 3.1 8B strictly obeys formatting rules, system constraints, and citation requirements.

### Graceful Fallback
- If `GROQ_API_KEY` is omitted or API fails, the backend gracefully falls back to returning formatted matching source context snippets, ensuring system resilience.
