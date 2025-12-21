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

    def __init__(self):
        self.quiz_data = quiz_data_access

    def initialize(self, force_rebuild: bool = False) -> None:
        logger.info("Initializing SQLite document retriever...")
        templates = self.quiz_data.get_quiz_templates(5)
        generated = self.quiz_data.get_generated_quizzes(5)
        logger.info(
            f"Found {len(templates)} quiz templates, {len(generated)} generated quizzes"
        )
        logger.info("SQLite document retriever initialized")

    def search_documents(
        self, query: str, config: Optional[RetrievalConfig] = None
    ) -> List[RetrievedDocument]:
        if not config:
            config = RetrievalConfig()

        results = []
        stored_docs = self._search_stored_chunks(query, config.top_k // 2)
        results.extend(stored_docs)

        quiz_docs = self._search_quiz_content(query, config.top_k // 2)
        results.extend(quiz_docs)

        results = self._rank_documents(results, query)

        return results[: config.top_k]

    def retrieve_documents(
        self, query: str, config: Optional[RetrievalConfig] = None
    ) -> List[RetrievedDocument]:

        logger.info(f"retrieve_documents called with query: '{query}'")
        return self.search_documents(query, config)

    def _search_stored_chunks(self, query: str, top_k: int = 5) -> List[RetrievedDocument]:
        results = []
        
        try:
            db = SessionLocal()
            
            query_words = query.lower().split()
            
            logger.info(f"Search chunks - Total in DB: {db.query(DocumentChunkModel).count()}")
            logger.info(f"Query words: {query_words}")
            
            logger.info(f"Executing search query...")
            matching_chunks = []
            
            for word in query_words:
                chunks = db.query(DocumentChunkModel).filter(
                    or_(
                        DocumentChunkModel.content.ilike(f"%{word}%"),
                        DocumentChunkModel.topic.ilike(f"%{word}%"),
                    )
                ).all()
                matching_chunks.extend(chunks)
            
            seen = set()
            unique_chunks = []
            for chunk in matching_chunks:
                if chunk.chunk_id not in seen:
                    seen.add(chunk.chunk_id)
                    unique_chunks.append(chunk)
            
            logger.info(f"Found {len(unique_chunks)} matching chunks")
            
            valid_count = 0
            for chunk in unique_chunks[:top_k]:
                content = (chunk.content or "").strip()
                if content:
                    valid_count += 1
                    try:
                        results.append(RetrievedDocument(
                            document_id=chunk.document_id or f"doc_{chunk.id}",
                            chunk_id=chunk.chunk_id,
                            content=content,
                            topic=chunk.topic or "Unknown",  
                            category=chunk.category or "document", 
                            similarity_score=0.8,  #
                            tags=chunk.tags or []
                        ))
                        logger.debug(f"Added chunk: {chunk.chunk_id}")
                    except Exception as chunk_err:
                        logger.error(f"Error adding chunk {chunk.chunk_id}: {chunk_err}")
                        continue
            
            logger.info(f"Valid chunks (non-empty): {valid_count}/{len(unique_chunks)}")
            for i, doc in enumerate(results[:3]):
                logger.info(f"  Chunk {i+1}: doc={doc.document_id}, topic={doc.topic}, content_len={len(doc.content)}")
            
            db.close()
            
            logger.info(f"Returning {len(results)} retrieved documents")
            return results
            
        except Exception as e:
            logger.error(f"Error searching chunks: {e}", exc_info=True)
            return []

    def _search_quiz_content(self, query: str, limit: int) -> List[RetrievedDocument]:
        results = []
    
        try:
            quiz_content = self.quiz_data.search_quiz_content(query, limit)
    
            for idx, item in enumerate(quiz_content):
                try:
                    results.append(RetrievedDocument(
                        document_id=f"quiz_{item.get('type', 'template')}_{idx}",
                        chunk_id=f"quiz_chunk_{len(results)}",
                        content=(item.get("content") or "")[:500],
                        topic=item.get("subject", "Quiz Content"),  
                        category=item.get("type", "quiz"),  
                        similarity_score=0.4, 
                        tags=["quiz", "template"]
                    ))
                except Exception as item_err:
                    logger.warning(f"Error adding quiz item: {item_err}")
                    continue
    
            logger.info(f"Found {len(results)} quiz content items")
            return results[:limit]
    
        except Exception as e:
            logger.error(f"Error searching quiz content: {e}", exc_info=True)
            return []

    def _rank_documents(
        self, documents: List[RetrievedDocument], query: str
    ) -> List[RetrievedDocument]:
        query_words = query.lower().split()

        for doc in documents:
            content_words = doc.content.lower().split()
            matches = sum(1 for word in query_words if word in content_words)
            doc.similarity_score = min(0.9, doc.similarity_score + (matches * 0.1))

        return sorted(documents, key=lambda x: x.similarity_score, reverse=True)

    def get_document_count(self) -> int:
        try:
            db = SessionLocal()
            chunk_count = db.query(DocumentChunkModel).count()


            templates = self.quiz_data.get_quiz_templates(100)
            generated = self.quiz_data.get_generated_quizzes(100)

            return chunk_count + len(templates) + len(generated)

        except Exception as e:
            logger.error(f"Error getting document count: {e}")
            return 0
        finally:
            db.close()

    def get_stats(self) -> Dict[str, Any]:
        try:
            db = SessionLocal()
            chunk_count = db.query(DocumentChunkModel).count()

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
        import time
        start_time = time.time()
        max_duration = 60  
        batch_size = 50
        
        db = None
        try:
            logger.info("Starting rebuild index...")
            db = SessionLocal()
            
            chunk_count_before = db.query(DocumentChunkModel).count()
            logger.info(f"Existing chunks in rag_chatbot.db: {chunk_count_before}")
            
            logger.info("Attempting to retrieve gateway documents...")
            gateway_docs = self.quiz_data.get_gateway_documents(limit=100)
            logger.info(f"Retrieved {len(gateway_docs)} gateway documents")
            
            if not gateway_docs:
                logger.warning("No gateway documents to ingest - this might be normal if no files uploaded yet")
                logger.info("Rebuild complete (no documents to process)")
                return
            
            logger.info(f"Processing {len(gateway_docs)} documents...")
            chunks_created = 0
            chunks_skipped = 0
            batch_buffer = []
            
            for doc_idx, doc in enumerate(gateway_docs):
                elapsed = time.time() - start_time
                if elapsed > max_duration:
                    logger.warning(f"Rebuild timeout ({elapsed:.1f}s), stopping at document {doc_idx+1}/{len(gateway_docs)}")
                    break
                
                try:
                    doc_id = doc.get("document_id", f"doc_{doc_idx}")
                    extracted_text = (doc.get("extracted_text") or "").strip()
                    summary_text = (doc.get("summary") or "").strip()
                    file_name = doc.get("file_name", "Document")
                    
                    logger.info(f"[{doc_idx+1}/{len(gateway_docs)}] {doc_id}")
                    logger.info(f"    File: {file_name}")
                    logger.info(f"    extracted_text: {len(extracted_text)} chars, summary: {len(summary_text)} chars")
                    
                    text = extracted_text if len(extracted_text) >= len(summary_text) else summary_text
                    text_source = "extracted_text" if len(extracted_text) >= len(summary_text) else "summary"
                    
                    MIN_CONTENT_LENGTH = 20
                    if not text or len(text) < MIN_CONTENT_LENGTH:
                        logger.warning(f"Skip: Content too short ({len(text)} < {MIN_CONTENT_LENGTH})")
                        chunks_skipped += 1
                        continue
                    
                    logger.info(f"Using {text_source} as content")
                    
                    text_chunks = self._split_text_into_chunks(text, chunk_size=500, overlap=50)
                    logger.info(f"Split into {len(text_chunks)} chunks")
                    
                    doc_chunks_created = 0
                    for chunk_idx, chunk_text in enumerate(text_chunks):
                        chunk_id = f"chunk_{doc_id}_{chunk_idx}"
                        
                        existing = db.query(DocumentChunkModel).filter(
                            DocumentChunkModel.chunk_id == chunk_id
                        ).first()
                        
                        if existing:
                            logger.debug(f"Chunk {chunk_idx}: duplicate")
                            chunks_skipped += 1
                            continue
                        
                        # Verify chunk content
                        chunk_text_clean = chunk_text.strip()
                        if not chunk_text_clean:
                            logger.debug(f"Chunk {chunk_idx}: empty")
                            chunks_skipped += 1
                            continue
                        
                        chunk = DocumentChunkModel(
                            chunk_id=chunk_id,
                            document_id=doc_id,
                            content=chunk_text_clean[:5000],
                            chunk_index=chunk_idx,
                            topic=file_name,
                            category="document",
                            tags=["gateway", "uploaded"],
                        )
                        batch_buffer.append(chunk)
                        doc_chunks_created += 1
                        
                        if len(batch_buffer) >= batch_size:
                            try:
                                db.add_all(batch_buffer)
                                db.commit()
                                chunks_created += len(batch_buffer)
                                logger.info(f"Batch committed: {chunks_created} total chunks")
                                batch_buffer = []
                            except Exception as batch_err:
                                logger.error(f"Batch commit error: {batch_err}")
                                db.rollback()
                                batch_buffer = []
                    
                    logger.info(f"Document done: {doc_chunks_created} chunks created")
                        
                except Exception as doc_err:
                    logger.error(f"Error processing document: {doc_err}", exc_info=True)
                    chunks_skipped += 1
                    continue
            
            # Final commit
            if batch_buffer:
                try:
                    db.add_all(batch_buffer)
                    db.commit()
                    chunks_created += len(batch_buffer)
                    logger.info(f"Final batch: {chunks_created} total new chunks")
                except Exception as final_err:
                    logger.error(f"Final commit error: {final_err}")
                    db.rollback()
            
            # Verify
            chunk_count_after = db.query(DocumentChunkModel).count()
            elapsed = time.time() - start_time
            
            logger.info(f"Rebuild complete in {elapsed:.1f}s")
            logger.info(f"Chunk count: {chunk_count_before} → {chunk_count_after} ({chunks_created} new)")
            logger.info(f"Skipped: {chunks_skipped} items")
            
        except Exception as e:
            logger.error(f"Rebuild failed: {e}", exc_info=True)
            try:
                if db:
                    db.rollback()
            except:
                pass
        finally:
            if db:
                try:
                    db.close()
                except:
                    pass


    def _split_text_into_chunks(
        self, text: str, chunk_size: int = 500, overlap: int = 50
    ) -> List[str]:
        import re
        
        if not text or len(text) < 10:
            return []
        
        max_chunks = 200
        chunks = []
        
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        current_chunk = ""
        for sentence in sentences:
            if len(chunks) >= max_chunks:
                logger.warning(f"Reached max chunks limit ({max_chunks})")
                break
            
            if current_chunk and len(current_chunk) + len(sentence) > chunk_size:
                chunks.append(current_chunk.strip())
                current_chunk = current_chunk[-overlap:] if overlap > 0 else ""
            
            current_chunk += " " + sentence if current_chunk else sentence
        
        if current_chunk.strip() and len(chunks) < max_chunks:
            chunks.append(current_chunk.strip())
        
        return chunks

    def _search_gateway_documents(self, query: str, top_k: int = 5) -> List[RetrievedDocument]:
        results = []
        
        try:
            logger.info(f"Fallback search in gateway DB...")
            
            gateway_docs = self.quiz_data.get_gateway_documents(limit=100)
            
            if not gateway_docs:
                logger.warning("⚠️ No documents in gateway DB")
                return []
            
            query_lower = query.lower()
            query_words = query_lower.split()
            
            scored_docs = []
            for doc in gateway_docs:
                content = (doc.get("extracted_text") or doc.get("summary") or "").lower()
                
                match_score = 0
                for word in query_words:
                    match_score += content.count(word)
                
                if match_score > 0:
                    scored_docs.append((match_score, doc, content))
            
            scored_docs.sort(key=lambda x: x[0], reverse=True)
            
            logger.info(f"  Found {len(scored_docs)} matching documents")
            
            for score, doc, content in scored_docs[:top_k]:
                chunks = self._split_text_into_chunks(content, chunk_size=500, overlap=50)
                
                for chunk_idx, chunk_content in enumerate(chunks[:2]): 
                    chunk_content_clean = chunk_content.strip()
                    if chunk_content_clean:
                        results.append(RetrievedDocument(
                            document_id=doc.get("document_id"),
                            content=chunk_content_clean,
                            metadata={
                                "chunk_id": f"gateway_{doc.get('document_id')}_{chunk_idx}",
                                "topic": doc.get("file_name"),
                                "source": "gateway_documents_db"
                            },
                            relevance_score=min(0.9, 0.5 + (score * 0.1))
                        ))
            
            logger.info(f"Fallback search returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Fallback search error: {e}", exc_info=True)
            return []
