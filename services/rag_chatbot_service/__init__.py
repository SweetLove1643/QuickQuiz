"""
RAG Chatbot Package
==================

Hệ thống chatbot RAG (Retrieval-Augmented Generation) cho hỏi đáp nội dung
từ các summaries sử dụng vector database và Gemini AI.

Features:
- Text embedding với sentence-transformers (local)
- FAISS vector store cho similarity search
- Document chunking và retrieval
- RAG-based Q&A với Gemini API
- REST API với FastAPI
- Mock data cho testing không cần database
"""

from .chat_engine import ask_question
from .schemas import ChatRequest, ChatResponse, SummaryDocument, RetrievalConfig

__version__ = "1.0.0"
__author__ = "RAG Chatbot Team"

__all__ = [
    "ask_question",
    "ChatRequest",
    "ChatResponse",
    "SummaryDocument",
    "RetrievalConfig",
]
