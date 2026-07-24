import os
from typing import List, Dict, Any, Tuple
try:
    from groq import Groq
except ImportError:
    Groq = None

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

class LLMService:
    def __init__(self, api_key: str = GROQ_API_KEY, model: str = GROQ_MODEL):
        self.api_key = api_key
        self.model = model
        self.client = Groq(api_key=api_key) if (Groq and api_key) else None

    def generate_answer(
        self, 
        question: str, 
        sources: List[Dict[str, Any]], 
        chat_history: List[Dict[str, str]] = None
    ) -> Tuple[str, float, str]:
        """
        Generates grounded answer using Groq LLM.
        Returns: (answer_text, confidence_score, confidence_label)
        """
        if not sources or len(sources) == 0:
            return (
                "I couldn't find any relevant information in the uploaded documents to answer your question.",
                0.0,
                "Low"
            )

        max_similarity = max((s.get("similarity", 0.0) for s in sources), default=0.0)

        # Build context block from sources with metadata citations
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

        # Append multi-turn history if present (last 4 messages for context)
        if chat_history:
            for msg in chat_history[-4:]:
                role = "user" if msg.get("sender") == "user" or msg.get("role") == "user" else "assistant"
                messages.append({"role": role, "content": msg.get("content", "")})

        # Append current user prompt with context
        user_message = f"DOCUMENT CONTEXT:\n{context_str}\n\nUSER QUESTION:\n{question}"
        messages.append({"role": "user", "content": user_message})

        if self.client:
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.2,
                    max_tokens=800
                )
                answer = response.choices[0].message.content.strip()
            except Exception as e:
                print(f"[LLM] Groq API call error: {e}")
                answer = self._generate_fallback_answer(question, sources)
        else:
            answer = self._generate_fallback_answer(question, sources)

        # Determine confidence score & label
        confidence_score, confidence_label = self._calculate_confidence(answer, max_similarity)

        return answer, confidence_score, confidence_label

    def _calculate_confidence(self, answer: str, max_sim: float) -> Tuple[float, str]:
        """Calculates confidence score (0.0 - 1.0) and human label."""
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
        """Fallback response generator when GROQ_API_KEY is not configured or fails."""
        first_src = sources[0]
        return (
            f"Based on **{first_src['filename']}** (Page {first_src['page_number']}):\n\n"
            f"\"{first_src['excerpt'][:350]}...\"\n\n"
            f"*(Note: Groq API key is not configured. To get full LLM synthesized answers, set GROQ_API_KEY in backend environment).* "
        )
