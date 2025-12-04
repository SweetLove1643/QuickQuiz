import google.genai as genai
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class RecommendationEngine:
    def __init__(self, api_key: Optional[str]):
        self.api_key = api_key
        if api_key:
            self.client = genai.Client(api_key=api_key)
        else:
            self.client = None
            logger.warning("RecommendationEngine initialized without API key")

    async def generate_recommendations(
        self, content: str, difficulty_level: str = "intermediate", study_time: int = 60
    ) -> Dict[str, Any]:
        """Generate study recommendations based on content"""
        if not self.client:
            raise ValueError("GEMINI_API_KEY not configured")

        try:
            recommendation_prompt = f"""
Bạn là một chuyên gia tư vấn học tập, hãy tạo kế hoạch học tập chi tiết dựa trên nội dung sau:

========================================
THÔNG TIN ĐẦU VÀO
========================================
- **Nội dung học**: {content[:1000]}...
- **Trình độ**: {difficulty_level}
- **Thời gian có**: {study_time} phút

========================================
YÊU CẦU TẠO KẾ HOẠCH
========================================
Hãy tạo một JSON object với các thông tin sau:

{{
    "study_plan": {{
        "overview": "Tóm tắt ngắn về nội dung và cách tiếp cận",
        "time_breakdown": {{
            "review": "X phút",
            "practice": "X phút", 
            "memorization": "X phút",
            "testing": "X phút"
        }},
        "learning_objectives": [
            "Mục tiêu 1",
            "Mục tiêu 2",
            "Mục tiêu 3"
        ],
        "study_steps": [
            {{
                "step": 1,
                "activity": "Tên hoạt động",
                "time": "X phút",
                "description": "Mô tả chi tiết",
                "tips": "Lời khuyên thực hiện"
            }}
        ],
        "key_concepts": [
            "Khái niệm quan trọng 1",
            "Khái niệm quan trọng 2"
        ],
        "practice_suggestions": [
            "Gợi ý luyện tập 1",
            "Gợi ý luyện tập 2"
        ],
        "assessment_methods": [
            "Phương pháp đánh giá 1",
            "Phương pháp đánh giá 2"
        ]
    }},
    "difficulty_assessment": "Đánh giá độ khó và điều chỉnh nếu cần",
    "additional_resources": [
        "Tài liệu bổ sung 1",
        "Tài liệu bổ sung 2"
    ]
}}

Chỉ trả về JSON object, không có text thêm.
"""

            response = self.client.models.generate_content(
                model="gemini-1.5-flash", contents=recommendation_prompt
            )

            # Try to parse JSON response
            import json

            try:
                recommendations = json.loads(response.text.strip())
                return recommendations
            except json.JSONDecodeError:
                # If JSON parsing fails, return structured text response
                return {
                    "study_plan": {
                        "overview": response.text.strip(),
                        "time_breakdown": {"total": f"{study_time} phút"},
                        "learning_objectives": ["Học nội dung đã cung cấp"],
                        "study_steps": [],
                        "key_concepts": [],
                        "practice_suggestions": [],
                        "assessment_methods": [],
                    },
                    "difficulty_assessment": f"Trình độ {difficulty_level}",
                    "additional_resources": [],
                }

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            raise e
