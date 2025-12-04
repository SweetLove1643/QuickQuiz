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

# Add ai_validation to Python path
ai_validation_path = Path(__file__).parent.parent / "ai_validation"
sys.path.insert(0, str(ai_validation_path))

from content_validator import ContentValidator, ValidationResult
from tasks import generate_quiz_job

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
            "validation_metrics": "GET /validation/metrics",
        },
        "features": [
            "AI-powered quiz generation",
            "Content validation & hallucination prevention",
            "Vietnamese language support",
            "Multiple question types (MCQ, True/False, Fill-blank)",
        ],
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8003, reload=False, log_level="info")
