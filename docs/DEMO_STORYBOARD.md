# DocMind 3-Minute Demo Video Storyboard 🎬

> **Length:** Exactly 3 Minutes (180 seconds max)  
> **Resolution:** 1080p, 60fps (Browser zoom at 110% for clear text)  
> **Key Points:** Two-Tier Nemotron routing, Nebius GPU speed (17.2x faster), Clickable page citations, Side-by-side document comparison  

---

## Storyboard Timeline & Cues

### Scene 1: The Problem & The Idea (0:00 – 0:30)
- **Screen Display:** Title slide with DocMind, Nebius Token Factory, and NVIDIA Nemotron. Quick cut to terminal showing slow CPU generation.
- **Voiceover:**  
  > *"If you've ever had to dig through a 50-page company policy or figure out what changed between two versions of a contract, you know how painful it is. Running an LLM locally on a laptop takes 15 to 30 seconds for a single question. But sending everything to a massive frontier model burns through API credits and still brings back noisy text.*  
  > *For this hackathon, we rebuilt DocMind to fix both problems: using a two-tier NVIDIA Nemotron pipeline hosted on Nebius Token Factory."*

---

### Scene 2: Live Grounded Chat & Clickable Citations (0:30 – 1:15)
- **Screen Display:** Browser on `http://localhost:3000/chat`.
- **Action:**
  1. Type question: `"What are our remote work guidelines and leave policies?"`
  2. Click Send.
  3. Response streams in under a second.
  4. Click on `[S1]` and `[S2]` citation pills to expand the source cards showing document name, page number, and exact text excerpt.
- **Voiceover:**  
  > *"Here's DocMind in action. When I ask a question, our Tier 1 router—powered by NVIDIA Nemotron Nano—cleans up the query in about 68 milliseconds. It adds the best keywords for our hybrid FAISS and BM25 search.*  
  > *Then, NVIDIA Nemotron 3 Ultra synthesizes a clear, grounded answer.*  
  > *Notice these citation tags: S1 and S2. If you click one, it opens the exact document and page number where that answer came from. If the answer isn't in the docs, DocMind tells you directly instead of guessing or making things up."*

---

### Scene 3: Deep Document Comparison (`/compare`) (1:15 – 2:05)
- **Screen Display:** Click on the **Compare** tab in the top navigation bar (`/compare`).
- **Action:**
  1. Check both `DocMind_Enterprise_Policy_2025.txt` and `DocMind_Enterprise_Policy_2026.txt`.
  2. Type focus aspect: `"Remote work, PTO, and equipment allowances"`.
  3. Click **"Compare Documents"**.
  4. Scroll through the generated output: Executive Summary, Key Differences table, Contradiction Analysis, and Risk Assessment.
- **Voiceover:**  
  > *"Now here’s our favorite new feature: Deep Compare.*  
  > *Instead of manually reading two versions of an employee policy, I can select our 2025 and 2026 files, type what I want to check—like remote work, PTO, and equipment stipends—and hit Compare.*  
  > *In seconds, Nemotron 3 Ultra reads both documents and builds a side-by-side comparison matrix:*  
  > *It spots that remote work expanded from 2 days to 4 days, vacation jumped from 15 to 25 days, and the home office stipend tripled to $1,500.*  
  > *It even flags conflicting deadlines so HR and legal don't get caught off guard."*

---

### Scene 4: Under the Hood & Nebius Benchmark (2:05 – 2:40)
- **Screen Display:** Terminal running `python scripts/benchmark_nebius.py` showing latency, TTFT, and credit savings numbers.
- **Action:** Highlight the benchmark comparison table.
- **Voiceover:**  
  > *"Under the hood, all of this speed comes from Nebius Token Factory.*  
  > *On our benchmarks, this two-tier setup gave us a 17.2x speedup compared to running locally on CPU—dropping response times from 14 seconds down to 800 milliseconds.*  
  > *Even better: because Nemotron Nano filters out noisy chunks before calling the bigger model, we cut credit consumption by 72%.*  
  > *You can even see real-time latency and tokens-per-second directly in the API telemetry."*

---

### Scene 5: Conclusion & Open Source Repository (2:40 – 3:00)
- **Screen Display:** GitHub repository page showing the MIT License, `NEBIUS_NVIDIA_README.md`, and clean project structure.
- **Voiceover:**  
  > *"DocMind is 100% open source under the MIT License, built on FastAPI and Next.js 16.*  
  > *By pairing NVIDIA's open models with Nebius Token Factory's cloud GPUs, we got enterprise search that's fast, cost-efficient, and easy to trust.*  
  > *Huge thanks to the Nebius and NVIDIA teams for hosting this hackathon!"*

---

## Presenter Quick Tips
1. Keep your mouse steady and let each card or table stay visible for at least two seconds so judges can read it.
2. If you don't want to record live voice, you can use our pre-generated audio tracks in `data/profiling/audio/`.
