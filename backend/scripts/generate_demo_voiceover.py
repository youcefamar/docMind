"""Generate automated neural voiceover audio for the 3-minute hackathon demo video.

Uses Microsoft Edge neural text-to-speech to produce professional, human-quality
narration matching the exact storyboard cues in docs/DEMO_STORYBOARD.md.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

try:
    import edge_tts
    HAS_EDGE_TTS = True
except ImportError:
    edge_tts = None
    HAS_EDGE_TTS = False

REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO_ROOT / "data" / "profiling" / "audio"
DEFAULT_VOICE = "en-US-ChristopherNeural"  # Professional, confident broadcast voice

STORYBOARD_SEGMENTS = [
    (
        "scene1_intro",
        (
            "Enterprises are drowning in thousands of multi-page PDFs, policy manuals, and contracts. "
            "Traditional RAG systems face a painful dilemma: running locally on CPUs is painfully slow, "
            "taking 15 to 30 seconds per question, while spamming monolithic cloud frontier models burns credits and adds high latency. "
            "Meet DocMind: re-engineered for the Nebius and NVIDIA Hackathon with a novel Dual-Nemotron Tiered Architecture powered by Nebius Token Factory."
        ),
    ),
    (
        "scene2_chat",
        (
            "Here is DocMind in action. When an employee asks a natural language question, our Tier 1 router, "
            "powered by NVIDIA Nemotron Nano, rewrites the query in under 70 milliseconds, injecting optimal search keywords and routing to the right department index. "
            "Our hybrid FAISS and BM25 search retrieves the most relevant context, and NVIDIA Nemotron 3 Ultra synthesizes an instant, grounded response. "
            "Notice the citation tags S1 and S2. Every claim is mathematically verified against the source text with exact page provenance: "
            "no hallucinations, no invented facts."
        ),
    ),
    (
        "scene3_compare",
        (
            "Beyond single-document questions, enterprise teams need cross-document intelligence. "
            "Welcome to our new Deep Document Comparison Engine. "
            "Here, we select our 2025 and 2026 enterprise policies and ask DocMind to evaluate remote work, PTO, and equipment stipends. "
            "In seconds, Nemotron 3 Ultra reads both multi-page documents and builds a complete executive comparison matrix. "
            "It highlights that remote flexibility expanded from 2 days to 4 days, PTO grew by 66 percent to 25 days, and equipment stipends upgraded to $1,500 annually. "
            "It even flags timeline contradictions and assigns risk levels for HR compliance."
        ),
    ),
    (
        "scene4_benchmark",
        (
            "Under the hood, this speed and intelligence is enabled by Nebius Token Factory. "
            "Our integrated benchmark demonstrates a 17.2x reduction in end-to-end latency compared to local CPU baselines. "
            "Furthermore, by offloading query reformulation and chunk noise reduction to the sub-100 millisecond Nemotron Nano, "
            "we achieve 72 percent credit savings compared to sending raw bloated context to frontier models. "
            "Judges can see real-time tokens per second and credit telemetry directly in our API responses."
        ),
    ),
    (
        "scene5_conclusion",
        (
            "DocMind is 100 percent open source under the MIT License, fully containerized, and built on FastAPI and Next.js 16. "
            "By pairing NVIDIA's state-of-the-art open models with Nebius Token Factory's cloud GPU performance, "
            "DocMind delivers the future of enterprise knowledge intelligence: fast, grounded, and cost-efficient. "
            "Thank you to the Nebius and NVIDIA teams!"
        ),
    ),
]


async def generate_narration(voice: str = DEFAULT_VOICE) -> None:
    if not HAS_EDGE_TTS:
        print("❌ edge-tts is not installed. Run: pip install edge-tts")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    full_audio_path = OUTPUT_DIR / "demo_narration_full.mp3"

    print("=" * 70)
    print("🎙️ DocMind: Generating Automated 3-Minute Demo Voiceover")
    print(f"   Voice: {voice}")
    print(f"   Output Directory: {OUTPUT_DIR}")
    print("=" * 70)

    # 1. Generate individual scene tracks (perfect for importing into OpenShot or video editors)
    for name, script in STORYBOARD_SEGMENTS:
        scene_path = OUTPUT_DIR / f"{name}.mp3"
        print(f"Generating {name}...")
        communicate = edge_tts.Communicate(script, voice=voice, rate="+5%")
        await communicate.save(str(scene_path))
        print(f"  ✓ Saved: {scene_path.name}")

    # 2. Generate unified master track with natural pauses between scenes
    full_script = " ... \n\n ".join(text for _, text in STORYBOARD_SEGMENTS)
    print("\nGenerating full unified narration track...")
    communicate_full = edge_tts.Communicate(full_script, voice=voice, rate="+5%")
    await communicate_full.save(str(full_audio_path))
    print(f"✅ Master voiceover ready: {full_audio_path}")
    print("🎬 You can import these directly into OpenShot, Clipchamp, or use FFmpeg!")


if __name__ == "__main__":
    asyncio.run(generate_narration())
