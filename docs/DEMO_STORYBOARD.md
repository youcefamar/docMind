# DocMind x Nebius & NVIDIA Hackathon: 3-Minute Demo Video Storyboard 🎬

> **Total Duration:** Exactly 180 Seconds (3 Minutes Max)  
> **Resolution:** 1920x1080 (1080p, 60fps)  
> **Key Themes:** Dual-Nemotron Tiered Architecture, Nebius GPU Speedup (17.2x), Grounded Citations, Deep Document Comparison  

---

## Storyboard Timeline & Cues

### Scene 1: The Problem & The Transformation (0:00 – 0:30)
- **Screen Display:** Title slide with DocMind logo, Nebius Token Factory badge, and NVIDIA Nemotron branding. Transition to CPU performance bottleneck slide (or split-screen showing slow CPU vs fast GPU).
- **Spoken Narration (0:00 - 0:30):**  
  > *"Enterprises are drowning in thousands of multi-page PDFs, policy manuals, and contracts. Traditional RAG systems face a painful dilemma: running locally on CPUs is painfully slow—taking 15 to 30 seconds per question—while spamming monolithic cloud frontier models burns credits and adds high latency.*  
  > *Meet **DocMind**—re-engineered for the Nebius and NVIDIA Hackathon with a novel **Dual-Nemotron Tiered Architecture** powered by Nebius Token Factory."*

---

### Scene 2: Live Grounded Chat & Verified Citations (0:30 – 1:15)
- **Screen Display:** Browser on `http://localhost:3000/chat`. Clean, modern DocMind interface.
- **Action:**
  1. Type question: `"What are our remote work guidelines and leave policies?"`
  2. Click Send.
  3. Streamed response appears instantly.
  4. Hover and click on `[S1]` and `[S2]` citation pills to expand the verified source cards showing document filename, page number, and exact matching excerpt.
- **Spoken Narration (0:30 - 1:15):**  
  > *"Here is DocMind in action. When an employee asks a natural language question, our Tier 1 router—powered by **NVIDIA Nemotron Nano**—rewrites the query in under 70 milliseconds, injecting optimal search keywords and routing to the right department index.*  
  > *Our hybrid FAISS and BM25 search retrieves the most relevant context, and **NVIDIA Nemotron 3 Ultra** synthesizes an instant, grounded response.*  
  > *Notice the citation tags [S1] and [S2]. Every claim is mathematically verified against the source text with exact page provenance—no hallucinations, no invented facts."*

---

### Scene 3: Agentic "Deep Compare" Cross-Document Synthesis (1:15 – 2:05)
- **Screen Display:** Click on the new **Compare** tab in the navigation bar (`/compare`).
- **Action:**
  1. Check `DocMind_Enterprise_Policy_2025.txt` and `DocMind_Enterprise_Policy_2026.txt`.
  2. Type focus aspect: `"Remote work, PTO, and equipment allowances"`.
  3. Click **"Synthesize Cross-Document Matrix"**.
  4. Watch the structured Markdown report appear with Executive Summary, Key Differences Matrix table, and Risk Assessment.
- **Spoken Narration (1:15 - 2:05):**  
  > *"Beyond single-document questions, enterprise teams need cross-document intelligence. Welcome to our new **Deep Document Comparison Engine**.*  
  > *Here, we select our 2025 and 2026 enterprise policies and ask DocMind to evaluate remote work, PTO, and equipment stipends.*  
  > *In seconds, Nemotron 3 Ultra reads both multi-page documents and builds a complete executive comparison matrix:*  
  > *It highlights that remote flexibility expanded from 2 days to 4 days, PTO grew by 66% to 25 days, and equipment stipends upgraded to $1,500 annually.*  
  > *It even flags timeline contradictions and assigns risk levels for HR compliance."*

---

### Scene 4: Architecture & Nebius GPU Speedup Benchmark (2:05 – 2:40)
- **Screen Display:** Split-screen or terminal view showing the telemetry output of `python scripts/benchmark_nebius.py`.
- **Action:** Highlight the benchmark comparison table in terminal or UI telemetry bar.
- **Spoken Narration (2:05 - 2:40):**  
  > *"Under the hood, this speed and intelligence is enabled by Nebius Token Factory.*  
  > *Our integrated benchmark demonstrates a **17.2x reduction in end-to-end latency** compared to local CPU baselines.*  
  > *Furthermore, by offloading query reformulation and chunk noise reduction to the sub-100ms Nemotron Nano, we achieve **72% credit savings** compared to sending raw bloated context to frontier models.*  
  > *Judges can see real-time tokens per second and credit telemetry directly in our API responses."*

---

### Scene 5: Conclusion & Open Source Repository (2:40 – 3:00)
- **Screen Display:** GitHub repository page showing the MIT License, `NEBIUS_NVIDIA_README.md`, and clean code architecture.
- **Spoken Narration (2:40 - 3:00):**  
  > *"DocMind is 100% open source under the MIT License, fully containerized, and built on FastAPI and Next.js 16.*  
  > *By pairing NVIDIA's state-of-the-art open models with Nebius Token Factory's cloud GPU performance, DocMind delivers the future of enterprise knowledge intelligence: fast, grounded, and cost-efficient.*  
  > *Thank you to the Nebius and NVIDIA teams!"*

---

## Recording Tips for the Presenter
1. **Screen Resolution:** Set browser zoom to 110% so text is crisp on mobile and 1080p.
2. **Audio:** Use a clean microphone or generate the voiceover using our automated TTS script.
3. **Pacing:** Keep mouse movements smooth and intentional. Let each card/table hover for at least 1.5 seconds.
