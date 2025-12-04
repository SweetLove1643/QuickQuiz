from django.urls import path
from . import views

urlpatterns = [
    path('<int:doc_id>/take/', views.take_quiz_view, name='take_quiz'),
    path('<int:doc_id>/submit/', views.submit_quiz_view, name='submit_quiz'),
    path('<int:doc_id>/result/', views.result_view, name='quiz_result'),
]
