from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import logging
import httpx

from schemas import (
    SummaryResponse,
    OCRSummaryResponse,
    HealthResponse,
    SummaryRequestModel,
)
from summary_processor import SummaryProcessor
from database import init_db, log_summary_request


# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==============================
# FastAPI app
# ==============================
app = FastAPI(
    title="Summary Service API",
    description="Document summarization service using ViT5 + LoRA",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ==============================
# CORS
# ==============================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==============================
# Init DB
# ==============================
init_db()

# ==============================
# Init processors (LOAD ONCE)
# ==============================
CHECKPOINT_PATH = "./ViT5_checkpoint_epochs4"

try:
    summary_processor = SummaryProcessor(checkpoint_path=CHECKPOINT_PATH)
    logger.info("SummaryProcessor initialized successfully")
except Exception as e:
    logger.exception("Failed to initialize SummaryProcessor")
    raise e


# ==============================
# Health check
# ==============================
@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        service="summary_service",
        version="1.0.0",
    )


# ==============================
# Summarize text
# ==============================
@app.post("/summarize_text", response_model=SummaryResponse)
async def summarize_text(request: SummaryRequestModel):
    if not request.text or not request.text.strip():
        raise HTTPException(
            status_code=400,
            detail="Text content is required",
        )

    try:
        summary = await summary_processor.summarize_text(request.text)

        await log_summary_request(
            content_type="text",
            input_text=request.text[:500],
            summary=summary,
            processing_method="direct_text",
        )

        return SummaryResponse(
            summary=summary,
            input_type="text",
            word_count=len(request.text.split()),
        )

    except Exception as e:
        logger.error(f"Error summarizing text: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error processing text summarization",
        )


# ==============================
# OCR + Summarize
# ==============================
@app.post("/ocr_and_summarize", response_model=OCRSummaryResponse)
async def ocr_and_summarize(files: List[UploadFile] = File(...)):
    if not files:
        raise HTTPException(
            status_code=400,
            detail="No files uploaded",
        )

    try:
        multipart_files = []
        for f in files:
            content = await f.read()

            multipart_files.append(
                (
                    "files",
                    (f.filename, content, f.content_type),
                )
            )
        OCR_SERVICE_URL = "http://127.0.0.1:8004/extract_information"

        async with httpx.AsyncClient(timeout=600) as client:
            response = await client.post(
                OCR_SERVICE_URL,
                files=multipart_files,
            )
        if response.status_code != 200:
            raise RuntimeError(
                f"OCR service error {response.status_code}: {response.text}"
            )

        data = response.json()
        extracted_text = data.get("text", "")

        if isinstance(extracted_text, list):
            extracted_text = "\n".join(extracted_text)

        if not isinstance(extracted_text, str):
            raise ValueError("OCR returned invalid text format")

        if not extracted_text.strip():
            raise HTTPException(
                status_code=400,
                detail="No text could be extracted from uploaded files",
            )

        summary = await summary_processor.summarize_text(extracted_text)

        await log_summary_request(
            content_type="ocr",
            input_text=extracted_text[:500],
            summary=summary,
            processing_method="ocr_and_summarize",
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
        logger.exception("Error in OCR and summarize")
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


# ==============================
# Legacy endpoint
# ==============================
@app.post("/image_ocr")
async def image_ocr_legacy(files: List[UploadFile] = File(...)):
    result = await ocr_and_summarize(files)
    return {
        "extracted_text": result.extracted_text,
        "num_files": result.num_files,
    }
