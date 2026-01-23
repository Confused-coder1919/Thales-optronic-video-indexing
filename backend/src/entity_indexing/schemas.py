from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class VideoCreateResponse(BaseModel):
    video_id: str
    status: str


class VideoSummary(BaseModel):
    video_id: str
    filename: str
    created_at: Optional[str] = None
    status: str
    duration_sec: Optional[float] = None
    frames_analyzed: Optional[int] = None
    entities_found: Optional[int] = None
    interval_sec: int


class VideoListResponse(BaseModel):
    items: List[VideoSummary]
    total: int
    page: int
    page_size: int


class VideoEntity(BaseModel):
    label: str
    count: int
    presence: float


class VideoDetail(BaseModel):
    video_id: str
    filename: str
    created_at: Optional[str] = None
    status: str
    duration_sec: Optional[float] = None
    interval_sec: int
    frames_analyzed: Optional[int] = None
    voice_file_included: bool
    unique_entities: Optional[int] = None
    entities: List[VideoEntity]
    report_ready: bool


class VideoStatus(BaseModel):
    status: str
    progress: float
    current_stage: Optional[str] = None
    status_text: Optional[str] = None


class FrameItem(BaseModel):
    frame_index: int
    timestamp_sec: float
    image_url: str


class FramesPage(BaseModel):
    page: int
    page_size: int
    total_frames: int
    total_pages: int
    items: List[FrameItem]


class SearchMatch(BaseModel):
    label: str
    presence: float
    frames: int


class SearchResult(BaseModel):
    video_id: str
    filename: str
    status: str
    duration_sec: Optional[float] = None
    created_at: Optional[str] = None
    matched_entities: List[SearchMatch]


class SimilarEntity(BaseModel):
    label: str
    similarity: float


class SearchResponse(BaseModel):
    exact_matches_count: int
    ai_enhancements_count: int
    total_unique_videos: int
    similar_entities: List[SimilarEntity]
    results: List[SearchResult]
