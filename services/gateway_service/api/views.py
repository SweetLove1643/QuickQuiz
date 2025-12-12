import logging
from django.http import JsonResponse, FileResponse
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


def fetch_single_document(document_id: str):
    """Fetch a single document by ID."""
    if not os.path.exists(DOCUMENT_DB_PATH):
        return None
    with closing(sqlite3.connect(DOCUMENT_DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, file_name, file_size, file_type, extracted_text, summary, created_at
            FROM documents
            WHERE id = ?
            """,
            (document_id,),
        )
        row = cur.fetchone()
        return dict(row) if row else None


def delete_document(document_id: str):
    """Delete a document by ID."""
    ensure_document_table()
    with closing(sqlite3.connect(DOCUMENT_DB_PATH)) as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM documents WHERE id = ?", (document_id,))
        conn.commit()
        return cur.rowcount > 0


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
def download_quiz_pdf(request, quiz_id):
    """Download quiz as PDF with full Unicode support."""
    try:
        import requests
        from django.http import FileResponse

        # Call quiz generator PDF endpoint
        response = requests.get(
            f"http://127.0.0.1:8002/quiz/{quiz_id}/pdf", stream=True
        )

        if response.status_code == 200:
            # Get filename from content-disposition header
            filename = f"quiz-{quiz_id}.pdf"
            if "content-disposition" in response.headers:
                import re

                match = re.search(
                    r'filename="?([^"]+)"?', response.headers["content-disposition"]
                )
                if match:
                    filename = match.group(1)

            # Return file response
            return FileResponse(
                response.raw,
                content_type="application/pdf",
                as_attachment=True,
                filename=filename,
            )
        else:
            return Response(
                {"error": "Failed to generate PDF"}, status=response.status_code
            )
    except Exception as e:
        logger.error(f"Failed to download quiz PDF: {str(e)}")
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
    """Extract text from files and create summary"""
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

        # Call Summary service
        result = summary_service.ocr_and_summarize(files_data)

        return JsonResponse(result)

    except Exception as e:
        logger.error(f"OCR and summarization failed: {str(e)}")
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
            return JsonResponse({"error": "Query is required"}, status=400)

        # Call RAG service
        result = rag_chatbot.chat(
            query=query,
            conversation_id=conversation_id,
            retrieval_config=retrieval_config,
            chat_config=chat_config,
        )

        return JsonResponse(result)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)
    except Exception as e:
        logger.error(f"Chat message failed: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)


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
@require_http_methods(["PUT", "PATCH"])
def update_document(request, document_id):
    """Update existing document in database"""
    try:
        data = json.loads(request.body)

        # Check if document exists
        existing_doc = fetch_single_document(document_id)
        if not existing_doc:
            return JsonResponse(
                {"error": f"Document with ID {document_id} not found"},
                status=404,
            )

        # Extract fields to update (allow partial updates)
        file_name = (
            data.get("title") or data.get("fileName") or existing_doc.get("file_name")
        )
        extracted_text = (
            data.get("content")
            or data.get("extractedText")
            or existing_doc.get("extracted_text")
        )
        summary = data.get("summary") or existing_doc.get("summary")
        file_size = data.get("fileSize") or existing_doc.get("file_size")
        file_type = data.get("fileType") or existing_doc.get("file_type")

        # Update document record
        document_data = {
            "document_id": document_id,
            "file_name": file_name,
            "file_size": file_size or 0,
            "file_type": file_type or "unknown",
            "extracted_text": extracted_text[:5000] if extracted_text else "",
            "summary": summary or "",
            "created_at": existing_doc.get("created_at"),  # Keep original creation time
        }

        logger.info(f"Updating document: {file_name} (ID: {document_id})")

        insert_document(document_data)  # INSERT OR REPLACE will update

        return JsonResponse(
            {
                "success": True,
                "message": "Document updated successfully",
                "document_id": document_id,
                "updated_at": timezone.now().isoformat(),
            }
        )

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)
    except Exception as e:
        logger.error(f"Document update failed: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def save_document(request):
    """Save processed document to database"""
    try:
        data = json.loads(request.body)

        # Extract required fields
        file_name = data.get("fileName")
        file_size = data.get("fileSize")
        file_type = data.get("fileType")
        extracted_text = data.get("extractedText")
        summary = data.get("summary")
        document_id = data.get("documentId")

        if not all([file_name, extracted_text, summary, document_id]):
            return JsonResponse(
                {
                    "error": "Missing required fields: fileName, extractedText, summary, documentId"
                },
                status=400,
            )

        # Create document record
        document_data = {
            "document_id": document_id,
            "file_name": file_name,
            "file_size": file_size or 0,
            "file_type": file_type or "unknown",
            "extracted_text": extracted_text[:5000],  # Limit text length
            "summary": summary,
            "created_at": timezone.now().isoformat(),
            "processing_time": data.get("processingTime", 0),
            "ocr_confidence": data.get("ocrConfidence"),
            "summary_confidence": data.get("summaryConfidence"),
        }

        logger.info(f"Saving document: {file_name} (ID: {document_id})")

        insert_document(document_data)

        return JsonResponse(
            {
                "success": True,
                "message": "Document saved successfully",
                "document_id": document_id,
                "saved_at": document_data["created_at"],
            }
        )

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)
    except Exception as e:
        logger.error(f"Document save failed: {str(e)}")
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


@api_view(["DELETE"])
@permission_classes([AllowAny])
def delete_document_view(request, document_id):
    """Delete a document from the database."""
    try:
        success = delete_document(document_id)
        if success:
            return JsonResponse(
                {"success": True, "message": "Document deleted successfully"}
            )
        else:
            return JsonResponse(
                {"success": False, "error": "Document not found"}, status=404
            )
    except Exception as e:
        logger.error(f"Document delete failed: {str(e)}")
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@api_view(["GET"])
@permission_classes([AllowAny])
def download_document_pdf(request, document_id):
    """Generate and download PDF for a document."""
    try:
        # Fetch document from database
        doc = fetch_single_document(document_id)
        if not doc:
            return JsonResponse({"error": "Document not found"}, status=404)

        # Import PDF generation libraries
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.platypus import (
            SimpleDocTemplate,
            Paragraph,
            Spacer,
            Table,
            TableStyle,
        )
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        import tempfile
        import os

        # Register Unicode font
        try:
            arial_unicode_path = "C:/Windows/Fonts/ARIALUNI.TTF"
            if os.path.exists(arial_unicode_path):
                pdfmetrics.registerFont(TTFont("ArialUnicode", arial_unicode_path))
                unicode_font = "ArialUnicode"
            else:
                arial_path = "C:/Windows/Fonts/arial.ttf"
                if os.path.exists(arial_path):
                    pdfmetrics.registerFont(TTFont("Arial", arial_path))
                    unicode_font = "Arial"
                else:
                    unicode_font = "Helvetica"
        except:
            unicode_font = "Helvetica"

        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        temp_file.close()

        # Create PDF
        pdf = SimpleDocTemplate(
            temp_file.name,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18,
        )

        # Container for PDF elements
        elements = []
        styles = getSampleStyleSheet()

        # Create custom styles with Unicode font
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontName=unicode_font,
            fontSize=24,
            textColor=colors.HexColor("#1e293b"),
            spaceAfter=30,
            alignment=1,  # Center
        )

        heading_style = ParagraphStyle(
            "CustomHeading",
            parent=styles["Heading2"],
            fontName=unicode_font,
            fontSize=14,
            textColor=colors.HexColor("#475569"),
            spaceAfter=12,
        )

        body_style = ParagraphStyle(
            "CustomBody",
            parent=styles["BodyText"],
            fontName=unicode_font,
            fontSize=11,
            textColor=colors.HexColor("#334155"),
            spaceAfter=12,
            leading=16,
        )

        # Add title
        file_name = doc.get("file_name", "Document")
        title = Paragraph(file_name, title_style)
        elements.append(title)
        elements.append(Spacer(1, 0.3 * inch))

        # Add metadata table
        metadata = [
            ["Loại file:", doc.get("file_type", "N/A")],
            [
                "Ngày tạo:",
                (
                    doc.get("created_at", "N/A").split("T")[0]
                    if doc.get("created_at")
                    else "N/A"
                ),
            ],
            [
                "Kích thước:",
                (
                    f"{doc.get('file_size', 0) / 1024:.2f} KB"
                    if doc.get("file_size")
                    else "N/A"
                ),
            ],
        ]

        meta_table = Table(metadata, colWidths=[2 * inch, 4 * inch])
        meta_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, -1), unicode_font),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#64748b")),
                    ("TEXTCOLOR", (1, 0), (1, -1), colors.HexColor("#1e293b")),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        elements.append(meta_table)
        elements.append(Spacer(1, 0.4 * inch))

        # Add summary if available
        if doc.get("summary"):
            summary_heading = Paragraph("Tóm tắt", heading_style)
            elements.append(summary_heading)
            summary_text = Paragraph(doc.get("summary"), body_style)
            elements.append(summary_text)
            elements.append(Spacer(1, 0.3 * inch))

        # Add extracted text
        if doc.get("extracted_text"):
            content_heading = Paragraph("Nội dung", heading_style)
            elements.append(content_heading)

            # Split long text into paragraphs
            text_content = doc.get("extracted_text", "")
            paragraphs = text_content.split("\n\n")
            for para in paragraphs:
                if para.strip():
                    p = Paragraph(para.strip().replace("\n", "<br/>"), body_style)
                    elements.append(p)
                    elements.append(Spacer(1, 0.1 * inch))

        # Build PDF
        pdf.build(elements)

        # Return file
        filename = f"{file_name.replace(' ', '_')}.pdf"
        return FileResponse(
            open(temp_file.name, "rb"),
            content_type="application/pdf",
            as_attachment=True,
            filename=filename,
        )

    except Exception as e:
        logger.error(f"Document PDF generation failed: {str(e)}")
        import traceback

        logger.error(traceback.format_exc())
        return JsonResponse({"error": str(e)}, status=500)


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
