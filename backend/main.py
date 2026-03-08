import asyncio
import os
import re
import uuid
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from services.transcript import extract_video_id, fetch_transcript
from services.translator import translate_to_english
from services.processor import process_transcript

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

app = FastAPI(title="YouTube Transcription Processor")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).resolve().parent / "static"
OUTPUT_DIR = Path(__file__).resolve().parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# In-memory job storage
jobs: dict[str, dict] = {}


class ProcessRequest(BaseModel):
    urls: list[str]


class JobStatus(BaseModel):
    job_id: str
    videos: list[dict]


def sanitize_filename(name: str) -> str:
    name = re.sub(r'[<>:"/\\|?*]', '_', name)
    name = name.strip('. ')
    return name[:100] if len(name) > 100 else name


async def process_single_video(job_id: str, index: int, url: str):
    video = jobs[job_id]["videos"][index]
    try:
        # Step 1: Download transcript
        video["status"] = "downloading"
        video_id = extract_video_id(url)
        result = await asyncio.to_thread(fetch_transcript, video_id)

        video["title"] = result["title"]
        transcript_text = result["text"]
        original_lang = result["language"]

        # Step 2: Translate if needed
        if not original_lang.startswith("en"):
            video["status"] = "translating"
            transcript_text = await asyncio.to_thread(
                translate_to_english, transcript_text, original_lang
            )

        # Step 3: Save full transcript
        safe_title = sanitize_filename(result["title"])
        job_dir = OUTPUT_DIR / job_id
        job_dir.mkdir(exist_ok=True)

        full_filename = f"{safe_title}_full_transcript.txt"
        full_path = job_dir / full_filename
        full_path.write_text(transcript_text, encoding="utf-8")

        # Step 4: Process with OpenAI
        video["status"] = "processing"
        processed_text = await asyncio.to_thread(
            process_transcript, transcript_text, result["title"]
        )

        processed_filename = f"{safe_title}_processed.txt"
        processed_path = job_dir / processed_filename
        processed_path.write_text(processed_text, encoding="utf-8")

        video["status"] = "done"
        video["files"] = {
            "full": full_filename,
            "processed": processed_filename,
        }

    except Exception as e:
        video["status"] = "error"
        video["error"] = str(e)


@app.post("/api/process")
async def start_processing(request: ProcessRequest):
    if len(request.urls) > 15:
        raise HTTPException(status_code=400, detail="Maximum 15 URLs allowed")

    if not request.urls:
        raise HTTPException(status_code=400, detail="At least one URL is required")

    job_id = str(uuid.uuid4())[:8]
    jobs[job_id] = {
        "videos": [
            {"url": url, "title": "", "status": "pending", "error": None, "files": None}
            for url in request.urls
        ]
    }

    # Launch all video processing tasks
    for i, url in enumerate(request.urls):
        asyncio.create_task(process_single_video(job_id, i, url))

    return {"job_id": job_id}


@app.get("/api/status/{job_id}")
async def get_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"job_id": job_id, "videos": jobs[job_id]["videos"]}


@app.get("/api/download/{job_id}/{filename}")
async def download_file(job_id: str, filename: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    file_path = OUTPUT_DIR / job_id / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="text/plain",
    )


@app.get("/")
async def serve_frontend():
    return HTMLResponse((STATIC_DIR / "index.html").read_text(encoding="utf-8"))
