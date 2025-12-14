from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import logging
import os
from dotenv import load_dotenv

from schemas import (
    SummaryResponse,
    OCRSummaryResponse,
    HealthResponse,
    SummaryRequestModel,
)
from summary_processor import SummaryProcessor
from ocr_processor import OCRProcessor
from database import init_db, log_summary_request

# Load environment variables from root directory
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="Summary Service API",
    description="Document summarization and study recommendation service",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
init_db()

# Initialize processors
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    logger.warning("GEMINI_API_KEY not found in environment variables")

summary_processor = SummaryProcessor(api_key)
ocr_processor = OCRProcessor(api_key)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(status="healthy", service="summary_service", version="1.0.0")


@app.post("/summarize_text", response_model=SummaryResponse)
async def summarize_text(request: SummaryRequestModel):
    """Summarize provided text"""
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text content is required")

    if not api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured")

    try:
        # summary = await summary_processor.summarize_text(request.text)
        summary = request.text

        # Log to database
        await log_summary_request(
            content_type="text",
            input_text=request.text[:500],  # Store first 500 chars for logging
            summary=summary,
            processing_method="direct_text",
        )

        return SummaryResponse(
            summary=summary, input_type="text", word_count=len(request.text.split())
        )

    except Exception as e:
        logger.error(f"Error summarizing text: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Error processing text summarization"
        )


@app.post("/ocr_and_summarize", response_model=OCRSummaryResponse)
async def ocr_and_summarize(files: List[UploadFile] = File(...)):
    """Extract text from images/PDFs and create summary"""
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    if not api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured")

    try:
        # Extract text using OCR
        extracted_text = await ocr_processor.extract_text_from_files(files)

        if not extracted_text.strip():
            raise HTTPException(
                status_code=400, detail="No text could be extracted from uploaded files"
            )

        # Create summary
        # summary = await summary_processor.summarize_text(extracted_text)
        summary = extracted_text

        # Log to database
        await log_summary_request(
            content_type="ocr",
            input_text=extracted_text[:500],
            summary=summary,
            processing_method="ocr_then_summary",
            num_files=len(files),
        )

        return OCRSummaryResponse(
            extracted_text=extracted_text,
            summary=summary,
            num_files=len(files),
            filenames=[f.filename for f in files],
            word_count=len(extracted_text.split()),
        )

    except Exception as e:
        logger.error(f"Error in OCR and summarize: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Error processing files for summarization"
        )


# Legacy endpoints for backward compatibility
@app.post("/image_ocr")
async def image_ocr_legacy(files: List[UploadFile] = File(...)):
    """Legacy OCR endpoint"""
    result = await ocr_and_summarize(files)
    return {"extracted_text": result.extracted_text, "num_files": result.num_files}
