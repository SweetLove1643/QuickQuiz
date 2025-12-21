import logging
import os
import sqlite3
from contextlib import closing
from django.conf import settings
import time

logger = logging.getLogger(__name__)

RAG_DB_PATH = os.path.abspath(os.path.join(
    settings.BASE_DIR, "..", "rag_chatbot_service", "rag_chatbot.db"
))


def create_rag_chunks_table():
    try:
        os.makedirs(os.path.dirname(RAG_DB_PATH), exist_ok=True)
        with closing(sqlite3.connect(RAG_DB_PATH)) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS document_chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chunk_id TEXT UNIQUE NOT NULL,
                    document_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    topic TEXT NOT NULL,
                    category TEXT NOT NULL,
                    tags JSON,
                    embedding_vector TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
        logger.info(f"RAG chunks table ready: {RAG_DB_PATH}")
        return True
    except Exception as e:
        logger.error(f"Failed to create RAG chunks table: {e}", exc_info=True)
        return False


def split_text_into_chunks(text: str, chunk_size: int = 500, overlap: int = 50) -> list:
    chunks = []
    if not text or len(text) < chunk_size:
        return [text]
    
    step = chunk_size - overlap
    for i in range(0, len(text), step):
        chunk = text[i:i + chunk_size]
        if chunk.strip():
            chunks.append(chunk)
        
        if i + chunk_size >= len(text):
            break
    
    return chunks if chunks else [text]


def insert_document_to_rag_db(document_data: dict) -> bool:
    try:
        logger.info(f"Syncing document to RAG DB: {document_data['document_id']}")
        
        if not create_rag_chunks_table():
            return False
        
        doc_id = document_data.get("document_id")
        file_name = document_data.get("file_name", "Document")
        extracted_text = (document_data.get("extracted_text") or "").strip()
        summary_text = (document_data.get("summary") or "").strip()
        
        content = extracted_text if len(extracted_text) >= len(summary_text) else summary_text
        
        if not content or len(content) < 20:
            logger.warning(f"Document content too short, skip: {len(content)} chars")
            return False
        
        text_chunks = split_text_into_chunks(content, chunk_size=500, overlap=50)
        logger.info(f"Split into {len(text_chunks)} chunks")
        
        with closing(sqlite3.connect(RAG_DB_PATH, timeout=30)) as conn:
            conn.execute("DELETE FROM document_chunks WHERE document_id = ?", (doc_id,))

            inserted = 0
            for idx, chunk in enumerate(text_chunks):
                chunk_id = f"{doc_id}_{idx}_{int(time.time())}"

                cur = conn.execute("""
                    INSERT INTO document_chunks
                    (chunk_id, document_id, content, chunk_index, topic, category, tags)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    chunk_id,
                    doc_id,
                    chunk[:5000],
                    idx,
                    file_name,
                    "document",
                    '["gateway"]'
                ))

                if cur.rowcount == 1:
                    inserted += 1

            conn.commit()
            logger.info(f"RAG DB insert: {inserted} chunks")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to sync document to RAG DB: {e}", exc_info=True)
        return False