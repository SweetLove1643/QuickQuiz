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
import json
from typing import List, Dict, Any, Optional
import logging
import time
import re

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
    
    def rebuild_index(self) -> None:
        """
        Rebuild document index from all sources with batch processing.
        Includes timeout protection and batch commits.
        """
        import time
        start_time = time.time()
        max_duration = 40  # 40s max (gateway timeout 45s)
        batch_size = 50  # Commit every 50 chunks
        
        try:
            logger.info("🔄 Starting rebuild index...")
            db = SessionLocal()
            
            chunk_count_before = db.query(DocumentChunkModel).count()
            logger.info(f"Existing chunks: {chunk_count_before}")
            
            # 1. Ingest gateway documents
            gateway_docs = self.quiz_data.get_gateway_documents(limit=50)
            logger.info(f"Found {len(gateway_docs)} gateway documents to ingest")
            
            if not gateway_docs:
                logger.info("No gateway documents to ingest")
                db.close()
                return
            
            chunks_created = 0
            batch_buffer = []  # Buffer for batch inserts
            
            for doc_idx, doc in enumerate(gateway_docs):
                # Check timeout
                elapsed = time.time() - start_time
                if elapsed > max_duration:
                    logger.warning(f"⏱️ Rebuild timeout approaching ({elapsed:.1f}s), stopping")
                    break
                
                try:
                    doc_id = doc.get("document_id", f"doc_{doc_idx}")
                    text = (doc.get("extracted_text") or doc.get("summary") or "").strip()
                    
                    if not text or len(text) < 10:
                        logger.debug(f"Skipping document {doc_id}: text too short")
                        continue
                    
                    logger.info(f"Ingesting document {doc_idx+1}/{len(gateway_docs)}: {doc_id}")
                    
                    # Split text into chunks with size limit
                    text_chunks = self._split_text_into_chunks(text, chunk_size=500, overlap=50)
                    logger.debug(f"  Created {len(text_chunks)} chunks from document")
                    
                    for chunk_idx, chunk_text in enumerate(text_chunks):
                        chunk_id = f"doc_{doc_id}_{chunk_idx}"
                        
                        # Avoid duplicate chunks
                        existing = db.query(DocumentChunkModel).filter(
                            DocumentChunkModel.chunk_id == chunk_id
                        ).first()
                        
                        if existing:
                            continue
                        
                        # Create chunk object (don't add yet - buffer it)
                        chunk = DocumentChunkModel(
                            chunk_id=chunk_id,
                            document_id=doc_id,
                            content=chunk_text[:5000],  # Limit chunk size
                            chunk_index=chunk_idx,
                            topic=doc.get("file_name", "Document"),
                            category="document",
                            tags=["gateway", "uploaded"],
                        )
                        batch_buffer.append(chunk)
                        
                        # Batch commit every N chunks
                        if len(batch_buffer) >= batch_size:
                            db.add_all(batch_buffer)
                            db.commit()
                            chunks_created += len(batch_buffer)
                            logger.debug(f"  Batch commit: {chunks_created} chunks total")
                            batch_buffer = []
                            
                except Exception as e:
                    logger.error(f"❌ Error processing document {doc_id}: {e}")
                    # Continue with next document
                    continue
            
            # Final commit for remaining chunks
            if batch_buffer:
                db.add_all(batch_buffer)
                db.commit()
                chunks_created += len(batch_buffer)
                logger.info(f"Final batch commit: {chunks_created} chunks total")
            
            db.close()
            elapsed = time.time() - start_time
            logger.info(f"✅ Index rebuild complete in {elapsed:.1f}s. Created {chunks_created} chunks")
            
        except Exception as e:
            logger.error(f"❌ Rebuild index failed: {e}", exc_info=True)
            try:
                db.close()
            except:
                pass
            raise


    def _split_text_into_chunks(
        self, text: str, chunk_size: int = 500, overlap: int = 50
    ) -> List[str]:
        """
        Split text into overlapping chunks safely.
        Prevents infinite loops and excessive memory use.
        """
        import re
        
        if not text or len(text) < 10:
            return []
        
        # Limit total chunks to prevent memory explosion
        max_chunks = 200
        chunks = []
        
        # Split by sentences first for better semantic chunks
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        current_chunk = ""
        for sentence in sentences:
            if len(chunks) >= max_chunks:
                logger.warning(f"Reached max chunks limit ({max_chunks})")
                break
            
            # If adding sentence exceeds chunk_size, save current chunk
            if current_chunk and len(current_chunk) + len(sentence) > chunk_size:
                chunks.append(current_chunk.strip())
                # Start new chunk with overlap (last part of previous chunk)
                current_chunk = current_chunk[-overlap:] if overlap > 0 else ""
            
            current_chunk += " " + sentence if current_chunk else sentence
        
        # Add final chunk
        if current_chunk.strip() and len(chunks) < max_chunks:
            chunks.append(current_chunk.strip())
        
        return chunks
