import os
import logging
from typing import Optional, List, Dict
from dotenv import load_dotenv

import requests
import json

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


class GeminiEvaluationAdapter:
    """Adapter for Google Gemini API cho Quiz Evaluation Analysis.

    Expects environment variables:
    - GEMINI_API_KEY (required)
    - GEMINI_MODEL (optional, defaults to gemini-2.5-flash)
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")

        self.model = model or os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
        self.base_url = "https://generativelanguage.googleapis.com/v1/models"

    def analyze_quiz_results(
        self,
        quiz_data: Dict,
        correct_count: int,
        total_count: int,
        topic_breakdown: List[Dict],
        max_tokens: int = 1500,
        temperature: float = 0.3,
    ) -> str:
        """Phân tích kết quả quiz và đưa ra đề xuất cải thiện."""

        # Allow canned response for testing
        use_canned = os.environ.get("USE_CANNED_LLM", "0").lower() in (
            "1",
            "true",
            "yes",
        )
        if use_canned:
            logger.info("Using canned evaluation analysis response")

            # Sample analysis result
            canned_analysis = {
                "strengths": [
                    "Hiểu tốt về khái niệm cơ bản của Python",
                    "Nắm vững cú pháp biến và kiểu dữ liệu",
                    "Làm tốt các câu hỏi true/false",
                ],
                "weaknesses": [
                    "Cần cải thiện về vòng lặp và hàm",
                    "Chưa nắm chắc về lập trình hướng đối tượng",
                    "Hay nhầm lẫn khi làm câu hỏi điền khuyết",
                ],
                "recommendations": [
                    "Học lại phần Functions và Parameters trong Python",
                    "Làm thêm bài tập về Classes và Objects",
                    "Ôn luyện cú pháp vòng lặp for và while",
                ],
                "study_plan": [
                    "Tuần 1: Ôn tập Functions - làm 10 bài tập cơ bản",
                    "Tuần 2: Học sâu về OOP - theory + practice",
                    "Tuần 3: Củng cố với project nhỏ kết hợp tất cả",
                ],
                "overall_feedback": "Bạn đã có nền tảng tốt về Python cơ bản. Tập trung vào các khái niệm nâng cao sẽ giúp bạn cải thiện đáng kể kết quả.",
                "improvement_areas": [
                    "Lập trình hướng đối tượng (OOP)",
                    "Cú pháp Functions và Parameters",
                    "Xử lý lỗi và debugging",
                ],
            }
            return json.dumps(canned_analysis, ensure_ascii=False)

        # Build analysis prompt
        prompt = self._build_analysis_prompt(
            quiz_data, correct_count, total_count, topic_breakdown
        )

        # Try different model names if default fails
        model_names = [
            self.model,
            "gemini-2.5-flash",
            "gemini-2.5-pro",
            "gemini-2.0-flash",
        ]

        # Remove duplicates while preserving order
        seen = set()
        model_names = [x for x in model_names if not (x in seen or seen.add(x))]

        headers = {"Content-Type": "application/json"}

        # Construct the request payload for Gemini API
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
                "candidateCount": 1,
            },
        }

        last_error = None

        for model_name in model_names:
            url = f"{self.base_url}/{model_name}:generateContent"
            params = {"key": self.api_key}

            try:
                logger.info(f"Trying Gemini model: {model_name}")
                resp = requests.post(
                    url, json=payload, headers=headers, params=params, timeout=60
                )
                resp.raise_for_status()

                data = resp.json()

                # Extract text from Gemini response
                if "candidates" in data and len(data["candidates"]) > 0:
                    candidate = data["candidates"][0]

                    # Check for text content in parts (older format)
                    if "content" in candidate and "parts" in candidate["content"]:
                        parts = candidate["content"]["parts"]
                        if len(parts) > 0 and "text" in parts[0]:
                            logger.info(f"Successfully used model: {model_name}")
                            return parts[0]["text"]

                    # Check for text directly in content (newer format)
                    elif "content" in candidate and "text" in candidate["content"]:
                        logger.info(f"Successfully used model: {model_name}")
                        return candidate["content"]["text"]

                    # Check finish reason
                    elif candidate.get("finishReason") == "MAX_TOKENS":
                        logger.warning(
                            f"Model {model_name} hit MAX_TOKENS, trying next model"
                        )
                        last_error = f"Model {model_name} hit MAX_TOKENS limit"
                        continue

                    else:
                        logger.warning(
                            f"No text content in response from model {model_name}: {candidate}"
                        )
                        last_error = (
                            f"No text content in response from model {model_name}"
                        )
                        continue

                # If no candidates, try next model
                logger.warning(f"No candidates in response from model {model_name}")
                last_error = f"No candidates in response from model {model_name}"
                continue

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    logger.warning(
                        f"Model {model_name} not found (404), trying next model"
                    )
                    last_error = f"Model {model_name} not found: {e}"
                    continue
                else:
                    logger.error(f"HTTP error with model {model_name}: {e}")
                    last_error = f"HTTP error with model {model_name}: {e}"
                    continue
            except Exception as e:
                logger.error(f"Unexpected error with model {model_name}: {e}")
                last_error = f"Unexpected error with model {model_name}: {e}"
                continue

        # If all models failed, raise the last error
        error_msg = f"All Gemini models failed. Last error: {last_error}"
        logger.exception(error_msg)
        raise RuntimeError(error_msg)

    def _build_analysis_prompt(
        self,
        quiz_data: Dict,
        correct_count: int,
        total_count: int,
        topic_breakdown: List[Dict],
    ) -> str:
        """Xây dựng prompt cho phân tích kết quả quiz."""

        score_percent = (correct_count / total_count * 100) if total_count > 0 else 0

        # Build topic analysis summary
        topic_summary = ""
        for topic in topic_breakdown:
            topic_summary += f"- {topic['topic']}: {topic['correct_answers']}/{topic['total_questions']} đúng ({topic['accuracy_rate']:.1f}%)\n"

        # Build prompt for Vietnamese analysis
        prompt = f"""Bạn là chuyên gia đánh giá giáo dục, hãy phân tích kết quả bài kiểm tra sau và đưa ra lời khuyên cải thiện bằng tiếng Việt.

THÔNG TIN BÀI KIỂM TRA:
- Tổng số câu: {total_count}
- Số câu đúng: {correct_count}
- Điểm số: {score_percent:.1f}%

PHÂN TÍCH THEO CHỦ ĐỀ:
{topic_summary}

CHI TIẾT CÂU HỎI SAI:
{self._format_wrong_answers(quiz_data)}

Hãy phân tích và trả về JSON với format chính xác sau (không thêm markdown hay text khác):

{{
  "strengths": ["Điểm mạnh 1", "Điểm mạnh 2", "..."],
  "weaknesses": ["Điểm yếu 1", "Điểm yếu 2", "..."], 
  "recommendations": ["Đề xuất 1", "Đề xuất 2", "..."],
  "study_plan": ["Kế hoạch học tập tuần 1", "Tuần 2", "..."],
  "overall_feedback": "Nhận xét tổng quan chi tiết về kết quả",
  "improvement_areas": ["Lĩnh vực cần cải thiện 1", "Lĩnh vực 2", "..."]
}}

YÊU CẦU:
- Phân tích dựa trên dữ liệu cụ thể
- Đưa ra lời khuyên thiết thực và có thể thực hiện
- Sử dụng tiếng Việt tự nhiên, dễ hiểu
- Tập trung vào cải thiện năng lực học tập
- Khích lệ tích cực, xây dựng"""

        return prompt

    def _format_wrong_answers(self, quiz_data: Dict) -> str:
        """Format thông tin câu trả lời sai để đưa vào prompt."""
        wrong_answers = []

        for question in quiz_data.get("questions", []):
            user_ans = question.get("user_answer", "").strip()
            correct_ans = question.get("correct_answer", "").strip()

            if user_ans != correct_ans:
                topic = question.get("topic", "Unknown")
                qtype = question.get("type", "unknown")
                stem = (
                    question.get("stem", "")[:100] + "..."
                    if len(question.get("stem", "")) > 100
                    else question.get("stem", "")
                )

                wrong_answers.append(
                    f"- [{topic}] [{qtype}] {stem} | Đáp án đúng: {correct_ans} | Người dùng chọn: {user_ans or 'Không trả lời'}"
                )

        return (
            "\n".join(wrong_answers) if wrong_answers else "Không có câu trả lời sai."
        )


__all__ = ["GeminiEvaluationAdapter"]
