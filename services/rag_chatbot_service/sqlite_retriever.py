"""
SQLite-based document retriever for RAG chatbot service.
Replaces MongoDB retriever with SQLite integration.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy import or_
from database import quiz_data_access, DocumentChunkModel, SessionLocal
from schemas import RetrievedDocument, RetrievalConfig
import sqlite3
import json

logger = logging.getLogger(__name__)


class SQLiteDocumentRetriever:
    """
    Simple SQLite-based document retriever.
    Uses quiz data from cross-service access and stored document chunks.
    """

    def __init__(self):
        """Initialize SQLite document retriever."""
        self.quiz_data = quiz_data_access

    def initialize(self, force_rebuild: bool = False) -> None:
        """Initialize the retriever."""
        logger.info("Initializing SQLite document retriever...")
        # Check if we have quiz data
        templates = self.quiz_data.get_quiz_templates(5)
        generated = self.quiz_data.get_generated_quizzes(5)
        logger.info(
            f"Found {len(templates)} quiz templates, {len(generated)} generated quizzes"
        )
        logger.info("SQLite document retriever initialized")

    def search_documents(
        self, query: str, config: Optional[RetrievalConfig] = None
    ) -> List[RetrievedDocument]:
        """
        Search documents based on query.
        Returns a mix of stored document chunks and quiz data.
        """
        if not config:
            config = RetrievalConfig()

        results = []

        # 1. Search stored document chunks
        stored_docs = self._search_stored_chunks(query, config.top_k // 2)
        results.extend(stored_docs)

        # 2. Search quiz content for additional context
        quiz_docs = self._search_quiz_content(query, config.top_k // 2)
        results.extend(quiz_docs)

        # Sort by relevance (simple keyword matching for now)
        results = self._rank_documents(results, query)

        return results[: config.top_k]

    def retrieve_documents(
        self, query: str, config: Optional[RetrievalConfig] = None
    ) -> List[RetrievedDocument]:
        """
        Alias for search_documents to maintain compatibility.
        """
        return self.search_documents(query, config)

    def _search_stored_chunks(self, query: str, limit: int) -> List[RetrievedDocument]:
        """Search stored document chunks in database."""
        try:
            db = SessionLocal()

            # Split query into words for better matching
            query_words = query.lower().split()

            if len(query_words) == 1:
                # Single word search
                query_pattern = f"%{query_words[0]}%"
                chunks = (
                    db.query(DocumentChunkModel)
                    .filter(DocumentChunkModel.content.ilike(query_pattern))
                    .limit(limit)
                    .all()
                )
            else:
                # Multi-word search - find documents containing any of the words
                filters = []
                for word in query_words:
                    filters.append(DocumentChunkModel.content.ilike(f"%{word}%"))

                chunks = (
                    db.query(DocumentChunkModel)
                    .filter(or_(*filters))
                    .limit(limit)
                    .all()
                )

            results = []
            for chunk in chunks:
                results.append(
                    RetrievedDocument(
                        document_id=chunk.document_id,
                        chunk_id=chunk.chunk_id,
                        content=chunk.content,
                        topic=chunk.topic,
                        category=chunk.category,
                        similarity_score=0.5,  # Simple fixed score for now
                        tags=chunk.tags or [],
                    )
                )

            return results

        except Exception as e:
            logger.error(f"Error searching stored chunks: {e}")
            return []
        finally:
            db.close()

    def _search_quiz_content(self, query: str, limit: int) -> List[RetrievedDocument]:
        """Search quiz content for relevant context."""
        results = []

        try:
            # Search quiz templates
            quiz_content = self.quiz_data.search_quiz_content(query, limit)

            for item in quiz_content:
                results.append(
                    RetrievedDocument(
                        document_id=f"quiz_{item.get('type', 'unknown')}",
                        chunk_id=f"quiz_{len(results)}",
                        content=item.get("content", ""),
                        topic=item.get("subject", "Quiz Content"),
                        category=item.get("type", "quiz"),
                        similarity_score=0.4,  # Lower score for quiz content
                        tags=[],
                    )
                )

            return results[:limit]

        except Exception as e:
            logger.error(f"Error searching quiz content: {e}")
            return []

    def _rank_documents(
        self, documents: List[RetrievedDocument], query: str
    ) -> List[RetrievedDocument]:
        """Simple ranking based on keyword matching."""
        query_words = query.lower().split()

        for doc in documents:
            content_words = doc.content.lower().split()
            matches = sum(1 for word in query_words if word in content_words)
            # Update similarity score based on keyword matches
            doc.similarity_score = min(0.9, doc.similarity_score + (matches * 0.1))

        # Sort by similarity score descending
        return sorted(documents, key=lambda x: x.similarity_score, reverse=True)

    def get_document_count(self) -> int:
        """Get total number of documents available."""
        try:
            db = SessionLocal()
            chunk_count = db.query(DocumentChunkModel).count()

            # Add quiz data count
            templates = self.quiz_data.get_quiz_templates(100)
            generated = self.quiz_data.get_generated_quizzes(100)

            return chunk_count + len(templates) + len(generated)

        except Exception as e:
            logger.error(f"Error getting document count: {e}")
            return 0
        finally:
            db.close()

    def get_stats(self) -> Dict[str, Any]:
        """Get retriever statistics."""
        try:
            db = SessionLocal()
            chunk_count = db.query(DocumentChunkModel).count()

            # Get quiz data stats
            templates = self.quiz_data.get_quiz_templates(100)
            generated = self.quiz_data.get_generated_quizzes(100)

            return {
                "document_chunks": chunk_count,
                "quiz_templates": len(templates),
                "generated_quizzes": len(generated),
                "total_documents": chunk_count + len(templates) + len(generated),
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {"error": str(e)}
        finally:
            db.close()
