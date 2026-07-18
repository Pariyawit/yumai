# 语脉 Yǔmài — your Chinese, mapped

A small personal PWA for studying Chinese lesson vocabulary. Three modes:

- **🕸 Word map** — words connect when they share a character; tap a node to grow its links.
- **🗣 Speak** — speak-first flashcards with a day-based spaced-repetition schedule (progress lives in localStorage, backup/restore built in).
- **🎵 Tones** — tone-pair drills on two-syllable words.

Pure static HTML/JS, no build step, works offline once installed (Add to Home Screen).

## Updating vocabulary

`vocab.js` is generated from a private `vocab_bank.csv` kept outside this repo:

```
python3 build_vocab.py   # rewrites vocab.js, bumps the sw.js cache version
git commit -am "vocab update" && git push
```
