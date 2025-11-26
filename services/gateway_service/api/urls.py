from django.urls import path, include
from . import views

app_name = "api"

urlpatterns = [
    # Health check endpoint
    path("health/", views.health_check, name="health_check"),
    # API root
    path("", views.api_root, name="api_root"),
    # Quiz endpoints
    path("quiz/", views.QuizView.as_view(), name="quiz"),
    path("quiz/generate/", views.generate_quiz, name="generate_quiz"),
    path("quiz/evaluate/", views.evaluate_quiz, name="evaluate_quiz"),
]
