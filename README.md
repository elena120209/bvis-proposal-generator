---
title: BVIS Proposal Generator
emoji: 📄
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# BVIS Proposal Generator

A tiny web service that fills the **BVIS Student Council proposal PowerPoint template**
with a proposal's data and returns the finished **PPTX + PDF** (exact template styling,
because it edits the real .pptx and exports it with LibreOffice).

## API
`POST /generate`  (JSON body)

```json
{
  "event": "HALLOWEEN HOUSE FEST",
  "committee": "Social Impact Committee",
  "month": "October 2026",
  "year": "2026 – 2027",
  "date": "30–31 October 2026",
  "location": "Auditorium",
  "activities": ["Pumpkin & Pins", "Snatch the Donut"],
  "why": ["Suitable for all year groups", "..."],
  "act1_participate": ["..."], "act1_prizes": ["..."],
  "act2_participate": ["..."], "act2_prizes": ["..."],
  "timeline": ["Wk1 ...", "Wk2 ..."]
}
```
Returns: `{ "pptx_base64": "...", "pdf_base64": "...", "filename": "HALLOWEEN_HOUSE_FEST" }`

Optional security: set an env var `GEN_API_KEY`; then include `"apikey":"<same value>"` in each request.

## Deploy (free) — Hugging Face Spaces (recommended)
1. Go to huggingface.co → **New Space** → name it (e.g. `bvis-proposal-generator`) → **SDK: Docker** → **Free** hardware → Create.
2. Upload these 5 files (Add file → Upload): `Dockerfile`, `app.py`, `filler.py`, `requirements.txt`, `template.pptx`, and this `README.md`.
3. Wait ~3–5 min for it to build. Your endpoint is:  `https://<your-username>-bvis-proposal-generator.hf.space/generate`
4. Send that URL to Claude to wire into the app.

## Alternative — Render.com
New → Web Service → “Deploy from a Git repo” (put these files in a GitHub repo) → Runtime **Docker** → Free plan → Deploy.
