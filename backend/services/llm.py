import os
from typing import List, Dict, Any, Tuple

# Try loading local llama-cpp-python for GGUF execution
try:
    from llama_cpp import Llama
    HAS_LLAMA_CPP = True
except ImportError:
    Llama = None
    HAS_LLAMA_CPP = False

# Try Groq API as secondary provider if configured
try:
    from groq import Groq
    HAS_GROQ = True
except ImportError:
    Groq = None
    HAS_GROQ = False

GGUF_MODEL_PATH = os.getenv("GGUF_MODEL_PATH", os.path.join(os.path.dirname(__file__), "..", "models", "llama-3.1-8b-instruct.Q4_K_M.gguf"))
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

class LLMService:
    def __init__(self, model_path: str = GGUF_MODEL_PATH):
        self.model_path = model_path
        self.local_llm = None
        self.groq_client = None

        # 1. Initialize Local GGUF Model if file exists and llama-cpp-python is available
        if HAS_LLAMA_CPP and os.path.exists(self.model_path):
            print(f"[LLM] Loading local GGUF model from: {self.model_path}")
            try:
                self.local_llm = Llama(
                    model_path=self.model_path,
                    n_ctx=4096,
                    n_threads=os.cpu_count() or 4,
                    verbose=False
                )
                print("[LLM] Local GGUF model loaded successfully!")
            except Exception as e:
                print(f"[LLM] Error loading local GGUF model: {e}")
                self.local_llm = None
        
        # 2. Fallback to Groq API if local GGUF is not found and Groq API key is present
        if not self.local_llm and HAS_GROQ and GROQ_API_KEY:
            try:
                self.groq_client = Groq(api_key=GROQ_API_KEY)
                print("[LLM] Configured Groq API client as LLM provider.")
            except Exception as e:
                print(f"[LLM] Error initializing Groq client: {e}")

    def generate_answer(
        self, 
        question: str, 
        sources: List[Dict[str, Any]], 
        chat_history: List[Dict[str, str]] = None
    ) -> Tuple[str, float, str]:
        """
        Generates grounded answer using local .gguf model or Groq LLM.
        Returns: (answer_text, confidence_score, confidence_label)
        """
        if not sources or len(sources) == 0:
            return (
                "I couldn't find any relevant information in the uploaded documents to answer your question.",
                0.0,
                "Low"
            )

        max_similarity = max((s.get("similarity", 0.0) for s in sources), default=0.0)

        # Build context block from sources
        context_blocks = []
        for idx, src in enumerate(sources, start=1):
            context_blocks.append(
                f"--- SOURCE [{idx}] ---\n"
                f"Document: {src.get('filename')}\n"
                f"Category: {src.get('category')}\n"
                f"Page: {src.get('page_number')}\n"
                f"Content:\n{src.get('excerpt')}\n"
            )
        
        context_str = "\n".join(context_blocks)

        system_prompt = (
            "You are DocMind, an intelligent and precise internal knowledge assistant for enterprise document search.\n"
            "Your task is to answer the employee's question using ONLY the provided document sources.\n\n"
            "STRICT RULES:\n"
            "1. Base your answer strictly on the context provided. Do NOT assume or hallucinate outside information.\n"
            "2. If the context does NOT contain enough information to answer the question, explicitly state: "
            "\"I don't know based on the provided documents.\"\n"
            "3. Cite the relevant document source name and page number whenever making specific statements.\n"
            "4. Keep your answers concise, professional, and clear.\n"
        )

        messages = [{"role": "system", "content": system_prompt}]

        if chat_history:
            for msg in chat_history[-4:]:
                role = "user" if msg.get("sender") == "user" or msg.get("role") == "user" else "assistant"
                messages.append({"role": role, "content": msg.get("content", "")})

        user_message = f"DOCUMENT CONTEXT:\n{context_str}\n\nUSER QUESTION:\n{question}"
        messages.append({"role": "user", "content": user_message})

        answer = ""

        # Option A: Local GGUF execution via llama-cpp-python
        if self.local_llm:
            try:
                response = self.local_llm.create_chat_completion(
                    messages=messages,
                    temperature=0.2,
                    max_tokens=600
                )
                answer = response["choices"][0]["message"]["content"].strip()
            except Exception as e:
                print(f"[LLM] Local GGUF generation error: {e}")
                answer = self._generate_fallback_answer(question, sources)

        # Option B: Groq API execution
        elif self.groq_client:
            try:
                response = self.groq_client.chat.completions.create(
                    model=GROQ_MODEL,
                    messages=messages,
                    temperature=0.2,
                    max_tokens=800
                )
                answer = response.choices[0].message.content.strip()
            except Exception as e:
                print(f"[LLM] Groq API call error: {e}")
                answer = self._generate_fallback_answer(question, sources)
        
        # Option C: Direct Context Fallback
        else:
            answer = self._generate_fallback_answer(question, sources)

        confidence_score, confidence_label = self._calculate_confidence(answer, max_similarity)
        return answer, confidence_score, confidence_label

    def _calculate_confidence(self, answer: str, max_sim: float) -> Tuple[float, str]:
        lower_ans = answer.lower()
        if "i don't know" in lower_ans or "couldn't find" in lower_ans or "not mentioned" in lower_ans:
            return 0.15, "Low"

        if max_sim >= 0.70:
            return min(0.98, max_sim + 0.05), "High"
        elif max_sim >= 0.45:
            return round(max_sim, 2), "Medium"
        else:
            return round(max_sim, 2), "Low"

    def _generate_fallback_answer(self, question: str, sources: List[Dict[str, Any]]) -> str:
        first_src = sources[0]
        return (
            f"Based on **{first_src['filename']}** (Page {first_src['page_number']}):\n\n"
            f"\"{first_src['excerpt'][:350]}...\"\n\n"
            f"*(Note: Place your local `.gguf` model file in `backend/models/` or set `GGUF_MODEL_PATH` in .env to enable full local LLM synthesis).* "
        )
