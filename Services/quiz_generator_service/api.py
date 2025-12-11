"""
FastAPI server for Quiz Generator
=================================

RESTful API endpoints for generating quizzes from Vietnamese text content.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ValidationError
import logging
import json
import sys
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
import uuid

# Add ai_validation to Python path
ai_validation_path = Path(__file__).parent.parent / "ai_validation"
sys.path.insert(0, str(ai_validation_path))

from content_validator import ContentValidator, ValidationResult
from tasks import generate_quiz_job, get_db_session
from schemas import QuizQuestion, Quiz
from database import GeneratedQuiz, create_tables

# Initialize database tables on startup
create_tables()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize content validator
content_validator = ContentValidator()

# Create FastAPI app
app = FastAPI(
    title="Quiz Generator API",
    description="Generate Vietnamese quizzes from text content using Google Gemini API",
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


class Section(BaseModel):
    id: str
    summary: str


class QuizConfig(BaseModel):
    n_questions: int = 5
    types: List[str] = ["multiple_choice"]


class GenerateQuizRequest(BaseModel):
    sections: List[Section]
    config: QuizConfig


class SaveQuizRequest(BaseModel):
    quiz_id: str | None = None
    user_id: str  # Required: user who creates the quiz
    title: str | None = None
    document_id: str | None = None
    document_name: str | None = None
    questions: List[QuizQuestion]
    metadata: Dict[str, Any] | None = None


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint with AI validation status."""
    try:
        # Test validator functionality by creating a simple test question
        test_question = {
            "id": "health_check",
            "type": "mcq",
            "stem": "Test question for health check",
            "options": ["A", "B", "C"],
            "correct_answer": "A",
        }
        validation_results = content_validator.validate_quiz_questions([test_question])

        return HealthResponse(
            status="healthy" if len(validation_results) > 0 else "degraded",
            service="quiz_generator",
            version="1.0.0",
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy", service="quiz_generator", version="1.0.0"
        )


@app.post("/quiz/generate")
async def generate_quiz_endpoint(request: GenerateQuizRequest):
    """
    Generate quiz from text content.

    Expected input format:
    {
        "sections": [
            {
                "id": "Section title",
                "summary": "Section content..."
            }
        ],
        "config": {
            "n_questions": 10,
            "types": ["multiple_choice", "true_false", "fill_blank"]
        }
    }

    Returns JSON quiz data.
    """
    try:
        # Convert Pydantic model to dict
        request_data = request.dict()

        logger.info(
            f"Received quiz generation request: {json.dumps(request_data, ensure_ascii=False)}"
        )

        # Generate quiz using the existing function
        import uuid

        job_id = f"api-{uuid.uuid4().hex[:8]}"
        result_data = generate_quiz_job(job_id, request_data)

        # Validate generated content to prevent AI hallucination
        logger.info("Validating generated quiz content...")
        questions = result_data.get("questions", [])
        if questions:
            validation_results = content_validator.validate_quiz_questions(questions)
            validation_summary = content_validator.get_validation_summary(
                validation_results
            )

            # Log validation warnings if any
            high_risk_questions = [
                r for r in validation_results if r.risk_level == "high"
            ]
            if high_risk_questions:
                logger.warning(f"Found {len(high_risk_questions)} high-risk questions")

            # Add validation metadata to response
            result_data["validation"] = {
                "summary": validation_summary,
                "total_questions": len(questions),
                "high_risk_count": len(high_risk_questions),
                "validation_timestamp": datetime.now().isoformat(),
            }
        else:
            result_data["validation"] = {
                "summary": {"message": "No questions to validate"},
                "validation_timestamp": datetime.now().isoformat(),
            }

        # Result is already a dict, no need to parse JSON
        question_count = len(result_data.get("questions", []))
        validation_info = result_data.get("validation", {})
        logger.info(
            f"Successfully generated and validated quiz with {question_count} questions"
        )

        return result_data

    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid input data: {str(e)}")
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to parse generated quiz: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.post("/quiz/save")
async def save_quiz_endpoint(request: SaveQuizRequest):
    """Persist a quiz payload for later retrieval/analytics."""
    quiz_id = request.quiz_id or f"quiz-{uuid.uuid4().hex[:8]}"

    try:
        # Validate questions via Pydantic
        question_objs = [QuizQuestion(**q.model_dump()) for q in request.questions]
        quiz = Quiz(
            id=quiz_id,
            questions=question_objs,
            meta={
                "title": request.title,
                "document_id": request.document_id,
                "document_name": request.document_name,
                **(request.metadata or {}),
            },
        )

        quiz_data = quiz.model_dump()

        db = get_db_session()
        generated_quiz = GeneratedQuiz(
            quiz_id=quiz_id,
            user_id=request.user_id,
            title=request.title,
            document_id=request.document_id,
            questions_data=quiz_data,
            quiz_metadata={
                "saved_at": datetime.utcnow().isoformat(),
                "document_name": request.document_name,
            },
            source_sections=[],
            generation_config={},
            validation_summary={},
        )
        db.add(generated_quiz)
        db.commit()

        return {
            "success": True,
            "quiz_id": quiz_id,
            "user_id": request.user_id,
            "saved_at": datetime.utcnow().isoformat(),
        }
    except ValidationError as e:
        logger.error(f"Quiz save validation error: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid quiz data: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to save quiz: {e}")
        raise HTTPException(status_code=500, detail="Failed to save quiz")
    finally:
        if "db" in locals():
            db.close()


@app.get("/validation/metrics")
async def get_validation_metrics():
    """Get AI validation metrics and statistics."""
    try:
        # Get basic validation info
        validator_info = {
            "validator_initialized": True,
            "high_risk_keywords": len(content_validator.high_risk_keywords),
            "confidence_weights": content_validator.confidence_weights,
            "validation_ready": True,
        }

        return {
            "validation_info": validator_info,
            "timestamp": datetime.now().isoformat(),
            "status": "operational",
        }
    except Exception as e:
        logger.error(f"Failed to get validation metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Metrics error: {str(e)}")


@app.get("/quiz/user/{user_id}")
async def get_user_quizzes(user_id: str, limit: int = 50, offset: int = 0):
    """Get all quizzes created by a specific user."""
    try:
        db = get_db_session()
        quizzes = (
            db.query(GeneratedQuiz)
            .filter(GeneratedQuiz.user_id == user_id)
            .order_by(GeneratedQuiz.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

        return {
            "success": True,
            "user_id": user_id,
            "quizzes": [
                {
                    "quiz_id": q.quiz_id,
                    "title": q.title or "Untitled Quiz",
                    "document_id": q.document_id,
                    "created_at": q.created_at.isoformat() if q.created_at else None,
                    "questions_count": (
                        len(q.questions_data.get("questions", []))
                        if q.questions_data
                        else 0
                    ),
                    "last_accessed": (
                        q.last_accessed.isoformat() if q.last_accessed else None
                    ),
                }
                for q in quizzes
            ],
            "total": len(quizzes),
        }
    except Exception as e:
        logger.error(f"Failed to get user quizzes: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve quizzes: {str(e)}"
        )
    finally:
        if "db" in locals():
            db.close()


@app.get("/quiz/user/{user_id}/recent")
async def get_user_recent_quizzes(user_id: str, limit: int = 10):
    """Get recent quizzes created by a user (for home page)."""
    try:
        db = get_db_session()
        quizzes = (
            db.query(GeneratedQuiz)
            .filter(GeneratedQuiz.user_id == user_id)
            .order_by(GeneratedQuiz.created_at.desc())
            .limit(limit)
            .all()
        )

        return {
            "success": True,
            "user_id": user_id,
            "recent_quizzes": [
                {
                    "quiz_id": q.quiz_id,
                    "title": q.title or "Untitled Quiz",
                    "document_id": q.document_id,
                    "created_at": q.created_at.isoformat() if q.created_at else None,
                    "questions_count": (
                        len(q.questions_data.get("questions", []))
                        if q.questions_data
                        else 0
                    ),
                }
                for q in quizzes
            ],
        }
    except Exception as e:
        logger.error(f"Failed to get recent quizzes: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve recent quizzes: {str(e)}"
        )
    finally:
        if "db" in locals():
            db.close()


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "Quiz Generator API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "generate_quiz": "POST /quiz/generate",
            "save_quiz": "POST /quiz/save",
            "get_user_quizzes": "GET /quiz/user/{user_id}",
            "get_recent_quizzes": "GET /quiz/user/{user_id}/recent",
            "validation_metrics": "GET /validation/metrics",
        },
        "features": [
            "AI-powered quiz generation",
            "Content validation & hallucination prevention",
            "Vietnamese language support",
            "Multiple question types (MCQ, True/False, Fill-blank)",
            "User-specific quiz management",
        ],
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8003, reload=False, log_level="info")
