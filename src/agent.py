# src/agent.py — Ollama-only summarizer (structured, faster, Windows-safe)

import os
import sys
import json
import time
from pathlib import Path
from urllib.request import urlopen
from dotenv import load_dotenv

# Third-party
import ollama

# ---------- Config & .env ----------
ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT / ".env"
if ENV_PATH.exists():
    load_dotenv(ENV_PATH, override=True)

MODEL = os.getenv("MODEL", "phi3:mini")
# Keep inputs modest for small local models (speed + quality)
MAX_CHARS = int(os.getenv("MAX_CHARS", "1800"))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "256"))

# ---------- Connectivity helpers ----------
def ping_ollama(timeout=5) -> bool:
    """Return True if the Ollama server responds on localhost:11434."""
    url = "http://localhost:11434/api/tags"
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urlopen(url, timeout=2) as r:
                if r.status == 200:
                    return True
        except Exception:
            time.sleep(0.25)
    return False

def ensure_model(model: str) -> bool:
    """Return True if the model is present locally, else print a hint."""
    try:
        tags = ollama.list()
        names = [m.get("model") for m in tags.get("models", [])]
        if model not in names:
            print(f"Model '{model}' not found locally. Pull it first:\n  ollama pull {model}")
            return False
        return True
    except Exception as e:
        print(f"Could not query Ollama models: {e}")
        return False

# ---------- Summarization ----------
def summarize_text(text: str, section_name: str) -> str:
    """
    Summarize text into 3–5 bullets. Tries JSON-structured output; falls back to raw.
    Returns a bullet list string suitable for display.
    """
    snippet = (text or "")[:MAX_CHARS]

    prompt = (
        "You are a careful summarizer. ONLY use the given text.\n"
        "Return JSON with keys: 'section', 'bullets'.\n"
        f"section must equal '{section_name}'.\n"
        "bullets must be 3-5 short, factual bullet points. Include concrete names, metrics, dates if present.\n"
        "If the text has no useful content, set bullets to ['No salient content in this section.']\n\n"
        f"TEXT:\n{snippet}"
    )

    try:
        resp = ollama.chat(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            options={
                "temperature": 0.2,
                "num_ctx": 3072,       # modest context helps small models
                "num_predict": MAX_TOKENS
            },
        )
        raw = (resp["message"]["content"] or "").strip()
    except Exception as e:
        print(f"Error summarizing {section_name}: {e}")
        return ""

    # Try to parse JSON; if not JSON, fallback to raw text
    try:
        data = json.loads(raw)
        if isinstance(data, dict) and "bullets" in data and isinstance(data["bullets"], list):
            bullets = [str(b).strip() for b in data["bullets"] if str(b).strip()]
            if not bullets:
                bullets = ["No salient content in this section."]
            return "\n".join(f"• {b}" for b in bullets)
    except Exception:
        pass

    # Fallback: ensure it's not empty
    return raw if raw else "No salient content in this section."

# ---------- CLI entry point ----------
if __name__ == "__main__":
    # Optional arg: run name (matches your processed folder), defaults to 'sample'
    run_name = sys.argv[1] if len(sys.argv) >= 2 else "sample"

    input_dir = ROOT / f"data/processed/{run_name}"
    output_dir = ROOT / f"data/summaries/{run_name}"
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Backend: Ollama | Model: {MODEL}")

    if not ping_ollama():
        print("Ollama server not reachable at http://localhost:11434")
        print("Open a Command Prompt and run:  ollama serve   (or ensure the service is running)")
        sys.exit(1)

    if not ensure_model(MODEL):
        sys.exit(1)

    files = sorted(input_dir.glob("*.txt"))
    if not files:
        print(f"No input files found in: {input_dir}. Run segmenter first.")
        sys.exit(1)

    print(f"Found {len(files)} section files. Summarizing...")
    for i, file in enumerate(files, 1):
        print(f"[{i}/{len(files)}] {file.name} ...", end="", flush=True)
        try:
            text = file.read_text(encoding="utf-8", errors="ignore")
            summary = summarize_text(text, section_name=file.stem)
            out_path = output_dir / file.name
            out_path.write_text(summary, encoding="utf-8")
            print(" done")
        except Exception as e:
            print(f" error: {e}")
