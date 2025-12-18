import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.views import View
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.conf import settings
from rest_framework.response import Response
from .service_clients import (
    QuizGeneratorClient,
    QuizEvaluatorClient,
    OCRServiceClient,
    SummaryServiceClient,
    RAGChatbotClient,
    IAMServiceClient,
)
from .rag_sync_helper import insert_document_to_rag_db
import json
import io
import os
import sqlite3
from contextlib import closing

logger = logging.getLogger(__name__)

# Document storage (lightweight sqlite)
DOCUMENT_DB_PATH = os.path.abspath(os.path.join(settings.BASE_DIR, "documents.db"))


def ensure_document_table():
    os.makedirs(os.path.dirname(DOCUMENT_DB_PATH), exist_ok=True)
    with closing(sqlite3.connect(DOCUMENT_DB_PATH)) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                file_name TEXT NOT NULL,
                file_size INTEGER,
                file_type TEXT,
                extracted_text TEXT,
                summary TEXT,
                created_at TEXT
            )
            """
        )
        conn.commit()


def insert_document(record: dict):
    ensure_document_table()
    with closing(sqlite3.connect(DOCUMENT_DB_PATH)) as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO documents
            (id, file_name, file_size, file_type, extracted_text, summary, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.get("document_id"),
                record.get("file_name"),
                record.get("file_size"),
                record.get("file_type"),
                record.get("extracted_text"),
                record.get("summary"),
                record.get("created_at"),
            ),
        )
        conn.commit()


def fetch_documents(limit: int = 50):
    if not os.path.exists(DOCUMENT_DB_PATH):
        return []
    with closing(sqlite3.connect(DOCUMENT_DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, file_name, file_size, file_type, extracted_text, summary, created_at
            FROM documents
            ORDER BY datetime(created_at) DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = cur.fetchall()
        return [dict(row) for row in rows]


# Initialize service clients
quiz_generator = QuizGeneratorClient()
quiz_evaluator = QuizEvaluatorClient()
ocr_service = OCRServiceClient()
summary_service = SummaryServiceClient()
rag_chatbot = RAGChatbotClient()
iam_service = IAMServiceClient()


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    """
    Health check endpoint for the API Gateway
    """
    try:
        # Check microservices health
        generator_health = quiz_generator.health_check()
        evaluator_health = quiz_evaluator.health_check()
        ocr_health = ocr_service.health_check()
        summary_health = summary_service.health_check()
        rag_health = rag_chatbot.health_check()

        return Response(
            {
                "status": "healthy",
                "timestamp": "2024-01-01T00:00:00Z",
                "services": {
                    "quiz_generator": {
                        "status": "healthy" if generator_health else "unhealthy",
                        "url": quiz_generator.base_url,
                    },
                    "quiz_evaluator": {
                        "status": "healthy" if evaluator_health else "unhealthy",
                        "url": quiz_evaluator.base_url,
                    },
                    "ocr_service": {
                        "status": "healthy" if ocr_health else "unhealthy",
                        "url": ocr_service.base_url,
                    },
                    "summary_service": {
                        "status": "healthy" if summary_health else "unhealthy",
                        "url": summary_service.base_url,
                    },
                    "rag_chatbot_service": {
                        "status": "healthy" if rag_health else "unhealthy",
                        "url": rag_chatbot.base_url,
                    },
                },
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return Response(
            {"status": "error", "message": str(e)},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


@api_view(["GET"])
@permission_classes([AllowAny])
def api_root(request):
    """
    API root endpoint with available endpoints
    """
    return Response(
        {
            "message": "QuickQuiz API Gateway",
            "version": "1.0.0",
            "endpoints": {
                "health": request.build_absolute_uri("/api/health/"),
                "generate_quiz": request.build_absolute_uri("/api/quiz/generate/"),
                "evaluate_quiz": request.build_absolute_uri("/api/quiz/evaluate/"),
            },
        }
    )


@api_view(["POST"])
@permission_classes([AllowAny])
def generate_quiz(request):
    """
    Generate quiz endpoint - proxies to quiz generator service
    """
    try:
        # Extract and validate request data
        data = request.data
        sections = data.get("sections", [])
        config = data.get("config", {})

        logger.info(
            f"Generating quiz: {len(sections)} sections, {config.get('n_questions', 'unknown')} questions"
        )

        # Call quiz generator service with correct arguments
        result = quiz_generator.generate_quiz(sections, config)

        if result:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(
                {"error": "Failed to generate quiz"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    except Exception as e:
        logger.error(f"Quiz generation failed: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([AllowAny])
def save_quiz(request):
    """Save quiz payload via quiz generator service."""
    try:
        data = request.data
        logger.info(
            f"Saving quiz with {len(data.get('questions', []))} questions and title {data.get('title')}"
        )

        result = quiz_generator.save_quiz(data)
        return Response(result, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Quiz save failed: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([AllowAny])
def evaluate_quiz(request):
    """
    Evaluate quiz endpoint - proxies to quiz evaluator service
    """
    try:
        # Extract and validate request data
        data = request.data
        submission = data.get("submission", {})
        config = data.get("config", {})

        quiz_id = submission.get("quiz_id", "unknown")
        logger.info(f"Evaluating quiz {quiz_id}")

        # Call quiz evaluator service with correct arguments
        result = quiz_evaluator.evaluate_quiz(submission, config)

        if result:
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(
                {"error": "Failed to evaluate quiz"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    except Exception as e:
        logger.error(f"Quiz evaluation failed: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([AllowAny])
def get_user_quizzes(request, user_id):
    """Get all quizzes created by a specific user."""
    try:
        limit = request.GET.get("limit", 50)
        offset = request.GET.get("offset", 0)

        result = quiz_generator.get_user_quizzes(user_id, limit, offset)
        return Response(result, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Failed to get user quizzes: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([AllowAny])
def get_user_recent_quizzes(request, user_id):
    """Get recent quizzes created by a user."""
    try:
        limit = request.GET.get("limit", 10)

        result = quiz_generator.get_user_recent_quizzes(user_id, limit)
        return Response(result, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Failed to get recent quizzes: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([AllowAny])
def get_quiz_details(request, quiz_id):
    """Get full quiz details including all questions."""
    try:
        result = quiz_generator.get_quiz_details(quiz_id)
        return Response(result, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Failed to get quiz details: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["DELETE"])
@permission_classes([AllowAny])
def delete_quiz(request, quiz_id):
    """Delete a quiz by ID."""
    try:
        result = quiz_generator.delete_quiz(quiz_id)
        return Response(result, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Failed to delete quiz: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([AllowAny])
def get_user_results(request, user_id):
    """Get all quiz results for a specific user."""
    try:
        limit = request.GET.get("limit", 50)
        offset = request.GET.get("offset", 0)

        result = quiz_evaluator.get_user_results(user_id, limit, offset)
        return Response(result, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Failed to get user results: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([AllowAny])
def get_user_recent_results(request, user_id):
    """Get recent quiz results for a user."""
    try:
        limit = request.GET.get("limit", 10)

        result = quiz_evaluator.get_user_recent_results(user_id, limit)
        return Response(result, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Failed to get recent results: {str(e)}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name="dispatch")
class QuizView(View):
    """
    Class-based view for quiz operations
    """

    def get(self, request):
        """Get quiz information"""
        return JsonResponse(
            {
                "available_operations": ["generate", "evaluate"],
                "methods": {
                    "generate": "POST /api/quiz/generate/",
                    "evaluate": "POST /api/quiz/evaluate/",
                },
            }
        )

    def post(self, request):
        """Handle quiz operations based on action parameter"""
        try:
            data = json.loads(request.body)
            action = data.get("action")

            if action == "generate":
                result = quiz_generator.generate_quiz(data)
            elif action == "evaluate":
                result = quiz_evaluator.evaluate_quiz(data)
            else:
                return JsonResponse(
                    {"error": 'Invalid action. Use "generate" or "evaluate"'},
                    status=400,
                )

            if result:
                return JsonResponse(result)
            else:
                return JsonResponse({"error": f"Failed to {action} quiz"}, status=500)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON data"}, status=400)
        except Exception as e:
            logger.error(f"Quiz operation failed: {str(e)}")
            return JsonResponse({"error": str(e)}, status=500)


# ==============================================================================
# OCR SERVICE VIEWS
# ==============================================================================


@method_decorator(csrf_exempt, name="dispatch")
class OCRView(View):
    """OCR service overview and operations"""

    def get(self, request):
        """Get OCR service information"""
        return JsonResponse(
            {
                "service": "OCR Service",
                "version": "1.0.0",
                "endpoints": {
                    "extract_text": "/api/ocr/extract_text/",
                    "extract_text_multi": "/api/ocr/extract_text_multi/",
                    "extract_information": "/api/ocr/extract_information/",
                },
                "description": "Text extraction from images using computer vision",
            }
        )


@csrf_exempt
@require_http_methods(["POST"])
def extract_text_single(request):
    """Extract text from a single image"""
    try:
        if not request.FILES.get("file"):
            return JsonResponse({"error": "No file provided"}, status=400)

        uploaded_file = request.FILES["file"]

        # Prepare file data
        file_data = uploaded_file.read()
        filename = uploaded_file.name
        content_type = uploaded_file.content_type

        # Call OCR service
        result = ocr_service.extract_text_single(file_data, filename, content_type)

        return JsonResponse(result)

    except Exception as e:
        logger.error(f"OCR single extraction failed: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def extract_text_multi(request):
    """Extract text from multiple images"""
    try:
        files = request.FILES.getlist("files")
        if not files:
            return JsonResponse({"error": "No files provided"}, status=400)

        # Prepare files data
        files_data = []
        for uploaded_file in files:
            files_data.append(
                {
                    "filename": uploaded_file.name,
                    "data": uploaded_file.read(),
                    "content_type": uploaded_file.content_type,
                }
            )

        # Call OCR service
        result = ocr_service.extract_text_multi(files_data)

        return JsonResponse(result)

    except Exception as e:
        logger.error(f"OCR multi extraction failed: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def extract_information_legacy(request):
    """Legacy OCR endpoint for backward compatibility"""
    try:
        files = request.FILES.getlist("files")
        if not files:
            return JsonResponse({"error": "No files provided"}, status=400)

        # Prepare files data
        files_data = []
        for uploaded_file in files:
            files_data.append(
                {
                    "filename": uploaded_file.name,
                    "data": uploaded_file.read(),
                    "content_type": uploaded_file.content_type,
                }
            )

        # Call legacy OCR service
        result = ocr_service.extract_information_legacy(files_data)

        return JsonResponse(result)

    except Exception as e:
        logger.error(f"Legacy OCR extraction failed: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)


# ==============================================================================
# SUMMARY SERVICE VIEWS
# ==============================================================================


@method_decorator(csrf_exempt, name="dispatch")
class SummaryView(View):
    """Summary service overview and operations"""

    def get(self, request):
        """Get Summary service information"""
        return JsonResponse(
            {
                "service": "Summary Service",
                "version": "1.0.0",
                "endpoints": {
                    "summarize_text": "/api/summary/summarize_text/",
                    "ocr_and_summarize": "/api/summary/ocr_and_summarize/",
                    "recommend_study": "/api/summary/recommend_study/",
                    "image_ocr": "/api/summary/image_ocr/",
                },
                "description": "Document summarization and study recommendations",
            }
        )


@csrf_exempt
@require_http_methods(["POST"])
def summarize_text(request):
    """Summarize provided text"""
    try:
        data = json.loads(request.body)
        text = data.get("text")

        if not text:
            return JsonResponse({"error": "Text content is required"}, status=400)

        # Call Summary service
        result = summary_service.summarize_text(text)

        return JsonResponse(result)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)
    except Exception as e:
        logger.error(f"Text summarization failed: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def ocr_and_summarize(request):
    """Extract text from base64 image and create summary"""
    try:
        data = json.loads(request.body)
        image_base64 = data.get("image")
        summary_config = data.get("summary_config", {"style": "detailed"})

        if not image_base64:
            return JsonResponse({"error": "No image provided"}, status=400)

        # Convert base64 to file-like object
        import base64

        try:
            # Remove data URL prefix if present (e.g., "data:image/png;base64,")
            if "," in image_base64:
                image_base64 = image_base64.split(",", 1)[1]

            # Decode base64
            image_data = base64.b64decode(image_base64)

            # Prepare files data for service client
            files_data = [
                {
                    "filename": "image.png",
                    "data": image_data,
                    "content_type": "image/png",
                }
            ]

            # Call Summary service
            result = summary_service.ocr_and_summarize(files_data)

            # Wrap response to match frontend expectations
            return JsonResponse(
                {
                    "ocr": {
                        "extracted_text": result.get("extracted_text", ""),
                        "confidence_score": 0.85,
                    },
                    "summary": {
                        "summary": result.get("summary", ""),
                        "confidence_score": 0.85,
                    },
                }
            )

        except base64.binascii.Error as b64_err:
            logger.error(f"Base64 decode failed: {str(b64_err)}")
            return JsonResponse(
                {"error": f"Invalid base64 image data: {str(b64_err)}"}, status=400
            )
        except Exception as e:
            logger.error(f"Base64 image processing failed: {str(e)}", exc_info=True)
            return JsonResponse(
                {"error": f"Image processing failed: {str(e)}"}, status=400
            )

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)
    except Exception as e:
        logger.error(f"OCR and summarization failed: {str(e)}", exc_info=True)
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def recommend_study(request):
    """Generate study recommendations"""
    try:
        data = json.loads(request.body)
        content = data.get("content")
        difficulty_level = data.get("difficulty_level", "intermediate")
        study_time = data.get("study_time", 60)

        if not content:
            return JsonResponse({"error": "Content is required"}, status=400)

        # Call Summary service
        result = summary_service.recommend_study(content, difficulty_level, study_time)

        return JsonResponse(result)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)
    except Exception as e:
        logger.error(f"Study recommendation failed: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def image_ocr_legacy(request):
    """Legacy OCR endpoint for Summary service"""
    try:
        files = request.FILES.getlist("files")
        if not files:
            return JsonResponse({"error": "No files provided"}, status=400)

        # Prepare files data
        files_data = []
        for uploaded_file in files:
            files_data.append(
                {
                    "filename": uploaded_file.name,
                    "data": uploaded_file.read(),
                    "content_type": uploaded_file.content_type,
                }
            )

        # Call legacy Summary service
        result = summary_service.image_ocr_legacy(files_data)

        return JsonResponse(result)

    except Exception as e:
        logger.error(f"Legacy image OCR failed: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)


# ==============================================================================
# RAG CHATBOT SERVICE VIEWS
# ==============================================================================


@method_decorator(csrf_exempt, name="dispatch")
class ChatView(View):
    """RAG Chatbot service overview and operations"""

    def get(self, request):
        """Get RAG Chatbot service information"""
        return JsonResponse(
            {
                "service": "RAG Chatbot Service",
                "version": "1.0.0",
                "endpoints": {
                    "chat_message": "/api/chat/message/",
                    "start_conversation": "/api/chat/conversations/start/",
                    "list_conversations": "/api/chat/conversations/",
                    "conversation_history": "/api/chat/conversations/{id}/history/",
                },
                "description": "AI-powered chatbot with document retrieval and quiz context",
            }
        )


@csrf_exempt
@require_http_methods(["POST"])
def chat_message(request):
    """Send message to RAG chatbot"""
    try:
        data = json.loads(request.body)
        query = data.get("query")
        conversation_id = data.get("conversation_id")
        retrieval_config = data.get("retrieval_config", {})
        chat_config = data.get("chat_config", {})

        if not query:
            return JsonResponse(
                {
                    "success": False,
                    "data": None,
                    "error": "Query is required",
                    "status_code": 400,
                },
                status=400,
            )

        # Call RAG service
        result = rag_chatbot.chat(
            query=query,
            conversation_id=conversation_id,
            retrieval_config=retrieval_config,
            chat_config=chat_config,
        )

        return JsonResponse(
            {"success": True, "data": result, "error": None, "status_code": 200}
        )

    except json.JSONDecodeError:
        return JsonResponse(
            {
                "success": False,
                "data": None,
                "error": "Invalid JSON data",
                "status_code": 400,
            },
            status=400,
        )
    except Exception as e:
        logger.error(f"Chat message failed: {str(e)}")
        return JsonResponse(
            {"success": False, "data": None, "error": str(e), "status_code": 500},
            status=500,
        )


@csrf_exempt
@require_http_methods(["GET"])
def list_conversations(request):
    """List all conversations"""
    try:
        limit = int(request.GET.get("limit", 20))

        # Call RAG service
        result = rag_chatbot.list_conversations(limit=limit)

        return JsonResponse(result)

    except Exception as e:
        logger.error(f"List conversations failed: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_conversation_history(request, conversation_id):
    """Get conversation history"""
    try:
        limit = int(request.GET.get("limit", 10))

        # Call RAG service
        result = rag_chatbot.get_conversation_history(
            conversation_id=conversation_id, limit=limit
        )

        return JsonResponse(result)

    except Exception as e:
        logger.error(f"Get conversation history failed: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def save_document(request):
    """Save processed document to database with comprehensive validation"""
    try:
        data = json.loads(request.body)

        # Extract required fields
        file_name = data.get("fileName")
        file_size = data.get("fileSize")
        file_type = data.get("fileType")
        extracted_text = (data.get("extractedText") or "").strip()
        summary = (data.get("summary") or "").strip()
        document_id = data.get("documentId")

        logger.info(f"📥 Save document request:")
        logger.info(f"  Document ID: {document_id}")
        logger.info(f"  File name: {file_name}")
        logger.info(f"  Extracted text length: {len(extracted_text)}")
        logger.info(f"  Summary length: {len(summary)}")

        # ✅ VALIDATION 1: Required fields
        if not file_name:
            logger.error("❌ Validation failed: missing file_name")
            return JsonResponse(
                {"error": "Missing required field: fileName"},
                status=400,
            )

        if not document_id:
            logger.error("❌ Validation failed: missing document_id")
            return JsonResponse(
                {"error": "Missing required field: documentId"},
                status=400,
            )

        # ✅ VALIDATION 2: Content exists and is meaningful
        if not extracted_text and not summary:
            logger.error(
                "❌ Validation failed: both extracted_text and summary are empty"
            )
            return JsonResponse(
                {
                    "error": "Both extracted_text and summary are empty. Document has no meaningful content."
                },
                status=400,
            )

        # ✅ Stricter validation - minimum length check
        MIN_TEXT_LENGTH = 20
        extracted_text_valid = extracted_text and len(extracted_text) >= MIN_TEXT_LENGTH
        summary_valid = summary and len(summary) >= MIN_TEXT_LENGTH

        if not extracted_text_valid and not summary_valid:
            logger.error(f"❌ Validation failed: content too short")
            logger.error(
                f"   extracted_text: {len(extracted_text)} chars (min: {MIN_TEXT_LENGTH})"
            )
            logger.error(f"   summary: {len(summary)} chars (min: {MIN_TEXT_LENGTH})")
            return JsonResponse(
                {
                    "error": f"Content too short. Minimum {MIN_TEXT_LENGTH} characters required."
                },
                status=400,
            )

        # ✅ Use the one with more meaningful content
        if extracted_text_valid and not summary_valid:
            summary = extracted_text[:2000]
            logger.info("ℹ️ Using extracted_text as summary")
        elif summary_valid and not extracted_text_valid:
            extracted_text = summary[:5000]
            logger.info("ℹ️ Using summary as extracted_text")

        # Create document record
        document_data = {
            "document_id": document_id,
            "file_name": file_name,
            "file_size": file_size or 0,
            "file_type": file_type or "unknown",
            "extracted_text": extracted_text[:5000],
            "summary": summary[:2000],
            "created_at": timezone.now().isoformat(),
        }

        logger.info(f"💾 Inserting document to gateway DB: {document_id}")

        # ✅ Insert vào gateway DB
        try:
            insert_document(document_data)
            logger.info(f"✅ Document saved to gateway DB successfully: {document_id}")
        except Exception as insert_err:
            logger.error(
                f"❌ Failed to insert into gateway DB: {insert_err}", exc_info=True
            )
            return JsonResponse(
                {"error": f"Database insertion failed: {str(insert_err)}"},
                status=500,
            )

        # 🆕 GIẢI PHÁP 1: Insert trực tiếp vào rag_chatbot.db
        logger.info(f"� Syncing document to RAG service DB...")
        try:
            rag_sync_success = insert_document_to_rag_db(document_data)
            if rag_sync_success:
                logger.info(f"✅ Document synced to RAG service DB")
            else:
                logger.warning(
                    f"⚠️ Document sync to RAG service failed, will try rebuild-index"
                )
        except Exception as sync_err:
            logger.warning(f"⚠️ RAG sync failed: {sync_err}, will try rebuild-index")

        # 🆕 GIẢI PHÁP 2: Vẫn gọi rebuild-index để đảm bảo
        try:
            logger.info(f"🔄 Requesting RAG rebuild-index...")

            original_timeout = rag_chatbot.timeout
            rag_chatbot.timeout = 120

            try:
                response = rag_chatbot._make_request("POST", "/admin/rebuild-index")

                if response.success:
                    logger.info(f"✅ RAG rebuild-index successful")
                else:
                    logger.warning(
                        f"⚠️ RAG rebuild-index returned error: {response.error}"
                    )

            finally:
                rag_chatbot.timeout = original_timeout

        except Exception as rag_err:
            logger.warning(f"⚠️ Failed to trigger RAG rebuild: {rag_err}")

        return JsonResponse(
            {
                "success": True,
                "message": "Document saved successfully",
                "document_id": document_id,
                "saved_at": document_data["created_at"],
            }
        )

    except json.JSONDecodeError as e:
        logger.error(f"❌ Invalid JSON in request: {e}")
        return JsonResponse({"error": "Invalid JSON data"}, status=400)
    except Exception as e:
        logger.error(f"❌ Document save failed: {e}", exc_info=True)
        return JsonResponse({"error": str(e)}, status=500)


@api_view(["GET"])
@permission_classes([AllowAny])
def list_documents(request):
    """Return available documents from local documents.db."""

    try:
        ensure_document_table()
        docs = fetch_documents(limit=100)
        # Normalize field names for frontend
        documents = [
            {
                "document_id": d.get("id"),
                "file_name": d.get("file_name"),
                "file_size": d.get("file_size"),
                "file_type": d.get("file_type"),
                "extracted_text": d.get("extracted_text") or "",
                "summary": (d.get("summary") or d.get("extracted_text") or "")[:400],
                "created_at": d.get("created_at"),
            }
            for d in docs
        ]

        return JsonResponse({"success": True, "documents": documents})

    except Exception as e:
        logger.error(f"Document list failed: {str(e)}")
        return JsonResponse({"success": False, "error": str(e)}, status=500)


# ============= Authentication Endpoints =============


@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    """Register a new student account."""
    try:
        data = request.data
        logger.info(f"Registration request for username: {data.get('username')}")

        # Validate required fields
        required_fields = ["username", "email", "password", "password_confirm"]
        for field in required_fields:
            if not data.get(field):
                return Response(
                    {"success": False, "error": f"Missing required field: {field}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Check password match
        if data["password"] != data["password_confirm"]:
            return Response(
                {"success": False, "error": "Passwords do not match"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Register via IAM service
        user_data = {
            "username": data["username"],
            "email": data["email"],
            "password": data["password"],
            "password_confirm": data["password_confirm"],
        }

        logger.info(f"Calling IAM service to register user: {user_data['username']}")
        result = iam_service.register_user(user_data)

        logger.info(f"User registered successfully: {data['username']}")
        return Response(
            {"success": True, "message": "Registration successful", "data": result},
            status=status.HTTP_201_CREATED,
        )

    except Exception as e:
        error_message = str(e)
        logger.error(f"Registration failed for {data.get('username')}: {error_message}")
        return Response(
            {"success": False, "error": error_message},
            status=status.HTTP_400_BAD_REQUEST,
        )


@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    """Login with username and password."""
    try:
        data = request.data
        username = data.get("username")
        password = data.get("password")

        logger.info(f"Login attempt for username: {username}")

        if not username or not password:
            return Response(
                {"success": False, "error": "Username and password are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Login via IAM service
        logger.info(f"Calling IAM service to login user: {username}")
        result = iam_service.login(username, password)

        logger.info(f"User logged in successfully: {username}")
        return Response(
            {"success": True, "message": "Login successful", "data": result},
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        error_message = str(e)
        logger.error(f"Login failed for {username}: {error_message}")
        return Response(
            {"success": False, "error": error_message},
            status=status.HTTP_401_UNAUTHORIZED,
        )


@api_view(["POST"])
def logout(request):
    """Logout and blacklist refresh token."""
    try:
        data = request.data
        refresh_token = data.get("refresh")

        if not refresh_token:
            return Response(
                {"success": False, "error": "Refresh token is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Logout via IAM service
        iam_service.logout(refresh_token)

        logger.info("User logged out")
        return Response(
            {"success": True, "message": "Logout successful"},
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        logger.error(f"Logout failed: {str(e)}")
        return Response(
            {"success": False, "error": str(e)},
            status=status.HTTP_400_BAD_REQUEST,
        )


@api_view(["POST"])
@permission_classes([AllowAny])
def refresh_token(request):
    """Refresh access token using refresh token."""
    try:
        data = request.data
        refresh = data.get("refresh")

        if not refresh:
            return Response(
                {"success": False, "error": "Refresh token is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Refresh via IAM service
        result = iam_service.refresh_token(refresh)

        return Response(
            {"success": True, "data": result},
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        logger.error(f"Token refresh failed: {str(e)}")
        return Response(
            {"success": False, "error": str(e)},
            status=status.HTTP_401_UNAUTHORIZED,
        )


@api_view(["GET"])
def get_current_user(request):
    """Get current user information."""
    try:
        # Get token from Authorization header
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return Response(
                {"success": False, "error": "Authorization header missing or invalid"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        access_token = auth_header.replace("Bearer ", "").strip()

        # Get user info from IAM service
        user_info = iam_service.get_current_user(access_token)

        return Response(
            {"success": True, "user": user_info},
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        logger.error(f"Get current user failed: {str(e)}")
        return Response(
            {"success": False, "error": str(e)},
            status=status.HTTP_401_UNAUTHORIZED,
        )
