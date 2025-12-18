from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import logging
import time
from io import BytesIO
from PIL import Image

from schemas import OCRResponse, OCRMultiResponse, HealthResponse
from ocr_processor import OCRProcessor
from database import init_db, log_ocr_request

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="OCR Service API",
    description="Text extraction service using computer vision models",
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

ocr_processor = OCRProcessor()


@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="healthy", service="ocr_service", version="1.0.0")


@app.post("/extract_text", response_model=OCRResponse)
async def extract_text_single(file: UploadFile = File(...)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    try:
        start_time = time.time()

        contents = await file.read()
        image = Image.open(BytesIO(contents)).convert("RGB")

        extracted_text = await ocr_processor.extract_text([image])

        processing_time = time.time() - start_time

        await log_ocr_request(
            filename=file.filename,
            file_size=len(contents),
            processing_time=processing_time,
            num_images=1,
            extracted_text=extracted_text,
        )

        return OCRResponse(
            text=extracted_text, processing_time=processing_time, filename=file.filename
        )

    except Exception as e:
        logger.error(f"Error processing single image: {str(e)}")
        raise HTTPException(status_code=500, detail="Error processing image")


@app.post("/extract_text_multi", response_model=OCRMultiResponse)
async def extract_text_multi(files: List[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    try:
        start_time = time.time()
        images = []
        total_size = 0
        filenames = []

        for file in files:
            if not file.content_type.startswith("image/"):
                raise HTTPException(
                    status_code=400, detail=f"File '{file.filename}' is not an image"
                )

            contents = await file.read()
            total_size += len(contents)
            filenames.append(file.filename)

            image = Image.open(BytesIO(contents)).convert("RGB")
            images.append(image)

        extracted_text = await ocr_processor.extract_text(images)

        processing_time = time.time() - start_time

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

    except Exception as e:
        logger.error(f"Error processing multiple images: {str(e)}")
        raise HTTPException(status_code=500, detail="Error processing images")


@app.post("/extract_information", response_model=OCRMultiResponse)
async def extract_information_legacy(files: List[UploadFile] = File(...)):
    return await extract_text_multi(files)
