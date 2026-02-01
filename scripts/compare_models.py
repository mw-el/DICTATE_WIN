#!/usr/bin/env python3
import os
import json
import time
import gc
from pathlib import Path

os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

from faster_whisper import WhisperModel
from faster_whisper.utils import download_model

ROOT = Path(__file__).resolve().parents[1]
MODELS_DIR = ROOT / "models"
AUDIO_DIR = Path.home() / "Music" / "dictate"

LANG_MAP = {
    "DE-DE": "de",
    "DE-CH": "de",
    "EN": "en",
}


def find_latest_audio():
    files = list(AUDIO_DIR.glob("*.mp3")) + list(AUDIO_DIR.glob("*.wav"))
    if not files:
        return None
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0]


def get_language_code():
    cfg_path = Path.home() / ".config" / "dictate" / "config.json"
    if not cfg_path.exists():
        return None
    try:
        with cfg_path.open("r", encoding="utf-8") as f:
            cfg = json.load(f)
        return LANG_MAP.get(cfg.get("language", "").upper())
    except Exception:
        return None


def wer(ref, hyp):
    ref_words = ref.split()
    hyp_words = hyp.split()
    if not ref_words:
        return 0.0 if not hyp_words else 1.0
    n = len(ref_words)
    m = len(hyp_words)
    dp = list(range(m + 1))
    for i in range(1, n + 1):
        prev = dp[0]
        dp[0] = i
        for j in range(1, m + 1):
            tmp = dp[j]
            cost = 0 if ref_words[i - 1] == hyp_words[j - 1] else 1
            dp[j] = min(
                dp[j] + 1,      # deletion
                dp[j - 1] + 1,  # insertion
                prev + cost     # substitution
            )
            prev = tmp
    return dp[m] / max(1, n)


def ensure_model(model_name, size_or_id):
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    out_dir = MODELS_DIR / model_name
    if not out_dir.exists() or not any(out_dir.iterdir()):
        download_model(size_or_id, output_dir=str(out_dir))
    return str(out_dir)


def main():
    audio_path = find_latest_audio()
    if not audio_path:
        raise SystemExit(f"No audio files found in {AUDIO_DIR}")

    language = get_language_code()

    models = [
        ("base", "base"),
        ("small", "small"),
        ("large-v3-turbo", "mobiuslabsgmbh/faster-whisper-large-v3-turbo"),
        ("large-v3", "large-v3"),
    ]

    results = []

    print(f"Audio: {audio_path}")
    print(f"Language: {language or 'auto'}")
    print("")

    for name, size_or_id in models:
        print(f"=== {name} ===")
        model_source = ensure_model(name, size_or_id)
        t0 = time.time()
        model = WhisperModel(model_source, device="cpu", compute_type="float32")
        t1 = time.time()
        segments, info = model.transcribe(
            str(audio_path),
            language=language,
            beam_size=5,
            condition_on_previous_text=False
        )
        text = "".join(seg.text for seg in segments).strip()
        t2 = time.time()
        results.append({
            "model": name,
            "load_s": t1 - t0,
            "transcribe_s": t2 - t1,
            "total_s": t2 - t0,
            "text": text,
        })
        del model
        gc.collect()

    ref = next((r for r in results if r["model"] == "large-v3"), None)
    if not ref:
        raise SystemExit("large-v3 result missing; cannot compute deviations.")

    print("")
    print("Model\tLoad_s\tTranscribe_s\tTotal_s\tWER_vs_large_v3")
    for r in results:
        w = wer(ref["text"].lower(), r["text"].lower())
        print(
            f"{r['model']}\t"
            f"{r['load_s']:.2f}\t"
            f"{r['transcribe_s']:.2f}\t"
            f"{r['total_s']:.2f}\t"
            f"{w*100:.1f}%"
        )


if __name__ == "__main__":
    main()
