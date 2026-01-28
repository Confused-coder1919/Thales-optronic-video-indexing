from __future__ import annotations

import json
import uuid
import shutil
from pathlib import Path
import math
from typing import Optional

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.routing import APIRouter
from sqlalchemy import select, func

from backend.src.entity_indexing.celery_app import celery_app
from backend.src.entity_indexing.config import DEFAULT_INTERVAL_SEC, ensure_dirs
from backend.src.entity_indexing.db import SessionLocal, init_db
from backend.src.entity_indexing.embeddings import EmbeddingProvider
from backend.src.entity_indexing.models import ShareLink, Video
from backend.src.entity_indexing.report_pdf import generate_pdf
from backend.src.entity_indexing.schemas import (
    FrameItem,
    FramesPage,
    SearchResponse,
    SimilarEntity,
    VideoCreateResponse,
    VideoDetail,
    VideoEntity,
    VideoListResponse,
    VideoStatus,
    VideoSummary,
    VideoUrlRequest,
    ShareLinkResponse,
)
from backend.src.entity_indexing.search import find_similar_entities, parse_query
from backend.src.entity_indexing.storage import (
    frames_index_path,
    report_path,
    report_pdf_path,
    report_csv_path,
    transcript_path,
    video_dir,
)
from backend.src.entity_indexing.report_csv import generate_csv
from backend.src.utils.download_video import download_video_from_url, probe_video_url

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


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}


def _voice_file_included(video_id: str) -> bool:
    path = video_dir(video_id)
    return any(file.suffix.lower() == ".txt" for file in path.glob("*.txt"))


def _status_text(stage: Optional[str], voice_included: bool, status: str) -> str:
    if status == "completed":
        return "Processing complete"
    if status == "failed":
        return "Processing failed"
    voice_note = "voice file included" if voice_included else "no voice file"
    if stage == "extracting_frames":
        return "Extracting video frames"
    if stage == "transcribing_audio":
        return "Transcribing audio"
    if stage == "detecting_entities":
        return f"Analyzing video frames ({voice_note})"
    if stage == "aggregating_report":
        return "Aggregating detections into report"
    if stage == "indexing_search":
        return "Indexing entities for search"
    return "Processing video"


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
        status="processing",
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

    return VideoCreateResponse(video_id=video_id, status=video.status)


@router.post("/videos/from-url", response_model=VideoCreateResponse)
def upload_video_from_url(
    payload: VideoUrlRequest,
    session=Depends(get_session),
):
    url = (payload.url or "").strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")

    interval_sec = payload.interval_sec or DEFAULT_INTERVAL_SEC
    video_id = str(uuid.uuid4())
    dest_dir = video_dir(video_id)
    try:
        video_path, filename = download_video_from_url(url, dest_dir)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    video = Video(
        id=video_id,
        filename=filename,
        status="processing",
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

    return VideoCreateResponse(video_id=video_id, status=video.status)


@router.post("/videos/from-url-upload", response_model=VideoCreateResponse)
async def upload_video_from_url_upload(
    url: str = Form(...),
    interval_sec: int = Form(DEFAULT_INTERVAL_SEC),
    cookies_file: Optional[UploadFile] = File(None),
    session=Depends(get_session),
):
    video_id = str(uuid.uuid4())
    dest_dir = video_dir(video_id)
    cookie_path = None
    if cookies_file is not None:
        cookie_path = dest_dir / "cookies.txt"
        with open(cookie_path, "wb") as f:
            f.write(await cookies_file.read())

    try:
        video_path, filename = download_video_from_url(
            url.strip(),
            dest_dir,
            cookie_file=cookie_path,
        )
    except Exception as exc:
        if cookie_path and cookie_path.exists():
            cookie_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if cookie_path and cookie_path.exists():
        cookie_path.unlink(missing_ok=True)

    video = Video(
        id=video_id,
        filename=filename,
        status="processing",
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

    return VideoCreateResponse(video_id=video_id, status=video.status)


@router.post("/videos/from-url/check")
async def check_video_url(
    url: str = Form(...),
    cookies_file: Optional[UploadFile] = File(None),
):
    cookie_path = None
    if cookies_file is not None:
        temp_dir = Path("/tmp/entity_indexing_cookies")
        temp_dir.mkdir(parents=True, exist_ok=True)
        cookie_path = temp_dir / f"cookies_{uuid.uuid4().hex}.txt"
        with open(cookie_path, "wb") as f:
            f.write(await cookies_file.read())
    try:
        info = probe_video_url(url.strip(), cookie_file=cookie_path)
    except Exception as exc:
        if cookie_path and cookie_path.exists():
            cookie_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if cookie_path and cookie_path.exists():
        cookie_path.unlink(missing_ok=True)
    return {"ok": True, **info}




@router.get("/videos", response_model=VideoListResponse)
def list_videos(
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    session=Depends(get_session),
):
    stmt = select(Video).order_by(Video.created_at.desc())
    count_stmt = select(func.count()).select_from(Video)
    if status:
        stmt = stmt.where(Video.status == status)
        count_stmt = count_stmt.where(Video.status == status)
    total = session.execute(count_stmt).scalar_one()
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    videos = session.execute(stmt).scalars().all()
    items = [
        VideoSummary(
            video_id=video.id,
            filename=video.filename,
            created_at=video.created_at.isoformat() if video.created_at else None,
            status=video.status,
            duration_sec=video.duration_sec,
            interval_sec=video.interval_sec,
            frames_analyzed=video.frames_analyzed,
            entities_found=video.unique_entities,
        )
        for video in videos
    ]
    return VideoListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/videos/{video_id}", response_model=VideoDetail)
def get_video(video_id: str, session=Depends(get_session)):
    video = session.get(Video, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    report_ready = report_path(video_id).exists()
    entities_data = json.loads(video.entities_json) if video.entities_json else {}
    entities = sorted(
        [
        VideoEntity(
            label=label,
            count=int(data.get("count", 0)),
            presence=float(data.get("presence", 0.0)),
        )
        for label, data in entities_data.items()
    ],
        key=lambda item: item.count,
        reverse=True,
    )
    return VideoDetail(
        video_id=video.id,
        filename=video.filename,
        status=video.status,
        duration_sec=video.duration_sec,
        interval_sec=video.interval_sec,
        frames_analyzed=video.frames_analyzed,
        voice_file_included=_voice_file_included(video.id),
        unique_entities=video.unique_entities,
        entities=entities,
        report_ready=report_ready,
        created_at=video.created_at.isoformat() if video.created_at else None,
    )


@router.get("/videos/{video_id}/status", response_model=VideoStatus)
def get_video_status(video_id: str, session=Depends(get_session)):
    video = session.get(Video, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    voice_included = _voice_file_included(video.id)
    return VideoStatus(
        status=video.status,
        progress=video.progress or 0.0,
        current_stage=video.current_stage,
        status_text=_status_text(video.current_stage, voice_included, video.status),
    )


@router.get("/videos/{video_id}/report")
def get_report(video_id: str, session=Depends(get_session)):
    video = session.get(Video, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    path = report_path(video_id)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Report not ready")
    data = json.loads(path.read_text(encoding="utf-8"))
    if "video_id" not in data:
        data["video_id"] = video_id
    if "filename" not in data:
        data["filename"] = video.filename
    t_path = transcript_path(video_id)
    if t_path.exists():
        data["transcript"] = json.loads(t_path.read_text(encoding="utf-8"))
    return data


@router.post("/videos/{video_id}/share", response_model=ShareLinkResponse)
def create_share_link(video_id: str, session=Depends(get_session)):
    video = session.get(Video, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    if not report_path(video_id).exists():
        raise HTTPException(status_code=400, detail="Report not ready")

    stmt = select(ShareLink).where(ShareLink.video_id == video_id)
    existing = session.execute(stmt).scalars().first()
    if existing:
        return ShareLinkResponse(token=existing.id)

    token = str(uuid.uuid4())
    link = ShareLink(id=token, video_id=video_id)
    session.add(link)
    session.commit()
    return ShareLinkResponse(token=token)


@router.get("/share/{token}")
def get_shared_report(token: str, session=Depends(get_session)):
    link = session.get(ShareLink, token)
    if not link:
        raise HTTPException(status_code=404, detail="Share link not found")
    video = session.get(Video, link.video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    path = report_path(video.id)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Report not ready")
    data = json.loads(path.read_text(encoding="utf-8"))
    data.setdefault("video_id", video.id)
    data.setdefault("filename", video.filename)
    t_path = transcript_path(video.id)
    if t_path.exists():
        data["transcript"] = json.loads(t_path.read_text(encoding="utf-8"))
    return {
        "token": token,
        "video_id": video.id,
        "filename": video.filename,
        "created_at": video.created_at.isoformat() if video.created_at else None,
        "report": data,
    }


@router.get("/videos/{video_id}/transcript")
def get_transcript(video_id: str, session=Depends(get_session)):
    video = session.get(Video, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    path = transcript_path(video_id)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Transcript not ready")
    return json.loads(path.read_text(encoding="utf-8"))


@router.get("/videos/{video_id}/frames", response_model=FramesPage)
def get_frames(
    video_id: str,
    page: int = 1,
    page_size: int = 12,
    annotated: bool = False,
    entity: Optional[str] = None,
):
    path = frames_index_path(video_id)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Frames not ready")
    data = json.loads(path.read_text(encoding="utf-8"))
    frames = data.get("frames", [])
    if entity:
        target = entity.strip().lower()
        frames = [
            frame
            for frame in frames
            if any(
                str(det.get("label", "")).lower() == target
                for det in frame.get("detections", [])
            )
        ]
    total = len(frames)
    total_pages = math.ceil(total / page_size) if page_size else 0
    start = (page - 1) * page_size
    end = start + page_size
    sliced = frames[start:end]
    items = []
    for frame in sliced:
        frame_index = frame.get("frame_index", frame.get("index", 0))
        filename = frame.get("filename")
        if annotated:
            annotated_name = frame.get("annotated_filename")
            if annotated_name:
                candidate = frames_index_path(video_id).parent / annotated_name
                if candidate.exists():
                    filename = annotated_name
        items.append(
            FrameItem(
                frame_index=int(frame_index),
                timestamp_sec=float(frame.get("timestamp_sec", 0.0)),
                image_url=f"/api/videos/{video_id}/frames/{filename}",
            )
        )
    return FramesPage(
        page=page,
        page_size=page_size,
        total_frames=total,
        total_pages=total_pages,
        items=items,
    )


@router.get("/videos/{video_id}/frames/{frame_name:path}")
def serve_frame(video_id: str, frame_name: str):
    path = frames_index_path(video_id).parent / frame_name
    if not path.exists():
        if "annotated" in frame_name:
            fallback = frames_index_path(video_id).parent / Path(frame_name).name
            if fallback.exists():
                return FileResponse(fallback)
        raise HTTPException(status_code=404, detail="Frame not found")
    return FileResponse(path)


@router.get("/videos/{video_id}/frames/nearest")
def get_nearest_frame(
    video_id: str,
    timestamp_sec: float,
    page_size: int = 12,
    entity: Optional[str] = None,
):
    path = frames_index_path(video_id)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Frames not ready")
    data = json.loads(path.read_text(encoding="utf-8"))
    frames = data.get("frames", [])
    if entity:
        target = entity.strip().lower()
        frames = [
            frame
            for frame in frames
            if any(
                str(det.get("label", "")).lower() == target
                for det in frame.get("detections", [])
            )
        ]
    if not frames:
        raise HTTPException(status_code=404, detail="No frames available for selection")
    closest_index = 0
    closest_distance = float("inf")
    for idx, frame in enumerate(frames):
        distance = abs(float(frame.get("timestamp_sec", 0.0)) - timestamp_sec)
        if distance < closest_distance:
            closest_index = idx
            closest_distance = distance
    total = len(frames)
    total_pages = math.ceil(total / page_size) if page_size else 0
    page = int(closest_index / page_size) + 1
    item = frames[closest_index]
    filename = item.get("filename")
    return {
        "page": page,
        "page_size": page_size,
        "total_frames": total,
        "total_pages": total_pages,
        "frame_index": int(item.get("frame_index", item.get("index", 0))),
        "timestamp_sec": float(item.get("timestamp_sec", 0.0)),
        "image_url": f"/api/videos/{video_id}/frames/{filename}",
    }


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


@router.get("/videos/{video_id}/report/csv/download")
def download_report_csv(video_id: str, session=Depends(get_session)):
    video = session.get(Video, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    json_path = report_path(video_id)
    if not json_path.exists():
        raise HTTPException(status_code=404, detail="Report not found")
    csv_path = report_csv_path(video_id)
    report = json.loads(json_path.read_text(encoding="utf-8"))
    if not generate_csv(report, csv_path):
        raise HTTPException(status_code=400, detail="CSV generation failed")
    return FileResponse(csv_path, filename=f"{video_id}.csv")


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
    similar_label_set = {label.lower() for label, _ in similar_labels}

    def token_matches_label(token: str, label: str) -> bool:
        if token == label:
            return True
        if len(token) >= 3 and token in label:
            return True
        return False

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
            exact_match = any(token_matches_label(token, label_lower) for token in tokens)
            similar_match = label_lower in similar_label_set
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
                    "created_at": video.created_at.isoformat() if video.created_at else None,
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
