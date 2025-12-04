import google.genai as genai
from fastapi import UploadFile
from typing import List, Optional
import logging
from io import BytesIO
import fitz  # PyMuPDF
from PIL import Image

logger = logging.getLogger(__name__)


class OCRProcessor:
    def __init__(self, api_key: Optional[str]):
        self.api_key = api_key
        if api_key:
            self.client = genai.Client(api_key=api_key)
        else:
            self.client = None
            logger.warning("OCRProcessor initialized without API key")

    async def extract_text_from_files(self, files: List[UploadFile]) -> str:
        """Extract text from uploaded files (images or PDFs)"""
        if not self.client:
            raise ValueError("GEMINI_API_KEY not configured")

        try:
            extracted_texts = []

            for file in files:
                content = await file.read()

                if file.content_type == "application/pdf":
                    # Handle PDF files
                    text = await self._extract_from_pdf(content)
                elif file.content_type.startswith("image/"):
                    # Handle image files
                    text = await self._extract_from_image(content)
                else:
                    logger.warning(f"Unsupported file type: {file.content_type}")
                    continue

                if text:
                    extracted_texts.append(text)

            return "\n\n".join(extracted_texts)

        except Exception as e:
            logger.error(f"Error extracting text from files: {e}")
            raise e

    async def _extract_from_pdf(self, pdf_content: bytes) -> str:
        """Extract text from PDF content"""
        try:
            # Open PDF from bytes
            doc = fitz.open(stream=pdf_content, filetype="pdf")
            extracted_text = ""

            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text()
                extracted_text += f"\n--- Trang {page_num + 1} ---\n{text}"

            doc.close()
            return extracted_text.strip()

        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            return ""

    async def _extract_from_image(self, image_content: bytes) -> str:
        """Extract text from image content using Gemini Vision"""
        try:
            # Convert bytes to PIL Image
            image = Image.open(BytesIO(image_content)).convert("RGB")

            # Use Gemini API for OCR
            prompt = """Hãy trích xuất toàn bộ nội dung văn bản có trong ảnh này.

YÊU CẦU:
- Trích xuất chính xác từng ký tự, từ ngữ
- Giữ nguyên format, xuống dòng như trong ảnh gốc
- Không thêm, bớt, sửa đổi nội dung
- Nếu không đọc được, ghi "Không thể đọc được nội dung"

Chỉ trả về nội dung văn bản đã trích xuất, không cần giải thích thêm."""

            response = self.client.models.generate_content(
                model="gemini-1.5-flash", contents=[prompt, image]
            )

            return response.text.strip()

        except Exception as e:
            logger.error(f"Error extracting text from image: {e}")
            return ""
