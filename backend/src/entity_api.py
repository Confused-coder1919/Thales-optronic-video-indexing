from __future__ import annotations

import json
import uuid
import shutil
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.routing import APIRouter
from sqlalchemy import select

from backend.src.entity_indexing.celery_app import celery_app
from backend.src.entity_indexing.config import DEFAULT_INTERVAL_SEC, ensure_dirs
from backend.src.entity_indexing.db import SessionLocal, init_db
from backend.src.entity_indexing.embeddings import EmbeddingProvider
from backend.src.entity_indexing.models import Video
from backend.src.entity_indexing.report_pdf import generate_pdf
from backend.src.entity_indexing.schemas import (
    FramesPage,
    SearchResponse,
    SimilarEntity,
    VideoCreateResponse,
    VideoDetail,
    VideoStatus,
    VideoSummary,
)
from backend.src.entity_indexing.search import find_similar_entities, parse_query
from backend.src.entity_indexing.storage import (
    frames_index_path,
    report_path,
    report_pdf_path,
    video_dir,
)

app = FastAPI(title="Entity Indexing API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter(prefix="/api")


def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@app.on_event("startup")
def startup() -> None:
    ensure_dirs()
    init_db()


@router.post("/videos", response_model=VideoCreateResponse)
async def upload_video(
    video_file: UploadFile = File(...),
    voice_file: Optional[UploadFile] = File(None),
    interval_sec: int = Form(DEFAULT_INTERVAL_SEC),
    session=Depends(get_session),
):
    video_id = str(uuid.uuid4())
    dest_dir = video_dir(video_id)
    video_path = dest_dir / video_file.filename
    with open(video_path, "wb") as f:
        f.write(await video_file.read())

    if voice_file is not None:
        voice_path = dest_dir / voice_file.filename
        with open(voice_path, "wb") as f:
            f.write(await voice_file.read())

    video = Video(
        id=video_id,
        filename=video_file.filename,
        status="queued",
        progress=0.0,
        current_stage="queued",
        interval_sec=interval_sec,
        original_path=str(video_path),
    )
    session.add(video)
    session.commit()

    celery_app.send_task(
        "entity_indexing.process_video", args=[video_id, str(video_path), interval_sec]
    )

    return VideoCreateResponse(video_id=video_id, status=video.status, interval_sec=interval_sec)


@router.get("/videos", response_model=list[VideoSummary])
def list_videos(
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    session=Depends(get_session),
):
    stmt = select(Video)
    if status:
        stmt = stmt.where(Video.status == status)
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    videos = session.execute(stmt).scalars().all()
    return [
        VideoSummary(
            video_id=video.id,
            filename=video.filename,
            status=video.status,
            duration_sec=video.duration_sec,
            interval_sec=video.interval_sec,
            frames_analyzed=video.frames_analyzed,
            unique_entities=video.unique_entities,
        )
        for video in videos
    ]


@router.get("/videos/{video_id}", response_model=VideoDetail)
def get_video(video_id: str, session=Depends(get_session)):
    video = session.get(Video, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    report_available = report_path(video_id).exists()
    report_data = None
    if report_available:
        report_data = json.loads(report_path(video_id).read_text(encoding="utf-8"))
    return VideoDetail(
        video_id=video.id,
        filename=video.filename,
        status=video.status,
        duration_sec=video.duration_sec,
        interval_sec=video.interval_sec,
        frames_analyzed=video.frames_analyzed,
        unique_entities=video.unique_entities,
        report_available=report_available,
        report=report_data,
        created_at=video.created_at.isoformat() if video.created_at else None,
        updated_at=video.updated_at.isoformat() if video.updated_at else None,
    )


@router.get("/videos/{video_id}/status", response_model=VideoStatus)
def get_video_status(video_id: str, session=Depends(get_session)):
    video = session.get(Video, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return VideoStatus(
        video_id=video.id,
        status=video.status,
        progress=video.progress or 0.0,
        current_stage=video.current_stage,
        error=video.error,
    )


@router.get("/videos/{video_id}/report")
def get_report(video_id: str, session=Depends(get_session)):
    video = session.get(Video, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    path = report_path(video_id)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Report not ready")
    return json.loads(path.read_text(encoding="utf-8"))


@router.get("/videos/{video_id}/frames", response_model=FramesPage)
def get_frames(video_id: str, page: int = 1, page_size: int = 24):
    path = frames_index_path(video_id)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Frames not ready")
    data = json.loads(path.read_text(encoding="utf-8"))
    frames = data.get("frames", [])
    total = len(frames)
    start = (page - 1) * page_size
    end = start + page_size
    sliced = frames[start:end]
    for frame in sliced:
        frame["url"] = f"/api/videos/{video_id}/frames/{frame['filename']}"
    return FramesPage(page=page, page_size=page_size, total=total, frames=sliced)


@router.get("/videos/{video_id}/frames/{frame_name}")
def serve_frame(video_id: str, frame_name: str):
    path = frames_index_path(video_id).parent / frame_name
    if not path.exists():
        raise HTTPException(status_code=404, detail="Frame not found")
    return FileResponse(path)


@router.get("/videos/{video_id}/download")
def download_video(video_id: str, session=Depends(get_session)):
    video = session.get(Video, video_id)
    if not video or not video.original_path:
        raise HTTPException(status_code=404, detail="Video not found")
    return FileResponse(video.original_path, filename=video.filename)


@router.get("/videos/{video_id}/report/download")
def download_report(video_id: str, format: str = "json"):
    json_path = report_path(video_id)
    if not json_path.exists():
        raise HTTPException(status_code=404, detail="Report not found")
    if format == "pdf":
        pdf_path = report_pdf_path(video_id)
        if not pdf_path.exists():
            report = json.loads(json_path.read_text(encoding="utf-8"))
            if not generate_pdf(report, pdf_path):
                raise HTTPException(status_code=400, detail="PDF generation not available")
        return FileResponse(pdf_path, filename=f"{video_id}.pdf")
    return FileResponse(json_path, filename=f"{video_id}.json")


@router.delete("/videos/{video_id}")
def delete_video(video_id: str, session=Depends(get_session)):
    video = session.get(Video, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    for path in [
        Path(video.original_path).parent if video.original_path else None,
        frames_index_path(video_id).parent,
        report_path(video_id).parent,
    ]:
        if path and path.exists():
            shutil.rmtree(path, ignore_errors=True)
    session.delete(video)
    session.commit()
    return {"status": "deleted"}


@router.get("/search", response_model=SearchResponse)
def search_entities(
    q: str,
    similarity: float = 0.7,
    min_presence: float = 0.0,
    min_frames: int = 0,
    session=Depends(get_session),
):
    if not q.strip():
        return SearchResponse(
            exact_matches_count=0,
            ai_enhancements_count=0,
            total_unique_videos=0,
            similar_entities=[],
            results=[],
        )
    tokens = parse_query(q)
    provider = EmbeddingProvider()
    similar_labels = find_similar_entities(q, similarity, provider)
    exact_found = set()

    stmt = select(Video).where(Video.status == "completed")
    videos = session.execute(stmt).scalars().all()

    results = []
    for video in videos:
        if not video.entities_json:
            continue
        entities = json.loads(video.entities_json)
        matched = []
        for label, data in entities.items():
            label_lower = label.lower()
            exact_match = any(token == label_lower for token in tokens)
            similar_match = any(label == sim_label for sim_label, _ in similar_labels)
            if exact_match or similar_match:
                presence = data.get("presence", 0.0)
                count = data.get("count", 0)
                if presence < min_presence or count < min_frames:
                    continue
                if exact_match:
                    exact_found.add(label_lower)
                matched.append(
                    {
                        "label": label,
                        "presence": presence,
                        "frames": count,
                    }
                )
        if matched:
            results.append(
                {
                    "video_id": video.id,
                    "filename": video.filename,
                    "status": video.status,
                    "duration_sec": video.duration_sec,
                    "matched_entities": matched,
                }
            )

    similar_entities = [
        SimilarEntity(label=label, similarity=round(score, 4))
        for label, score in similar_labels
    ]

    return SearchResponse(
        exact_matches_count=len(exact_found),
        ai_enhancements_count=len(similar_entities),
        total_unique_videos=len(results),
        similar_entities=similar_entities,
        results=results,
    )


app.include_router(router)
