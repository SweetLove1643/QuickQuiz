from typing import List
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from services.ocr_service.Extract_Information_Service import extract_information
import time
from pdf2image import convert_from_bytes
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
    
    allowed_types = ["image/png", "image/jpeg", "application/pdf"]
    print(f"types: {[f.content_type for f in files]}")

    for f in files:
        if f.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"File {f.filename} không hỗ trợ. Chỉ hỗ trợ PNG, JPG, PDF"
            )

    start_time = time.time()
    images: List[Image.Image] = []

    for f in files:
        try:
            contents = await f.read()

            if f.filename.lower().endswith(".pdf") or f.content_type == "application/pdf":
                try:
                    pdf_pages = convert_from_bytes(contents, dpi=200, fmt="jpeg")
                    images.extend(pdf_pages)
                    continue
                except Exception as e:
                    print("[ERROR] Cannot convert PDF:", repr(e), flush=True)
                    raise HTTPException(
                        status_code=400,
                        detail=f"File '{f.filename}' không phải PDF hợp lệ hoặc không thể đọc"
                    )
                
            try: 
                img = Image.open(BytesIO(contents)).convert("RGB")
                images.append(img)
            except Exception as e:
                print("[ERROR] Cannot open uploaded image:", repr(e), flush=True)
                raise HTTPException(
                    status_code=400,
                    detail=f"File '{f.filename}' không phải là ảnh hợp lệ"
                )

        except Exception:
            raise HTTPException(status_code=400, detail=f"Lỗi khi đọc file {f.filename}")
    
    if not images:
        raise HTTPException(status_code=400, detail="Không có trang ảnh nào để xử lý")

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
