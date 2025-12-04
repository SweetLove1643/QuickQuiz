from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class Section(BaseModel):
    id: str
    summary: str


class QuizConfig(BaseModel):
    n_questions: int = Field(default=5, ge=1)
    types: List[str] = Field(default_factory=lambda: ["mcq", "tf", "fill_blank"])
    difficulty: Optional[Dict[str, float]] = None


class GenerateRequest(BaseModel):
    document_id: Optional[str] = None
    sections: Optional[List[Section]] = None
    config: Optional[QuizConfig] = None


class QuizQuestion(BaseModel):
    id: str
    type: str
    stem: str
    options: Optional[List[str]] = None
    answer: Optional[str] = None
    difficulty: Optional[str] = None
    source_sections: Optional[List[str]] = None


class Quiz(BaseModel):
    id: str
    questions: List[QuizQuestion]
    meta: Optional[Dict] = None


__all__ = ["Section", "QuizConfig", "GenerateRequest", "QuizQuestion", "Quiz"]
