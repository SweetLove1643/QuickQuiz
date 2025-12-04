"""
FastAPI server for Quiz Evaluator
=================================

RESTful API endpoints for evaluating quiz results and providing learning analytics.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ValidationError
import logging
import json
from typing import Dict, Any

from tasks import evaluate_quiz

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Quiz Evaluator API",
    description="Evaluate Vietnamese quiz results with AI-powered learning analytics using Google Gemini API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


class ErrorResponse(BaseModel):
    error: str
    details: str = None


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(status="healthy", service="quiz_evaluator", version="1.0.0")


@app.post("/quiz/evaluate")
async def evaluate_quiz_endpoint(request_data: Dict[str, Any]):
    """
    Evaluate quiz results and provide learning analytics.

    Expected input format:
    {
        "submission": {
            "quiz_id": "quiz-12345",
            "questions": [
                {
                    "id": "q1",
                    "type": "mcq",
                    "stem": "Câu hỏi...",
                    "options": ["A", "B", "C"],
                    "correct_answer": "A",
                    "user_answer": "B",
                    "topic": "Python basics"
                }
            ],
            "user_info": {
                "user_id": "user123",
                "completion_time": 300,
                "session_id": "session456"
            }
        },
        "config": {
            "include_explanations": true,
            "include_ai_analysis": true,
            "save_history": true
        }
    }

    Returns comprehensive evaluation results with AI analysis.
    """
    try:
        logger.info(
            f"Received quiz evaluation request for quiz: {request_data.get('submission', {}).get('quiz_id', 'unknown')}"
        )

        # Evaluate quiz using the existing function
        result_json = evaluate_quiz(request_data)

        # Parse JSON to validate it's correct
        result_data = json.loads(result_json)

        logger.info(
            f"Successfully evaluated quiz - Score: {result_data.get('summary', {}).get('score_percentage', 0):.1f}%"
        )

        return result_data

    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid input data: {str(e)}")
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to parse evaluation results: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get("/quiz/grading-scale")
async def get_grading_scale():
    """Get the current grading scale configuration."""
    return {
        "grading_scale": {
            "A": {"min": 90, "max": 100, "description": "Xuất sắc"},
            "B": {"min": 80, "max": 89, "description": "Tốt"},
            "C": {"min": 70, "max": 79, "description": "Khá"},
            "D": {"min": 60, "max": 69, "description": "Trung bình"},
            "F": {"min": 0, "max": 59, "description": "Yếu"},
        },
        "question_types": ["mcq", "tf", "fill_blank"],
        "analysis_features": [
            "Topic-based analysis",
            "AI-powered recommendations",
            "Learning analytics",
            "Personalized study plans",
        ],
    }


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "Quiz Evaluator API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "evaluate_quiz": "POST /quiz/evaluate",
            "grading_scale": "GET /quiz/grading-scale",
        },
        "features": [
            "Automatic scoring and grading",
            "Topic-based performance analysis",
            "AI-powered learning recommendations",
            "Detailed explanations for incorrect answers",
            "Evaluation history tracking",
        ],
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8005, reload=False, log_level="info")
