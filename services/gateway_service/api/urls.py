from django.urls import path, include
from . import views

app_name = "api"

urlpatterns = [
    path("health/", views.health_check, name="health_check"),
    path("", views.api_root, name="api_root"),
    path("auth/register/", views.register, name="register"),
    path("auth/login/", views.login, name="login"),
    path("auth/logout/", views.logout, name="logout"),
    path("auth/refresh/", views.refresh_token, name="refresh_token"),
    path("auth/me/", views.get_current_user, name="get_current_user"),
    path("quiz/", views.QuizView.as_view(), name="quiz"),
    path("quiz/generate/", views.generate_quiz, name="generate_quiz"),
    path("quiz/evaluate/", views.evaluate_quiz, name="evaluate_quiz"),
    path("quiz/save/", views.save_quiz, name="save_quiz"),
    path("quiz/<str:quiz_id>/", views.get_quiz_details, name="get_quiz_details"),
    path("quiz/<str:quiz_id>/delete/", views.delete_quiz, name="delete_quiz"),
    path("quiz/user/<str:user_id>/", views.get_user_quizzes, name="get_user_quizzes"),
    path(
        "quiz/user/<str:user_id>/recent/",
        views.get_user_recent_quizzes,
        name="get_user_recent_quizzes",
    ),
    path(
        "results/user/<str:user_id>/", views.get_user_results, name="get_user_results"
    ),
    path(
        "results/user/<str:user_id>/recent/",
        views.get_user_recent_results,
        name="get_user_recent_results",
    ),
    path("ocr/", views.OCRView.as_view(), name="ocr"),
    path("ocr/extract_text/", views.extract_text_single, name="extract_text_single"),
    path(
        "ocr/extract_text_multi/", views.extract_text_multi, name="extract_text_multi"
    ),
    path(
        "ocr/extract_information/",
        views.extract_information_legacy,
        name="extract_information_legacy",
    ),
    path("summary/", views.SummaryView.as_view(), name="summary"),
    path("summary/summarize_text/", views.summarize_text, name="summarize_text"),
    path(
        "summary/ocr_and_summarize/", views.ocr_and_summarize, name="ocr_and_summarize"
    ),
    path("documents/process/", views.process_document, name="process_document"),
    path("summary/recommend_study/", views.recommend_study, name="recommend_study"),
    path("summary/image_ocr/", views.image_ocr_legacy, name="image_ocr_legacy"),
    path("documents/save/", views.save_document, name="save_document"),
    path("documents/list/", views.list_documents, name="list_documents"),
    path(
        "documents/<str:doc_id>/update/", views.update_document, name="update_document"
    ),
    path("rag/", views.ChatView.as_view(), name="rag_chat"),
    path("rag/chat/", views.chat_message, name="rag_chat_message"),
    path("rag/conversations/", views.list_conversations, name="rag_list_conversations"),
    path(
        "rag/conversations/<str:conversation_id>/",
        views.get_conversation_history,
        name="rag_conversation_history",
    ),
]
