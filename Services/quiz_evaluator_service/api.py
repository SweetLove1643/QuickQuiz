from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ValidationError
import logging
import json
from typing import Dict, Any

from tasks import evaluate_quiz
from database import create_tables

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

create_tables()
logger.info("Database tables initialized")

app = FastAPI(
    title="Quiz Evaluator API",
    description="Evaluate Vietnamese quiz results with AI-powered learning analytics using Google Gemini API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
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
    return HealthResponse(status="healthy", service="quiz_evaluator", version="1.0.0")


@app.post("/quiz/evaluate")
async def evaluate_quiz_endpoint(request_data: Dict[str, Any]):
    try:
        logger.info(
            f"Received quiz evaluation request for quiz: {request_data.get('submission', {}).get('quiz_id', 'unknown')}"
        )

        result_json = evaluate_quiz(request_data)

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


@app.get("/results/user/{user_id}")
async def get_user_results(user_id: str, limit: int = 50, offset: int = 0):
    try:
        from database import QuizSubmission, get_db

        db = next(get_db())
        results = (
            db.query(QuizSubmission)
            .filter(QuizSubmission.user_id == user_id)
            .order_by(QuizSubmission.submitted_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

        return {
            "success": True,
            "user_id": user_id,
            "results": [
                {
                    "submission_id": r.submission_id,
                    "quiz_id": r.quiz_id,
                    "score_percentage": r.score_percentage,
                    "grade": (
                        "A"
                        if r.score_percentage >= 90
                        else (
                            "B"
                            if r.score_percentage >= 80
                            else (
                                "C"
                                if r.score_percentage >= 70
                                else "D" if r.score_percentage >= 60 else "F"
                            )
                        )
                    ),
                    "total_questions": r.total_questions,
                    "correct_count": r.correct_count,
                    "completion_time": r.completion_time,
                    "submitted_at": (
                        r.submitted_at.isoformat() if r.submitted_at else None
                    ),
                }
                for r in results
            ],
            "total": len(results),
        }
    except Exception as e:
        logger.error(f"Failed to get user results: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve results: {str(e)}"
        )
    finally:
        if db:
            db.close()


@app.get("/results/user/{user_id}/recent")
async def get_user_recent_results(user_id: str, limit: int = 10):
    try:
        from database import QuizSubmission, get_db

        db = next(get_db())
        results = (
            db.query(QuizSubmission)
            .filter(QuizSubmission.user_id == user_id)
            .order_by(QuizSubmission.submitted_at.desc())
            .limit(limit)
            .all()
        )

        return {
            "success": True,
            "user_id": user_id,
            "recent_results": [
                {
                    "submission_id": r.submission_id,
                    "quiz_id": r.quiz_id,
                    "score_percentage": r.score_percentage,
                    "submitted_at": (
                        r.submitted_at.isoformat() if r.submitted_at else None
                    ),
                }
                for r in results
            ],
        }
    except Exception as e:
        logger.error(f"Failed to get recent results: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve recent results: {str(e)}"
        )
    finally:
        if db:
            db.close()


@app.get("/")
async def root():
    return {
        "service": "Quiz Evaluator API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "evaluate_quiz": "POST /quiz/evaluate",
            "grading_scale": "GET /quiz/grading-scale",
            "get_user_results": "GET /results/user/{user_id}",
            "get_recent_results": "GET /results/user/{user_id}/recent",
        },
        "features": [
            "Automatic scoring and grading",
            "Topic-based performance analysis",
            "AI-powered learning recommendations",
            "Detailed explanations for incorrect answers",
            "Evaluation history tracking",
            "User-specific result management",
        ],
    }


if __name__ == "__main__":
    import uvicorn
    import os

    port = int(os.getenv("PORT", "8003"))
    uvicorn.run(app, host="127.0.0.1", port=port, reload=False, log_level="info")
