import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .service_clients import QuizGeneratorClient, QuizEvaluatorClient
import json

logger = logging.getLogger(__name__)

# Initialize service clients
quiz_generator = QuizGeneratorClient()
quiz_evaluator = QuizEvaluatorClient()


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
        logger.info(f"Generating quiz with data: {data}")

        # Call quiz generator service
        result = quiz_generator.generate_quiz(data)

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
def evaluate_quiz(request):
    """
    Evaluate quiz endpoint - proxies to quiz evaluator service
    """
    try:
        # Extract and validate request data
        data = request.data
        logger.info(f"Evaluating quiz with data: {data}")

        # Call quiz evaluator service
        result = quiz_evaluator.evaluate_quiz(data)

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
