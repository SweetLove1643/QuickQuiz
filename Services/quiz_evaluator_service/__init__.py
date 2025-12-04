"""
Quiz Evaluator Package
=====================

Đánh giá kết quả bài kiểm tra và phân tích học tập cho người dùng.

Features:
- Tính điểm và xếp loại tự động
- Phân tích ưu nhược điểm theo topic/category
- Đề xuất cải thiện từ AI (Gemini API)
- Lưu lịch sử đánh giá
- REST API với FastAPI
"""

from .tasks import evaluate_quiz
from .schemas import (
    QuizSubmission,
    EvaluationResult,
    QuestionResult,
    Analysis,
    EvaluationConfig,
)

__version__ = "1.0.0"
__author__ = "Quiz Evaluator Team"

__all__ = [
    "evaluate_quiz",
    "QuizSubmission",
    "EvaluationResult",
    "QuestionResult",
    "Analysis",
    "EvaluationConfig",
]
