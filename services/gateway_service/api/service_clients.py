import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import requests
import logging
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
from django.conf import settings
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


@dataclass
class ServiceResponse:
    success: bool
    data: Optional[Dict[str, Any]]
    error: Optional[str]
    status_code: int
    response_time: float
    service_name: str


class ServiceClientError(Exception):
    def __init__(self, message: str, status_code: int = None, service_name: str = None):
        super().__init__(message)
        self.status_code = status_code
        self.service_name = service_name


class BaseServiceClient:
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.config = settings.MICROSERVICES.get(service_name)

        if not self.config:
            raise ValueError(f"Service '{service_name}' not configured in settings")

        self.base_url = self.config["base_url"]
        # Timeout mặc định 300s cho các tác vụ nặng (OCR, Summary)
        # Nếu cần thay đổi, điều chỉnh giá trị này hoặc trong config
        self.timeout = self.config.get("timeout", 300)
        self.retry_count = self.config.get("retry_count", 3)

        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        session = requests.Session()

        retry_strategy = Retry(
            total=self.retry_count,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],
            backoff_factor=1,
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        timeout: Optional[int] = None,
        **kwargs,
    ) -> ServiceResponse:
        url = f"{self.base_url}{endpoint}"
        start_time = time.time()

        try:
            logger.debug(f"[{self.service_name}] {method} {url}")
            effective_timeout = timeout or self.timeout

            if "files" in kwargs:
                response = self.session.request(
                    method=method,
                    url=url,
                    params=params,
                    timeout=effective_timeout,
                    **kwargs,
                )
            else:
                response = self.session.request(
                    method=method,
                    url=url,
                    json=data,
                    params=params,
                    headers={"Content-Type": "application/json"},
                    timeout=effective_timeout,
                    **kwargs,
                )

            response_time = time.time() - start_time

            if response_time > 5.0:
                logger.warning(
                    f"[{self.service_name}] Slow request: {response_time:.2f}s"
                )

            response.raise_for_status()

            try:
                response_data = response.json()
            except ValueError:
                response_data = {"raw_content": response.text}

            return ServiceResponse(
                success=True,
                data=response_data,
                error=None,
                status_code=response.status_code,
                response_time=response_time,
                service_name=self.service_name,
            )

        except requests.exceptions.ConnectionError as e:
            error_msg = f"Connection failed to {self.service_name}"
            logger.error(f"[{self.service_name}] {error_msg}: {e}")

            return ServiceResponse(
                success=False,
                data=None,
                error=error_msg,
                status_code=503,
                response_time=time.time() - start_time,
                service_name=self.service_name,
            )

        except requests.exceptions.HTTPError as e:
            response_time = time.time() - start_time
            status_code = e.response.status_code if e.response else 500

            try:
                error_data = e.response.json() if e.response else {}
                error_msg = error_data.get("error", str(e))
            except ValueError:
                error_msg = e.response.text if e.response else str(e)

            logger.error(f"[{self.service_name}] HTTP {status_code}: {error_msg}")

            return ServiceResponse(
                success=False,
                data=None,
                error=f"HTTP {status_code}: {error_msg}",
                status_code=status_code,
                response_time=response_time,
                service_name=self.service_name,
            )

        except requests.exceptions.Timeout as e:
            error_msg = f"Request timeout after {self.timeout}s"
            logger.error(f"[{self.service_name}] {error_msg}")

            return ServiceResponse(
                success=False,
                data=None,
                error=error_msg,
                status_code=408,
                response_time=self.timeout,
                service_name=self.service_name,
            )

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"[{self.service_name}] {error_msg}")

            return ServiceResponse(
                success=False,
                data=None,
                error=error_msg,
                status_code=500,
                response_time=time.time() - start_time,
                service_name=self.service_name,
            )

    def health_check(self) -> Dict[str, Any]:
        health_endpoint = self.config.get("health_endpoint", "/health")
        response = self._make_request("GET", health_endpoint)

        if response.success:
            health_data = response.data or {}
            return {
                "status": ServiceStatus.HEALTHY.value,
                "service": self.service_name,
                "version": health_data.get("version", "unknown"),
                "response_time": round(response.response_time, 3),
                **health_data,
            }
        else:
            return {
                "status": ServiceStatus.UNHEALTHY.value,
                "service": self.service_name,
                "error": response.error,
                "response_time": round(response.response_time, 3),
            }

    def get_service_info(self) -> Dict[str, Any]:
        return {
            "name": self.service_name,
            "base_url": self.base_url,
            "timeout": self.timeout,
            "retry_count": self.retry_count,
            "health_endpoint": self.config.get("health_endpoint", "/health"),
        }


class QuizGeneratorClient(BaseServiceClient):

    def __init__(self):
        super().__init__("quiz_generator")

    def generate_quiz(
        self, sections: List[Dict], config: Dict[str, Any]
    ) -> Dict[str, Any]:
        payload = {"sections": sections, "config": config}

        logger.info(
            f"[{self.service_name}] Generating quiz: {len(sections)} sections, {config.get('n_questions', 'unknown')} questions"
        )

        response = self._make_request("POST", "/quiz/generate", data=payload)

        if not response.success:
            raise ServiceClientError(
                response.error, response.status_code, self.service_name
            )

        result = response.data

        if "metadata" in result:
            metadata = result["metadata"]
            total_generated = metadata.get("total_generated", 0)
            total_validated = metadata.get("total_validated", 0)
            filtered_count = metadata.get("filtered_count", 0)

            logger.info(
                f"[{self.service_name}] Quiz generated successfully: {total_validated}/{total_generated} questions validated"
            )

            if filtered_count > 0:
                logger.warning(
                    f"[{self.service_name}] Filtered {filtered_count} high-risk questions"
                )

        result["gateway_response_meta"] = {
            "response_time": response.response_time,
            "service": self.service_name,
            "timestamp": time.time(),
        }

        return result

    def save_quiz(self, quiz_payload: Dict[str, Any]) -> Dict[str, Any]:
        response = self._make_request("POST", "/quiz/save", data=quiz_payload)

        if not response.success:
            raise ServiceClientError(
                response.error, response.status_code, self.service_name
            )

        return response.data or {}

    def get_user_quizzes(
        self, user_id: str, limit: int = 50, offset: int = 0
    ) -> Dict[str, Any]:
        response = self._make_request(
            "GET", f"/quiz/user/{user_id}", params={"limit": limit, "offset": offset}
        )

        if not response.success:
            raise ServiceClientError(
                response.error, response.status_code, self.service_name
            )

        return response.data or {}

    def get_user_recent_quizzes(self, user_id: str, limit: int = 10) -> Dict[str, Any]:
        response = self._make_request(
            "GET", f"/quiz/user/{user_id}/recent", params={"limit": limit}
        )

        if not response.success:
            raise ServiceClientError(
                response.error, response.status_code, self.service_name
            )

        return response.data or {}

    def get_quiz_details(self, quiz_id: str) -> Dict[str, Any]:
        response = self._make_request("GET", f"/quiz/{quiz_id}")

        if not response.success:
            raise ServiceClientError(
                response.error, response.status_code, self.service_name
            )

        return response.data or {}

    def delete_quiz(self, quiz_id: str) -> Dict[str, Any]:
        response = self._make_request("DELETE", f"/quiz/{quiz_id}")

        if not response.success:
            raise ServiceClientError(
                response.error, response.status_code, self.service_name
            )

        return response.data or {}

    def get_generator_info(self) -> Dict[str, Any]:
        response = self._make_request("GET", "/")

        if response.success:
            return response.data
        else:
            return {"error": response.error}


class OCRServiceClient(BaseServiceClient):

    def __init__(self):
        super().__init__("ocr_service")

    def extract_text_single(
        self, file_data: bytes, filename: str, content_type: str
    ) -> Dict[str, Any]:
        files = {"file": (filename, file_data, content_type)}

        logger.info(
            f"[{self.service_name}] Extracting text from single image: {filename}"
        )

        # Timeout = 300s
        response = self._make_request("POST", "/extract_text", files=files, timeout=300)

        if not response.success:
            raise ServiceClientError(
                response.error, response.status_code, self.service_name
            )

        return response.data

    def extract_text_multi(self, files_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        files = [
            (
                "files",
                (file_info["filename"], file_info["data"], file_info["content_type"]),
            )
            for file_info in files_data
        ]

        logger.info(
            f"[{self.service_name}] Extracting text from {len(files_data)} images"
        )

        # Timeout = 300s
        response = self._make_request(
            "POST", "/extract_text_multi", files=files, timeout=300
        )

        if not response.success:
            raise ServiceClientError(
                response.error, response.status_code, self.service_name
            )

        return response.data

    def extract_information_legacy(
        self, files_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        files = [
            (
                "files",
                (file_info["filename"], file_info["data"], file_info["content_type"]),
            )
            for file_info in files_data
        ]

        logger.info(
            f"[{self.service_name}] Legacy extraction from {len(files_data)} images"
        )

        # Timeout = 300s
        response = self._make_request(
            "POST", "/extract_information", files=files, timeout=300
        )

        if not response.success:
            raise ServiceClientError(
                response.error, response.status_code, self.service_name
            )

        return response.data


class SummaryServiceClient(BaseServiceClient):

    def __init__(self):
        super().__init__("summary_service")

    def summarize_text(self, text: str) -> Dict[str, Any]:
        data = {"text": text}

        logger.info(f"[{self.service_name}] Summarizing text: {len(text)} characters")

        # Timeout = 300s
        response = self._make_request("POST", "/summarize_text", data=data, timeout=300)

        if not response.success:
            raise ServiceClientError(
                response.error, response.status_code, self.service_name
            )

        return response.data

    def ocr_and_summarize(self, files_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        files = [
            (
                "files",
                (file_info["filename"], file_info["data"], file_info["content_type"]),
            )
            for file_info in files_data
        ]

        logger.info(
            f"[{self.service_name}] OCR and summarize from {len(files_data)} files"
        )

        # Timeout = 300s
        response = self._make_request(
            "POST", "/ocr_and_summarize", files=files, timeout=300
        )

        if not response.success:
            raise ServiceClientError(
                response.error, response.status_code, self.service_name
            )

        return response.data

    def recommend_study(
        self, content: str, difficulty_level: str = "intermediate", study_time: int = 60
    ) -> Dict[str, Any]:
        data = {
            "content": content,
            "difficulty_level": difficulty_level,
            "study_time": study_time,
        }

        logger.info(
            f"[{self.service_name}] Generating recommendations for {difficulty_level} level"
        )

        # Timeout = 300s
        response = self._make_request(
            "POST", "/recommend_study", data=data, timeout=300
        )

        if not response.success:
            raise ServiceClientError(
                response.error, response.status_code, self.service_name
            )

        return response.data

    def image_ocr_legacy(self, files_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        files = [
            (
                "files",
                (file_info["filename"], file_info["data"], file_info["content_type"]),
            )
            for file_info in files_data
        ]

        logger.info(f"[{self.service_name}] Legacy OCR from {len(files_data)} files")

        # Timeout = 300s
        response = self._make_request("POST", "/image_ocr", files=files, timeout=300)

        if not response.success:
            raise ServiceClientError(
                response.error, response.status_code, self.service_name
            )

        return response.data


class QuizEvaluatorClient(BaseServiceClient):

    def __init__(self):
        super().__init__("quiz_evaluator")

    def evaluate_quiz(
        self, submission: Dict[str, Any], config: Dict[str, Any]
    ) -> Dict[str, Any]:
        payload = {"submission": submission, "config": config}

        quiz_id = submission.get("quiz_id", "unknown")
        questions_count = len(submission.get("questions", []))

        logger.info(
            f"[{self.service_name}] Evaluating quiz {quiz_id} with {questions_count} questions"
        )

        response = self._make_request("POST", "/quiz/evaluate", data=payload)

        if not response.success:
            raise ServiceClientError(
                response.error, response.status_code, self.service_name
            )

        result = response.data

        if "summary" in result:
            summary = result["summary"]
            score = summary.get("score_percentage", 0)
            correct_answers = summary.get("correct_answers", 0)
            total_questions = summary.get("total_questions", 0)

            logger.info(
                f"[{self.service_name}] Quiz {quiz_id} evaluated: {score:.1f}% ({correct_answers}/{total_questions})"
            )

        result["gateway_response_meta"] = {
            "response_time": response.response_time,
            "service": self.service_name,
            "timestamp": time.time(),
        }

        return result

    def get_grading_scale(self) -> Dict[str, Any]:
        response = self._make_request("GET", "/quiz/grading-scale")

        if not response.success:
            raise ServiceClientError(
                response.error, response.status_code, self.service_name
            )

        return response.data

    def get_user_results(
        self, user_id: str, limit: int = 50, offset: int = 0
    ) -> Dict[str, Any]:
        response = self._make_request(
            "GET", f"/results/user/{user_id}", params={"limit": limit, "offset": offset}
        )

        if not response.success:
            raise ServiceClientError(
                response.error, response.status_code, self.service_name
            )

        return response.data or {}

    def get_user_recent_results(self, user_id: str, limit: int = 10) -> Dict[str, Any]:
        response = self._make_request(
            "GET", f"/results/user/{user_id}/recent", params={"limit": limit}
        )

        if not response.success:
            raise ServiceClientError(
                response.error, response.status_code, self.service_name
            )

        return response.data or {}

    def get_evaluator_info(self) -> Dict[str, Any]:
        response = self._make_request("GET", "/")

        if response.success:
            return response.data
        else:
            return {"error": response.error}


class RAGChatbotClient(BaseServiceClient):

    def __init__(self):
        super().__init__("rag_chatbot_service")

    def chat(
        self,
        query: str,
        conversation_id: Optional[str] = None,
        retrieval_config: Optional[Dict] = None,
        chat_config: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        data = {
            "query": query,
            "conversation_id": conversation_id,
            "retrieval_config": retrieval_config
            or {"top_k": 5, "similarity_threshold": 0.3},
            "chat_config": chat_config or {"temperature": 0.7, "max_tokens": 1000},
        }

        logger.info(f"[{self.service_name}] Processing chat query: {query[:50]}...")

        response = self._make_request("POST", "/chat", data=data)

        if not response.success:
            raise ServiceClientError(
                response.error, response.status_code, self.service_name
            )

        return response.data

    def get_conversation_history(
        self, conversation_id: str, limit: int = 10
    ) -> Dict[str, Any]:
        params = {"limit": limit}

        logger.info(
            f"[{self.service_name}] Getting history for conversation {conversation_id[:8]}"
        )

        response = self._make_request(
            "GET", f"/conversations/{conversation_id}", params=params
        )

        if not response.success:
            raise ServiceClientError(
                response.error, response.status_code, self.service_name
            )

        return response.data

    def list_conversations(self, limit: int = 20) -> Dict[str, Any]:
        params = {"limit": limit}

        logger.info(f"[{self.service_name}] Listing conversations")

        response = self._make_request("GET", "/conversations", params=params)

        if not response.success:
            raise ServiceClientError(
                response.error, response.status_code, self.service_name
            )

        return response.data


class IAMServiceClient(BaseServiceClient):

    def __init__(self):
        super().__init__("iam_service")

    def register_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(
            f"[{self.service_name}] Registering user: {user_data.get('username')}"
        )

        payload = {
            "username": user_data.get("username", ""),
            "email": user_data.get("email", ""),
            "password": user_data.get("password", ""),
            "password_confirm": user_data.get(
                "password_confirm", user_data.get("password", "")
            ),
            "first_name": user_data.get("first_name", ""),
            "last_name": user_data.get("last_name", ""),
            "role": user_data.get("role", "student"),
            "phone_number": user_data.get("phone_number", ""),
            "avatar_url": user_data.get("avatar_url", ""),
        }

        response = self._make_request("POST", "/api/users/", data=payload)

        if not response.success:
            raise ServiceClientError(
                response.error, response.status_code, self.service_name
            )

        return response.data

    def login(self, username: str, password: str) -> Dict[str, Any]:
        logger.info(f"[{self.service_name}] Login attempt for user: {username}")

        data = {"username": username, "password": password}
        response = self._make_request("POST", "/api/users/login/", data=data)

        if not response.success:
            logger.warning(f"[{self.service_name}] Login failed for user: {username}")
            raise ServiceClientError(
                response.error, response.status_code, self.service_name
            )

        logger.info(f"[{self.service_name}] Login successful for user: {username}")
        return response.data

    def logout(self, refresh_token: str) -> Dict[str, Any]:
        logger.info(f"[{self.service_name}] Logging out user")

        data = {"refresh": refresh_token}
        response = self._make_request("POST", "/api/users/logout/", data=data)

        if not response.success:
            raise ServiceClientError(
                response.error, response.status_code, self.service_name
            )

        return response.data

    def get_current_user(self, access_token: str) -> Dict[str, Any]:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = self._make_request("GET", "/api/users/me/", headers=headers)

        if not response.success:
            raise ServiceClientError(
                response.error, response.status_code, self.service_name
            )

        return response.data

    def get_user(self, user_id: str, access_token: str) -> Dict[str, Any]:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = self._make_request("GET", f"/api/users/{user_id}/", headers=headers)

        if not response.success:
            raise ServiceClientError(
                response.error, response.status_code, self.service_name
            )

        return response.data

    def update_user(
        self, user_id: str, access_token: str, user_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = self._make_request(
            "PUT", f"/api/users/{user_id}/", data=user_data, headers=headers
        )

        if not response.success:
            raise ServiceClientError(
                response.error, response.status_code, self.service_name
            )

        return response.data

    def change_password(
        self, user_id: str, access_token: str, password_data: Dict[str, str]
    ) -> Dict[str, Any]:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = self._make_request(
            "POST",
            f"/api/users/{user_id}/change_password/",
            data=password_data,
            headers=headers,
        )

        if not response.success:
            raise ServiceClientError(
                response.error, response.status_code, self.service_name
            )

        return response.data

    def list_users(
        self, access_token: str, page: int = 1, search: str = ""
    ) -> Dict[str, Any]:
        headers = {"Authorization": f"Bearer {access_token}"}
        params = {"page": page}
        if search:
            params["search"] = search

        response = self._make_request(
            "GET", "/api/users/", params=params, headers=headers
        )

        if not response.success:
            raise ServiceClientError(
                response.error, response.status_code, self.service_name
            )

        return response.data

    def verify_token(self, access_token: str) -> bool:
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            response = self._make_request("GET", "/api/users/me/", headers=headers)
            return response.success
        except:
            return False

    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        data = {"refresh": refresh_token}
        response = self._make_request("POST", "/api/token/refresh/", data=data)

        if not response.success:
            raise ServiceClientError(
                response.error, response.status_code, self.service_name
            )

        return response.data


class ServiceRegistry:
    def __init__(self):
        self.clients = {
            "quiz_generator": QuizGeneratorClient(),
            "quiz_evaluator": QuizEvaluatorClient(),
            "ocr_service": OCRServiceClient(),
            "summary_service": SummaryServiceClient(),
            "rag_chatbot_service": RAGChatbotClient(),
            "iam_service": IAMServiceClient(),
        }

    def get_client(self, service_name: str) -> BaseServiceClient:
        if service_name not in self.clients:
            raise ValueError(f"Unknown service: {service_name}")
        return self.clients[service_name]

    def health_check_all(self) -> Dict[str, Dict[str, Any]]:
        health_results = {}

        for service_name, client in self.clients.items():
            try:
                health_results[service_name] = client.health_check()
            except Exception as e:
                logger.error(f"Health check failed for {service_name}: {e}")
                health_results[service_name] = {
                    "status": ServiceStatus.UNKNOWN.value,
                    "error": str(e),
                }

        return health_results

    def get_services_info(self) -> Dict[str, Dict[str, Any]]:
        return {
            service_name: client.get_service_info()
            for service_name, client in self.clients.items()
        }


service_registry = ServiceRegistry()

quiz_generator_client = service_registry.get_client("quiz_generator")
quiz_evaluator_client = service_registry.get_client("quiz_evaluator")
ocr_service_client = service_registry.get_client("ocr_service")
summary_service_client = service_registry.get_client("summary_service")
rag_chatbot_client = service_registry.get_client("rag_chatbot_service")
iam_service_client = service_registry.get_client("iam_service")
