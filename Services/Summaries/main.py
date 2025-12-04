# main.py
# uvicorn main:app --reload
from fastapi import FastAPI, UploadFile, File, HTTPException
from src.ocr_service import extract_information
from src.summaries_service import Summaries_Knowledge
from src.recommend_study_event import RecommendStudyEvent
from models.recommend_study_model import RecommendRequest
from models.summary_model import SummaryRequestModel
from fastapi.concurrency import run_in_threadpool
import uvicorn
from typing import List
import os

from dotenv import load_dotenv

app = FastAPI()

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

from typing import List
from fastapi import UploadFile, File, HTTPException
from fastapi.concurrency import run_in_threadpool

@app.post("/image_ocr")
async def ocr_endpoint(files: List[UploadFile] = File(...)):
    """
    OCR nhiều ảnh hoặc PDF cùng lúc.
    Gộp toàn bộ nội dung vào 1 request → giảm thời gian & chi phí.
    """

    allowed_types = ["image/png", "image/jpeg", "application/pdf"]

    print(f"types: {[f.content_type for f in files]}")

    # 1. Validate
    for f in files:
        if f.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"File {f.filename} không hỗ trợ. Chỉ hỗ trợ PNG, JPG, PDF"
            )

    # 2. Đọc toàn bộ bytes
    file_bytes_list = []
    mime_types = []

    for f in files:
        content = await f.read()
        file_bytes_list.append(content)
        mime_types.append(f.content_type)

    try:
        # 3. Gọi batch OCR
        text = await run_in_threadpool(
            extract_information,
            file_bytes_list,
            mime_types,
            API_KEY
        )

        return {
            "total_files": len(files),
            "files": [f.filename for f in files],
            "text": text
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/summarize")
async def summarize_endpoint(request: SummaryRequestModel):
    """
    Endpoint tóm tắt văn bản.
    Nhận: Chuỗi văn bản
    Trả về: Chuỗi văn bản tóm tắt
    """

    try:
        summary = Summaries_Knowledge(ocr_text=request.text, api_key=API_KEY)
        return {"summary": summary}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/api/notes/analyze")
async def recommend_study_event_endpoint(payload: RecommendRequest):
    """
    Endpoint gợi ý sự kiện học tập dựa trên tóm tắt văn bản.
    Nhận: Chuỗi văn bản tóm tắt
    Trả về: Danh sách sự kiện học tập được gợi ý
    """

    try:
        result = RecommendStudyEvent(
            userEmail=payload.userEmail,
            newNote=payload.newNote.dict(),
            allEventsInMonth=[event.dict() for event in payload.allEventsInMonth],
            api_key=API_KEY
        )

        return {"newEvent": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
