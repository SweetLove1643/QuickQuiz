import os
import logging
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import time
from schemas import ChatConfig

# Load environment variables from parent directory
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

logger = logging.getLogger(__name__)


class GeminiChatAdapter:
    """Gemini LLM adapter tối ưu cho RAG chatbot conversations."""

    def __init__(self):
        """Initialize Gemini chat adapter."""
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.default_model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        logger.info(
            f"GEMINI_API_KEY loaded: {'***' + self.api_key[-4:] if self.api_key else 'None'}"
        )
        logger.info(f"Default model: {self.default_model}")
        # Enable canned responses by default for development
        use_canned_env = os.getenv("USE_CANNED_LLM", "true")
        self.use_canned_responses = use_canned_env.lower() == "true"

        logger.info(
            f"USE_CANNED_LLM env: '{use_canned_env}', use_canned_responses: {self.use_canned_responses}"
        )

        # Model fallback order for chat (working models only)
        self.model_fallback = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.5-pro"]

        self.current_model = self.default_model

        if not self.use_canned_responses:
            if not self.api_key:
                raise ValueError("GEMINI_API_KEY không được cung cấp trong .env file")
            genai.configure(api_key=self.api_key)
            logger.info(
                f"Gemini Chat Adapter initialized với model: {self.default_model}"
            )
        else:
            logger.info("Using canned responses for chat (development mode)")

    def generate_response(
        self, messages: List[Dict[str, str]], config: ChatConfig
    ) -> str:
        """
        Generate chat response từ conversation messages.

        Args:
            messages: List of messages [{"role": "system/user/assistant", "content": "..."}]
            config: Chat configuration

        Returns:
            Generated response text
        """
        if self.use_canned_responses:
            logger.info(
                f"Using canned responses (use_canned={self.use_canned_responses})"
            )
            return self._get_canned_response(messages)

        return self._generate_with_retry(messages, config)

    def _generate_with_retry(
        self, messages: List[Dict[str, str]], config: ChatConfig
    ) -> str:
        """Generate response với retry logic across models."""

        for model_name in self.model_fallback:
            try:
                self.current_model = model_name
                logger.info(f"Trying chat generation với model: {model_name}")

                # Create model instance
                model = genai.GenerativeModel(
                    model_name=model_name,
                    generation_config={
                        "temperature": config.temperature,
                        "top_p": config.top_p,
                        "max_output_tokens": config.max_tokens,
                        "candidate_count": 1,
                    },
                    safety_settings={
                        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                    },
                )

                # Convert messages to Gemini format
                formatted_messages = self._format_messages_for_gemini(messages)

                # Generate response
                response = model.generate_content(formatted_messages)

                if response.text:
                    logger.info(
                        f"Chat response generated successfully với {model_name}"
                    )
                    return response.text.strip()
                else:
                    logger.warning(f"Empty response từ model {model_name}")
                    continue

            except Exception as e:
                logger.warning(f"Model {model_name} failed: {str(e)}")
                if "quota" in str(e).lower() or "limit" in str(e).lower():
                    time.sleep(2)  # Rate limit backoff
                continue

        # All models failed
        logger.error("All Gemini models failed for chat generation")
        return (
            "Xin lỗi, tôi không thể trả lời câu hỏi này lúc này. Vui lòng thử lại sau."
        )

    def _format_messages_for_gemini(self, messages: List[Dict[str, str]]) -> str:
        """
        Convert conversation messages thành format cho Gemini.

        Gemini không support native conversation format, nên concat thành single prompt.
        """
        formatted_parts = []

        for message in messages:
            role = message["role"]
            content = message["content"]

            if role == "system":
                formatted_parts.append(f"[Hướng dẫn hệ thống]\n{content}\n")
            elif role == "user":
                formatted_parts.append(f"[Người dùng]\n{content}\n")
            elif role == "assistant":
                formatted_parts.append(f"[Trợ lý]\n{content}\n")

        # Add explicit instruction for current response
        formatted_parts.append("[Trợ lý] (hãy trả lời câu hỏi mới nhất):")

        return "\n".join(formatted_parts)

    def _get_canned_response(self, messages: List[Dict[str, str]]) -> str:
        """Generate canned response cho development testing."""

        # Get the last user message
        user_messages = [msg for msg in messages if msg["role"] == "user"]
        if not user_messages:
            return "Bạn có câu hỏi gì không?"

        full_content = user_messages[-1]["content"]

        # Extract original query từ RAG-formatted content
        if "=== câu hỏi ===" in full_content.lower():
            # Extract query after "=== câu hỏi ==="
            parts = full_content.lower().split("=== câu hỏi ===")
            if len(parts) > 1:
                # Get text after the marker and before any additional instructions
                query_part = parts[1].strip()
                # Extract just the query line (first line after marker)
                query_lines = query_part.split("\n")
                last_query = query_lines[0].strip() if query_lines else query_part
            else:
                last_query = full_content.lower()
        else:
            # Fallback to full content if no RAG format
            last_query = full_content.lower()

        # Enhanced keyword matching for RAG canned responses
        canned_responses = {
            "python": """Dựa trên tài liệu về Python programming, Python có những ưu điểm nổi bật sau:

• Cú pháp đơn giản: Python sử dụng cú pháp rõ ràng và dễ đọc như tiếng Anh
• Dynamic typing: Biến không cần khai báo kiểu dữ liệu trước (x = 10, name = 'Alice')  
• Đa paradigm: Hỗ trợ lập trình hướng đối tượng với class và object
• Thư viện phong phú: List, Dictionary và nhiều cấu trúc dữ liệu mạnh mẽ
• Dễ học: Được thiết kế với triết lý đơn giản và dễ đọc

Ứng dụng chính: Web development (Django, Flask), Data science và AI/ML, Automation và scripting.

Python rất phù hợp cho người mới bắt đầu lập trình.""",
            "javascript": """Theo tài liệu về JavaScript, đây là ngôn ngữ lập trình chính cho web development.

Đặc điểm của JavaScript:
• Chạy trên browser và server (Node.js)
• Dynamic typing và flexible syntax
• Event-driven programming model
• Rich ecosystem với NPM packages

JavaScript là nền tảng cho các framework hiện đại như React, Vue, Angular và được sử dụng để tạo interactive web applications.""",
            "database": """Dựa trên tài liệu về cơ sở dữ liệu, có nhiều loại database phù hợp cho các use case khác nhau:

**Relational Databases (SQL):**
• MySQL, PostgreSQL, SQL Server
• ACID compliance và strong consistency
• Phù hợp cho transactional applications

**NoSQL Databases:**
• MongoDB (document-based)
• Redis (key-value store)
• Elasticsearch (search engine)

Việc chọn database phụ thuộc vào yêu cầu về data structure, scalability và consistency.""",
            "api": """Theo tài liệu về API development, REST API là standard phổ biến nhất cho web services:

**REST API Principles:**
• Stateless communication
• HTTP methods (GET, POST, PUT, DELETE)
• JSON data format
• Consistent URL patterns

**Best practices:**
• Proper status codes
• Authentication & authorization  
• Rate limiting
• Comprehensive documentation
• Error handling

Modern alternatives bao gồm GraphQL cho flexible queries và gRPC cho high-performance services.""",
        }

        # Check for keywords và return appropriate response
        for keyword, response in canned_responses.items():
            if keyword in last_query:
                return response

        # Default canned response
        return """Tôi hiểu câu hỏi của bạn. Dựa trên các tài liệu có sẵn, đây là những thông tin liên quan:

• Các tài liệu chứa nhiều chủ đề về công nghệ và lập trình
• Bao gồm Python, JavaScript, databases, và web development
• Mỗi tài liệu cung cấp thông tin chi tiết và practical examples

Bạn có thể đặt câu hỏi cụ thể hơn về một chủ đề để tôi tìm kiếm thông tin chính xác từ tài liệu phù hợp."""

    def get_model_info(self) -> Dict[str, Any]:
        """Get current model information."""
        return {
            "current_model": self.current_model,
            "available_models": self.model_fallback,
            "using_canned": self.use_canned_responses,
            "api_configured": bool(self.api_key) and not self.use_canned_responses,
        }


__all__ = ["GeminiChatAdapter"]
