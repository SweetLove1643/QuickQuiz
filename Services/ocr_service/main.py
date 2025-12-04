from typing import List
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from services.OCR_IE.Extract_Information_Service import extract_information
import time
from io import BytesIO
from PIL import Image



app = FastAPI(
    title="Extractive Information System",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ExtractMultiResponse(BaseModel):
    text: str
    processing_time: float
    num_images: int

@app.post("/extract_information", response_model=ExtractMultiResponse)
async def extract_multi_endpoint(files: List[UploadFile] = File(...)):

    if not files:
        raise HTTPException(status_code=400, detail="Chưa upload file nào")

    start_time = time.time()
    images: List[Image.Image] = []

    for f in files:
        try:
            contents = await f.read()
            img = Image.open(BytesIO(contents)).convert("RGB")
            images.append(img)
        except Exception as e:
            print("[ERROR] Cannot open uploaded image:", repr(e), flush=True)
            raise HTTPException(
                status_code=400,
                detail=f"File '{f.filename}' không phải là ảnh hợp lệ"
            )

    try:
        text = extract_information(images)
    except Exception as e:
        print("[ERROR] Error in extract_information:", repr(e), flush=True)
        raise HTTPException(status_code=500, detail="Lỗi trong quá trình trích xuất thông tin")

    processing_time = time.time() - start_time
    return ExtractMultiResponse(
        text=text,
        processing_time=processing_time,
        num_images=len(images),
    )
