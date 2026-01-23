from __future__ import annotations

from sqlalchemy import Column, String, Float, Integer, DateTime, Text
from sqlalchemy.sql import func

from .db import Base


class Video(Base):
    __tablename__ = "videos"

    id = Column(String, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    status = Column(String, nullable=False, default="queued")
    progress = Column(Float, nullable=False, default=0.0)
    current_stage = Column(String, nullable=True)
    duration_sec = Column(Float, nullable=True)
    interval_sec = Column(Integer, nullable=False, default=5)
    frames_analyzed = Column(Integer, nullable=True)
    unique_entities = Column(Integer, nullable=True)
    entities_json = Column(Text, nullable=True)
    report_path = Column(String, nullable=True)
    frames_path = Column(String, nullable=True)
    original_path = Column(String, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
