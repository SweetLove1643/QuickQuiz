from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class HealthResponse(BaseModel):
    status: str = "healthy"
    service: str
    version: str


class OCRResponse(BaseModel):
    text: str
    processing_time: float
    filename: str


class OCRMultiResponse(BaseModel):
    text: str
    processing_time: float
    num_images: int
    filenames: List[str]


# Legacy response for backward compatibility
class ExtractMultiResponse(BaseModel):
    text: str
    processing_time: float
    num_images: int


# Database schemas
class OCRRequest(BaseModel):
    id: Optional[int] = None
    filename: str
    file_size: int
    processing_time: float
    num_images: int
    extracted_text: str
    created_at: Optional[datetime] = None


class OCRStats(BaseModel):
    total_requests: int
    total_images_processed: int
    average_processing_time: float
    total_processing_time: float
