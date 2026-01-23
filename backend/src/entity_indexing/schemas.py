from __future__ import annotations

from typing import Dict, List, Optional
from pydantic import BaseModel


class VideoCreateResponse(BaseModel):
    video_id: str
    status: str
    interval_sec: int


class VideoStatus(BaseModel):
    video_id: str
    status: str
    progress: float
    current_stage: Optional[str] = None
    error: Optional[str] = None


class VideoSummary(BaseModel):
    video_id: str
    filename: str
    status: str
    duration_sec: Optional[float] = None
    interval_sec: int
    frames_analyzed: Optional[int] = None
    unique_entities: Optional[int] = None


class VideoDetail(VideoSummary):
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    report_available: bool = False
    report: Optional[Dict] = None


class FramesPage(BaseModel):
    page: int
    page_size: int
    total: int
    frames: List[Dict]


class SearchMatch(BaseModel):
    label: str
    presence: float
    frames: int


class SearchResult(BaseModel):
    video_id: str
    filename: str
    status: str
    duration_sec: Optional[float] = None
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
