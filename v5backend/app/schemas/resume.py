from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid


class UploadResponse(BaseModel):
    ids: List[str]


class ResumeMeta(BaseModel):
    id: str
    original_filename: str
    mime: str
    size: int
    status: str


class ResumeDetail(ResumeMeta):
    extracted_json: Optional[dict] = None
    scores: Optional[dict] = None


class SearchRequest(BaseModel):
    query: str
    top_k: int = Field(default=20)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=200)


class MatchRequest(BaseModel):
    job_description: str
    top_k: int = Field(default=20)


class ChatRequest(BaseModel):
    session_id: str
    message: str
    filters: Optional[dict] = None
