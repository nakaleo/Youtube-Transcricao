# CLAUDE.md

## Project Overview
YouTube Transcription Processor — downloads YouTube transcripts, translates to English via OpenAI, extracts key points/keywords via GPT-4o-mini. FastAPI backend serves a static HTML/CSS/JS frontend.

## Project Structure
- `backend/main.py` — FastAPI app, endpoints, serves static frontend at `/`
- `backend/services/transcript.py` — YouTube transcript fetching via `youtube-transcript-api`
- `backend/services/translator.py` — Translation via OpenAI (not deep-translator, it fails)
- `backend/services/processor.py` — GPT-4o-mini analysis (summary, key points, keywords)
- `backend/static/` — Frontend (vanilla HTML/CSS/JS, no build step)
- `backend/output/` — Generated files per job (gitignored)
- `.env` — `OPENAI_API_KEY` (gitignored)

## Commands
- Run server: `cd backend && uvicorn main:app --reload --port 8000`
- Install deps: `cd backend && pip install -r requirements.txt`
- Open app: `http://localhost:8000`

## Gotchas
- `youtube-transcript-api` v1.2.4+: use `ytt_api.list(video_id)` NOT `list_transcripts()`
- `deep-translator` GoogleTranslator fails with RequestError on Windows — use OpenAI for translation instead
- Windows terminal encoding: use `io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')` when testing non-Latin text in CLI
- No Node.js installed — frontend is pure HTML/CSS/JS served by FastAPI StaticFiles
- Bash shell has empty PATH — `npm`, `node`, `gh` not available; use Python tooling only
- Git identity set per-repo: user `nakaleo`, email `nakaleo@users.noreply.github.com`
- Remote: `https://github.com/nakaleo/Youtube-Transcricao.git`
