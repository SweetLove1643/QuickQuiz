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
