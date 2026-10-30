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
            "If you've ever had to dig through a 50-page company policy or figure out what changed between two versions of a contract, "
            "you know how painful it is. Running an LLM locally on a laptop takes 15 to 30 seconds for a single question. "
            "But sending everything to a massive frontier model burns through API credits and still brings back noisy text. "
            "For this hackathon, we rebuilt DocMind to fix both problems: using a two-tier NVIDIA Nemotron pipeline hosted on Nebius Token Factory."
        ),
    ),
    (
        "scene2_chat",
        (
            "Here's DocMind in action. When I ask a question, our Tier 1 router, powered by NVIDIA Nemotron Nano, "
            "cleans up the query in about 68 milliseconds. It adds the best keywords for our hybrid FAISS and BM25 search. "
            "Then, NVIDIA Nemotron 3 Ultra synthesizes a clear, grounded answer. "
            "Notice these citation tags: S1 and S2. If you click one, it opens the exact document and page number where that answer came from. "
            "If the answer isn't in the docs, DocMind tells you directly instead of guessing or making things up."
        ),
    ),
    (
        "scene3_compare",
        (
            "Now here's our favorite new feature: Deep Compare. "
            "Instead of manually reading two versions of an employee policy, I can select our 2025 and 2026 files, "
            "type what I want to check—like remote work, PTO, and equipment stipends—and hit Compare. "
            "In seconds, Nemotron 3 Ultra reads both documents and builds a side-by-side comparison matrix: "
            "It spots that remote work expanded from 2 days to 4 days, vacation jumped from 15 to 25 days, and the home office stipend tripled to $1,500. "
            "It even flags conflicting deadlines so HR and legal don't get caught off guard."
        ),
    ),
    (
        "scene4_benchmark",
        (
            "Under the hood, all of this speed comes from Nebius Token Factory. "
            "On our benchmarks, this two-tier setup gave us a 17.2x speedup compared to running locally on CPU, "
            "dropping response times from 14 seconds down to 800 milliseconds. "
            "Even better: because Nemotron Nano filters out noisy chunks before calling the bigger model, we cut credit consumption by 72%. "
            "You can even see real-time latency and tokens-per-second directly in the API telemetry."
        ),
    ),
    (
        "scene5_conclusion",
        (
            "DocMind is 100 percent open source under the MIT License, built on FastAPI and Next.js 16. "
            "By pairing NVIDIA's open models with Nebius Token Factory's cloud GPUs, we got enterprise search that's fast, cost-efficient, and easy to trust. "
            "Huge thanks to the Nebius and NVIDIA teams for hosting this hackathon!"
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
