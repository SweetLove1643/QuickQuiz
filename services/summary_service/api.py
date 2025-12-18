from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import logging
import httpx
import io

try:
    import fitz  # PyMuPDF
except ImportError:  # pragma: no cover - optional dependency
    fitz = None

from schemas import (
    SummaryResponse,
    OCRSummaryResponse,
    HealthResponse,
    SummaryRequestModel,
)
from summary_processor import SummaryProcessor
from database import init_db, log_summary_request


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Summary Service API",
    description="Document summarization service using ViT5 + LoRA",
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

init_db()

CHECKPOINT_PATH = "./ViT5_checkpoint_epochs4"

try:
    summary_processor = SummaryProcessor(checkpoint_path=CHECKPOINT_PATH)
    logger.info("SummaryProcessor initialized successfully")
except Exception as e:
    logger.exception("Failed to initialize SummaryProcessor")
    raise e


@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        service="summary_service",
        version="1.0.0",
    )


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


@app.post("/ocr_and_summarize", response_model=OCRSummaryResponse)
async def ocr_and_summarize(files: List[UploadFile] = File(...)):
    if not files:
        raise HTTPException(
            status_code=400,
            detail="No files uploaded",
        )

    try:
        pdf_text_parts = []
        image_files = []

        for f in files:
            content = await f.read()
            content_type = (f.content_type or "").lower()
            filename = f.filename or ""
            filename_lower = filename.lower()

            if content_type == "application/pdf" or filename_lower.endswith(".pdf"):
                if fitz is None:
                    error_detail = "Lỗi xử lý PDF: Thư viện PyMuPDF (fitz) chưa được cài đặt trên máy chủ."
                    logger.error(error_detail)
                    raise HTTPException(status_code=500, detail=error_detail)
                
                try:
                    # Attempt to extract text first
                    text = _extract_pdf_text(content)
                    if text and text.strip():
                        logger.info(f"Extracted text from PDF '{filename}' successfully.")
                        pdf_text_parts.append(text)
                    else:
                        # If no text, assume it's an image-based PDF and send to OCR
                        logger.warning(f"No text found in PDF '{filename}'. Forwarding to OCR service.")
                        image_files.append(
                            (
                                "files",
                                (
                                    filename or "document.pdf",
                                    content,
                                    "application/pdf",
                                ),
                            )
                        )
                except Exception as pdf_error:
                    logger.exception(f"Failed to process PDF '{filename}' directly. Forwarding to OCR as a fallback.")
                    # If any error occurs during PDF text extraction, treat it as a candidate for OCR
                    image_files.append(
                        (
                            "files",
                            (
                                filename or "document.pdf",
                                content,
                                "application/pdf",
                            ),
                        )
                    )
            elif content_type == "text/plain" or filename_lower.endswith(".txt"):
                text = content.decode("utf-8", errors="ignore")
                if text.strip():
                    pdf_text_parts.append(text)
                else:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Cannot extract text from TXT: {filename or 'uploaded.txt'}",
                    )
            elif (
                content_type
                == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                or filename_lower.endswith(".docx")
            ):
                image_files.append(
                    (
                        "files",
                        (
                            filename or "document.docx",
                            content,
                            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        ),
                    )
                )
            else:
                image_files.append(
                    (
                        "files",
                        (
                            filename or "image.png",
                            content,
                            content_type or "application/octet-stream",
                        ),
                    )
                )

        extracted_text_parts = []

        if pdf_text_parts:
            extracted_text_parts.append("\n\n".join(pdf_text_parts))

        if image_files:
            OCR_SERVICE_URL = "http://127.0.0.1:8004/extract_information"
            async with httpx.AsyncClient(timeout=300) as client:
                response = await client.post(
                    OCR_SERVICE_URL,
                    files=image_files,
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
                    detail="No text could be extracted from uploaded image files",
                )

            extracted_text_parts.append(extracted_text)

        if not extracted_text_parts:
            raise HTTPException(
                status_code=400,
                detail="No text could be extracted from uploaded files",
            )

        combined_text = "\n\n".join(extracted_text_parts)

        summary = await summary_processor.summarize_text(combined_text)

        await log_summary_request(
            content_type="ocr" if image_files else "pdf",
            input_text=combined_text[:500],
            summary=summary,
            processing_method="ocr_and_summarize",
            num_files=len(files),
        )

        return OCRSummaryResponse(
            extracted_text=combined_text,
            summary=summary,
            num_files=len(files),
            filenames=[f.filename for f in files],
            word_count=len(combined_text.split()),
        )

    except Exception as e:
        logger.exception("Error in OCR and summarize")
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


@app.post("/image_ocr")
async def image_ocr_legacy(files: List[UploadFile] = File(...)):
    result = await ocr_and_summarize(files)
    return {
        "extracted_text": result.extracted_text,
        "num_files": result.num_files,
    }


def _extract_pdf_text(content: bytes) -> str:
    if fitz is None:
        raise RuntimeError("PyMuPDF not installed")

    with fitz.open(stream=content, filetype="pdf") as doc:
        texts = []
        for page in doc:
            texts.append(page.get_text("text"))
    return "\n".join(texts)
