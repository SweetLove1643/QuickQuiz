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
from typing import Dict, Any

from tasks import generate_quiz_job

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(status="healthy", service="quiz_generator", version="1.0.0")


@app.post("/quiz/generate")
async def generate_quiz_endpoint(request_data: Dict[str, Any]):
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
        logger.info(
            f"Received quiz generation request: {json.dumps(request_data, ensure_ascii=False)}"
        )

        # Generate quiz using the existing function
        import uuid

        job_id = f"api-{uuid.uuid4().hex[:8]}"
        result_data = generate_quiz_job(job_id, request_data)

        # Result is already a dict, no need to parse JSON
        logger.info(
            f"Successfully generated quiz with {len(result_data.get('questions', []))} questions"
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


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "Quiz Generator API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {"generate_quiz": "POST /quiz/generate"},
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8003, reload=False, log_level="info")
