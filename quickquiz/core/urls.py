from django.urls import path
from . import views

urlpatterns = [
    path('', views.upload_document_view, name='upload_document'),
    path('document/<int:doc_id>/', views.document_detail_view, name='document_detail'),
]
