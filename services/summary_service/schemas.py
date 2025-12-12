from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class HealthResponse(BaseModel):
    status: str = "healthy"
    service: str
    version: str


class SummaryResponse(BaseModel):
    summary: str
    input_type: str
    word_count: int
    processing_time: Optional[float] = None


class OCRSummaryResponse(BaseModel):
    extracted_text: str
    summary: str
    num_files: int
    filenames: List[str]
    word_count: int
    processing_time: Optional[float] = None


class RecommendationResponse(BaseModel):
    recommendations: Dict[str, Any]
    content_length: int
    difficulty_level: str
    estimated_study_time: int


class SummaryRequestModel(BaseModel):
    text: str
    summary_type: Optional[str] = "general"
    max_length: Optional[int] = 500


class RecommendRequest(BaseModel):
    content: str
    difficulty_level: Optional[str] = "intermediate"
    study_time: Optional[int] = 60
    subject: Optional[str] = None


# Database schemas
class SummaryRequest(BaseModel):
    id: Optional[int] = None
    content_type: str  # "text", "ocr", "file"
    input_text: str
    summary: str
    processing_method: str
    num_files: Optional[int] = None
    processing_time: Optional[float] = None
    created_at: Optional[datetime] = None


class SummaryStats(BaseModel):
    total_requests: int
    total_text_processed: int
    average_processing_time: float
    summary_types: Dict[str, int]
