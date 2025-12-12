from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import logging
import time
from io import BytesIO
from PIL import Image
from pdf2image import convert_from_bytes

from schemas import OCRResponse, OCRMultiResponse, HealthResponse
from ocr_processor import OCRProcessor
from database import init_db, log_ocr_request

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="OCR Service API",
    description="Text extraction service using computer vision models",
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

# Initialize OCR processor
ocr_processor = OCRProcessor()


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(status="healthy", service="ocr_service", version="1.0.0")


@app.post("/extract_text", response_model=OCRResponse)
async def extract_text_single(file: UploadFile = File(...)):
    """Extract text from a single image or PDF file"""
    allowed_types = ["image/png", "image/jpeg", "image/jpg", "application/pdf"]

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Định dạng file {file.content_type} chưa được hỗ trợ. Chỉ hỗ trợ: PNG, JPEG, PDF",
        )

    try:
        start_time = time.time()
        contents = await file.read()
        images = []

        # Handle PDF files
        if file.content_type == "application/pdf" or file.filename.lower().endswith(
            ".pdf"
        ):
            try:
                pdf_pages = convert_from_bytes(contents, dpi=200, fmt="jpeg")
                images.extend(pdf_pages)
                logger.info(f"Converted PDF to {len(pdf_pages)} pages")
            except Exception as e:
                logger.error(f"PDF conversion error: {str(e)}")
                raise HTTPException(
                    status_code=400,
                    detail=f"File '{file.filename}' không phải PDF hợp lệ hoặc không thể đọc",
                )
        else:
            # Handle image files
            try:
                image = Image.open(BytesIO(contents)).convert("RGB")
                images.append(image)
            except Exception as e:
                logger.error(f"Image open error: {str(e)}")
                raise HTTPException(
                    status_code=400,
                    detail=f"File '{file.filename}' không phải là ảnh hợp lệ",
                )

        if not images:
            raise HTTPException(
                status_code=400, detail="Không có trang ảnh nào để xử lý"
            )

        # Extract text
        extracted_text = await ocr_processor.extract_text(images)
        processing_time = time.time() - start_time

        # Log to database
        await log_ocr_request(
            filename=file.filename,
            file_size=len(contents),
            processing_time=processing_time,
            num_images=len(images),
            extracted_text=extracted_text,
        )

        return OCRResponse(
            text=extracted_text, processing_time=processing_time, filename=file.filename
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lỗi xử lý file: {str(e)}")


@app.post("/extract_text_multi", response_model=OCRMultiResponse)
async def extract_text_multi(files: List[UploadFile] = File(...)):
    """Extract text from multiple image and PDF files"""
    if not files:
        raise HTTPException(status_code=400, detail="Chưa upload file nào")

    allowed_types = ["image/png", "image/jpeg", "image/jpg", "application/pdf"]

    try:
        start_time = time.time()
        images = []
        total_size = 0
        filenames = []

        # Process all uploaded files
        for file in files:
            if file.content_type not in allowed_types:
                raise HTTPException(
                    status_code=400,
                    detail=f"File '{file.filename}' không hỗ trợ. Chỉ hỗ trợ: PNG, JPEG, PDF",
                )

            contents = await file.read()
            total_size += len(contents)
            filenames.append(file.filename)

            # Handle PDF files
            if file.content_type == "application/pdf" or file.filename.lower().endswith(
                ".pdf"
            ):
                try:
                    pdf_pages = convert_from_bytes(contents, dpi=200, fmt="jpeg")
                    images.extend(pdf_pages)
                    logger.info(f"Converted {file.filename} to {len(pdf_pages)} pages")
                except Exception as e:
                    logger.error(f"PDF conversion error for {file.filename}: {str(e)}")
                    raise HTTPException(
                        status_code=400,
                        detail=f"File '{file.filename}' không phải PDF hợp lệ hoặc không thể đọc",
                    )
            else:
                # Handle image files
                try:
                    image = Image.open(BytesIO(contents)).convert("RGB")
                    images.append(image)
                except Exception as e:
                    logger.error(f"Image open error for {file.filename}: {str(e)}")
                    raise HTTPException(
                        status_code=400,
                        detail=f"File '{file.filename}' không phải là ảnh hợp lệ",
                    )

        if not images:
            raise HTTPException(
                status_code=400, detail="Không có trang ảnh nào để xử lý"
            )

        # Extract text from all images
        extracted_text = await ocr_processor.extract_text(images)
        processing_time = time.time() - start_time

        # Log to database
        await log_ocr_request(
            filename=", ".join(filenames),
            file_size=total_size,
            processing_time=processing_time,
            num_images=len(images),
            extracted_text=extracted_text,
        )

        return OCRMultiResponse(
            text=extracted_text,
            processing_time=processing_time,
            num_images=len(images),
            filenames=filenames,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing files: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lỗi xử lý files: {str(e)}")


# Backward compatibility endpoint
@app.post("/extract_information", response_model=OCRMultiResponse)
async def extract_information_legacy(files: List[UploadFile] = File(...)):
    """Legacy endpoint for backward compatibility"""
    return await extract_text_multi(files)
