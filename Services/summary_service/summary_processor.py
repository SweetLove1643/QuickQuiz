import google.genai as genai
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class SummaryProcessor:
    def __init__(self, api_key: Optional[str]):
        self.api_key = api_key
        if api_key:
            self.client = genai.Client(api_key=api_key)
        else:
            self.client = None
            logger.warning("SummaryProcessor initialized without API key")

    async def summarize_text(self, text: str) -> str:
        """Summarize the provided text using Gemini API"""
        if not self.client:
            raise ValueError("GEMINI_API_KEY not configured")

        try:
            summary_prompt = f"""
Bạn là Gemini, một mô hình chuyên tóm tắt tài liệu học thuật và kỹ thuật ở nhiều lĩnh vực khác nhau.

========================================
NHIỆM VỤ CỦA BẠN
========================================
Hãy tạo một bản tóm tắt kiến thức duy nhất từ nội dung sau đây.

Yêu cầu của bản tóm tắt:
1. **TÓM TẮT CHÍNH XÁC**: Chỉ dựa trên nội dung đã cung cấp, không thêm thông tin bên ngoài
2. **CẤU TRÚC RÕ RÀNG**: Chia thành các mục chính với tiêu đề phù hợp
3. **NGÔN NGỮ DỄ HIỂU**: Sử dụng thuật ngữ phù hợp với cấp độ của nội dung
4. **ĐẦY ĐỦ THÔNG TIN**: Giữ lại các khái niệm, công thức, ví dụ quan trọng
5. **ĐỊNH DẠNG MARKDOWN**: Sử dụng headers, bullets, emphasis khi cần thiết

========================================
NỘI DUNG CẦN TÓM TẮT
========================================
{text}

========================================
YÊU CẦU ĐỊNH DẠNG
========================================
- Bắt đầu với tiêu đề chính của chủ đề
- Chia thành các phần với ## hoặc ###
- Sử dụng bullet points cho danh sách
- In đậm từ khóa quan trọng
- Giữ lại công thức, số liệu chính xác

Hãy tạo bản tóm tắt ngay bây giờ:
"""

            response = self.client.models.generate_content(
                model="gemini-2.5-flash", contents=summary_prompt
            )

            return response.text.strip()

        except Exception as e:
            logger.error(f"Error in text summarization: {e}")
            raise e
