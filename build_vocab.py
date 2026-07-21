#!/usr/bin/env python3
"""Regenerate vocab.js for the Yǔmài app from ../vocab_bank.csv.

Run after appending a lesson's words to vocab_bank.csv:

    python3 build_vocab.py

Also stamps a content-hash CACHE_VERSION into sw.js so installed
clients (PWA) pick up the new vocab on their next visit.
"""

import csv
import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
CSV_PATH = HERE.parent / "vocab_bank.csv"
HOMEWORK_DIR = HERE.parent / "homework"
VOCAB_JS = HERE / "vocab.js"
SW_JS = HERE / "sw.js"


def theme_from_source(source: str) -> str:
    """'2025-10-18_FreeFoodFromFriend_Notes.docx' -> 'Free Food From Friend'"""
    stem = Path(source).stem
    parts = stem.split("_")
    topic = "".join(p for p in parts if not re.fullmatch(r"\d{4}-\d{2}-\d{2}|Notes|Homework|Review", p))
    words = re.findall(r"[A-Z][a-z0-9]*|[a-z0-9]+", topic)
    return " ".join(words) or stem


def load_homework() -> dict:
    """Map (class_date, hanzi) -> {example_zh, example_pinyin, breakdown} from homework JSONs."""
    extras = {}
    for path in sorted(HOMEWORK_DIR.glob("*_content.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        date = data.get("class_date") or path.name[:10]
        for w in data.get("new_words", []):
            fields = {k: w[k].strip() for k in ("example_zh", "example_pinyin", "breakdown") if w.get(k, "").strip()}
            if fields:
                extras[(date, w["hanzi"].strip())] = fields
    return extras


def main() -> None:
    extras = load_homework() if HOMEWORK_DIR.is_dir() else {}
    n_files = len(list(HOMEWORK_DIR.glob("*_content.json"))) if HOMEWORK_DIR.is_dir() else 0
    unmatched = set(extras)

    rows = []
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            entry = {
                "hanzi": row["hanzi"].strip(),
                "pinyin": row["pinyin"].strip(),
                "english": row["english"].strip(),
                "date": row["date"].strip(),
                "theme": theme_from_source(row["source"].strip()),
            }
            key = (entry["date"], entry["hanzi"])
            if key in extras:
                entry.update(extras[key])
                unmatched.discard(key)
            rows.append(entry)

    if unmatched:
        print(f"Warning: {len(unmatched)} homework words not in vocab_bank.csv: "
              + ", ".join(f"{h} ({d})" for d, h in sorted(unmatched)))

    payload = "const VOCAB = " + json.dumps(rows, ensure_ascii=False) + ";\n"
    VOCAB_JS.write_text(payload, encoding="utf-8")
    enriched = sum(1 for r in rows if "example_zh" in r or "breakdown" in r)
    print(f"Wrote {VOCAB_JS.name}: {len(rows)} words, {len({r['theme'] for r in rows})} themes, "
          f"{enriched} enriched from {n_files} homework files")

    if SW_JS.exists():
        version = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:10]
        sw = SW_JS.read_text(encoding="utf-8")
        sw_new = re.sub(r"const CACHE_VERSION = '[^']*'", f"const CACHE_VERSION = '{version}'", sw)
        if sw != sw_new:
            SW_JS.write_text(sw_new, encoding="utf-8")
            print(f"Bumped sw.js CACHE_VERSION -> {version}")
    else:
        print("sw.js not found; skipped cache-version bump")


if __name__ == "__main__":
    main()
