from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class QuestionType(str, Enum):

    mcq = "mcq"
    tf = "tf"
    fill_blank = "fill_blank"


class Grade(str, Enum):

    A = "A"  # 90-100%
    B = "B"  # 80-89%
    C = "C"  # 70-79%
    D = "D"  # 60-69%
    F = "F"  # <60%


class UserQuestion(BaseModel):

    id: str
    type: QuestionType
    stem: str
    options: Optional[List[str]] = None
    correct_answer: str
    user_answer: Optional[str] = None
    topic: Optional[str] = None
    difficulty: Optional[str] = None
    source_sections: Optional[List[str]] = None


class UserInfo(BaseModel):

    user_id: Optional[str] = None
    completion_time: Optional[int] = None 
    timestamp: datetime = Field(default_factory=datetime.now)
    session_id: Optional[str] = None


class QuizSubmission(BaseModel):

    quiz_id: str
    questions: List[UserQuestion]
    user_info: Optional[UserInfo] = None
    config: Optional[Dict[str, Any]] = None


class QuestionResult(BaseModel):

    question_id: str
    is_correct: bool
    topic: Optional[str] = None
    question_type: QuestionType
    correct_answer: str
    user_answer: Optional[str] = None
    explanation: Optional[str] = None
    points: float = Field(ge=0)


class EvaluationSummary(BaseModel):

    total_questions: int
    correct_answers: int
    incorrect_answers: int
    unanswered: int
    score_percentage: float = Field(ge=0, le=100)
    total_points: float
    max_points: float
    grade: Grade


class TopicBreakdown(BaseModel):

    topic: str
    total_questions: int
    correct_answers: int
    accuracy_rate: float = Field(ge=0, le=100)
    recommendations: List[str] = Field(default_factory=list)


class Analysis(BaseModel):

    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    study_plan: List[str] = Field(default_factory=list)
    overall_feedback: str = ""
    improvement_areas: List[str] = Field(default_factory=list)


class EvaluationConfig(BaseModel):

    include_explanations: bool = True
    include_ai_analysis: bool = True
    save_history: bool = True
    grading_scale: Dict[str, tuple] = Field(
        default_factory=lambda: {
            "A": (90, 100),
            "B": (80, 89),
            "C": (70, 79),
            "D": (60, 69),
            "F": (0, 59),
        }
    )


class EvaluationResult(BaseModel):

    evaluation_id: str
    quiz_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    summary: EvaluationSummary
    question_results: List[QuestionResult]
    topic_breakdown: List[TopicBreakdown]
    analysis: Analysis
    config: Optional[EvaluationConfig] = None
    metadata: Optional[Dict[str, Any]] = None


class EvaluateRequest(BaseModel):

    submission: QuizSubmission
    config: Optional[EvaluationConfig] = None


__all__ = [
    "QuestionType",
    "Grade",
    "UserQuestion",
    "UserInfo",
    "QuizSubmission",
    "QuestionResult",
    "EvaluationSummary",
    "TopicBreakdown",
    "Analysis",
    "EvaluationConfig",
    "EvaluationResult",
    "EvaluateRequest",
]
