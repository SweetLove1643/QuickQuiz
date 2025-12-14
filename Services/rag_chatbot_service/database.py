from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Text,
    JSON,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
import sqlite3
import json
from typing import List, Dict, Any, Optional

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# Database setup for RAG service
DATABASE_URL = "sqlite:///./rag_chatbot.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Database Models for RAG service
class ConversationModel(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, nullable=True, index=True)
    title = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    message_count = Column(Integer, default=0)
    last_message = Column(Text, nullable=True)


class ChatMessageModel(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(String, nullable=False, index=True)
    user_query = Column(Text, nullable=False)
    assistant_response = Column(Text, nullable=False)
    retrieved_documents = Column(JSON, nullable=True)
    context_sources = Column(JSON, nullable=True)
    processing_time = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class DocumentChunkModel(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    chunk_id = Column(String, unique=True, index=True)
    document_id = Column(String, nullable=False, index=True)
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    topic = Column(String, nullable=False, index=True)
    category = Column(String, nullable=False, index=True)
    tags = Column(JSON, nullable=True)
    embedding_vector = Column(Text, nullable=True)  # JSON string of vector
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    """Initialize database and create tables"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class QuizDataAccess:
    """Access quiz data from other microservices for RAG context"""

    def __init__(self):
        # ✅ FIX 1: Compute paths carefully
        repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        
        self.quiz_generator_db = os.path.join(
            repo_root, "services", "quiz_generator_service", "quiz_generator_service.db"
        )
        self.quiz_evaluator_db = os.path.join(
            repo_root, "services", "quiz_evaluator_service", "quiz_evaluator.db"
        )
        self.gateway_documents_db = os.path.join(
            repo_root, "services", "gateway_service", "documents.db"
        )
        
        # ✅ FIX 2: Log paths on init
        logger.info(f"🔧 QuizDataAccess initialized with paths:")
        logger.info(f"  quiz_generator_db: {self.quiz_generator_db}")
        logger.info(f"  gateway_documents_db: {self.gateway_documents_db}")
        
        # ✅ FIX 3: Verify paths exist
        logger.info(f"  quiz_generator exists: {os.path.exists(self.quiz_generator_db)}")
        logger.info(f"  gateway_documents exists: {os.path.exists(self.gateway_documents_db)}")
        
    def get_quiz_templates(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent quiz templates for context"""
        try:
            if not os.path.exists(self.quiz_generator_db):
                logger.info(f"Quiz templates DB not found: {self.quiz_generator_db}")
                return []

            conn = sqlite3.connect(self.quiz_generator_db)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # FIX: Correct schema - quiz_templates has: id, name, description, content_sections
            query = """
            SELECT name, description, content_sections, created_at
            FROM quiz_templates 
            WHERE is_active = 1
            ORDER BY created_at DESC 
            LIMIT ?
            """
            cursor.execute(query, (limit,))
            results = cursor.fetchall()
            conn.close()

            templates = []
            for row in results:
                try:
                    content_sections = (
                        json.loads(row["content_sections"])
                        if isinstance(row["content_sections"], str)
                        else row["content_sections"] or {}
                    )
                    templates.append({
                        "name": row["name"],
                        "description": row["description"],
                        "content_sections": content_sections,
                        "created_at": row["created_at"],
                    })
                except Exception as e:
                    logger.warning(f"Error parsing template: {e}")
                    continue

            logger.info(f"Retrieved {len(templates)} quiz templates")
            return templates
        except Exception as e:
            logger.error(f"Error accessing quiz templates: {e}")
            return []
    

    def get_gateway_documents(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Read documents saved by Gateway (documents.db)."""
        logger.info(f"🔍 get_gateway_documents() called, limit={limit}")
        
        try:
            # ✅ CRITICAL FIX: Check path again (not just at __init__)
            if not os.path.exists(self.gateway_documents_db):
                logger.error(f"❌ Gateway documents DB not found at: {self.gateway_documents_db}")
                logger.info(f"  Expected path: {self.gateway_documents_db}")
                logger.info(f"  Current working directory: {os.getcwd()}")
                # Try to find it
                alt_path = os.path.join(os.getcwd(), "..", "gateway_service", "documents.db")
                if os.path.exists(alt_path):
                    logger.warning(f"⚠️ Found at alternative path: {alt_path}")
                    self.gateway_documents_db = alt_path
                else:
                    return []
            
            logger.info(f"✅ Gateway DB file exists: {self.gateway_documents_db}")
            
            # ✅ CRITICAL FIX: Use timeout để avoid lock
            conn = sqlite3.connect(self.gateway_documents_db, timeout=5.0)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            
            # List all tables
            try:
                cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cur.fetchall()
                logger.info(f"📋 Tables in gateway DB: {[t[0] for t in tables]}")
            except Exception as table_err:
                logger.error(f"❌ Error listing tables: {table_err}")
            
            # Check 'documents' table exists
            cur.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='documents'"
            )
            table_exists = cur.fetchone()
            if not table_exists:
                logger.error("❌ 'documents' table does not exist in gateway DB")
                conn.close()
                return []
            
            logger.info("✅ 'documents' table exists")
            
            # Get table schema
            try:
                cur.execute("PRAGMA table_info(documents)")
                columns = cur.fetchall()
                column_names = [col[1] for col in columns]
                logger.info(f"📋 documents table columns: {column_names}")
            except Exception as schema_err:
                logger.error(f"❌ Error getting table schema: {schema_err}")
            
            # Count total documents
            try:
                cur.execute("SELECT COUNT(*) FROM documents")
                count = cur.fetchone()[0]
                logger.info(f"📊 Total documents in gateway DB: {count}")
            except Exception as count_err:
                logger.error(f"❌ Error counting documents: {count_err}")
            
            # ✅ CRITICAL FIX: Query with ORDER BY DESC (newest first)
            try:
                query = """
                SELECT id as document_id, file_name, extracted_text, summary, created_at
                FROM documents
                ORDER BY datetime(created_at) DESC
                LIMIT ?
                """
                logger.info(f"🔍 Executing query...")
                cur.execute(query, (limit,))
                rows = cur.fetchall()
                logger.info(f"✅ Query executed successfully, retrieved: {len(rows)} rows")
            except Exception as query_err:
                logger.error(f"❌ Query error: {query_err}", exc_info=True)
                conn.close()
                return []
            finally:
                conn.close()
            
            # Convert rows to dicts
            result = []
            for row in rows:
                try:
                    doc_dict = dict(row)
                    result.append(doc_dict)
                except Exception as dict_err:
                    logger.error(f"❌ Error converting row to dict: {dict_err}")
                    continue
            
            logger.info(f"✅ Retrieved {len(result)} gateway documents")
            
            # Log document details
            for i, doc in enumerate(result[:5]):
                extracted_len = len(doc.get("extracted_text") or "") if doc.get("extracted_text") else 0
                summary_len = len(doc.get("summary") or "") if doc.get("summary") else 0
                logger.info(f"  Doc {i+1}: ID={doc.get('document_id')}, "
                        f"file={doc.get('file_name')}, "
                        f"extracted={extracted_len}ch, summary={summary_len}ch")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error accessing gateway documents: {e}", exc_info=True)
            return []


    def get_generated_quizzes(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent generated quizzes for context"""
        try:
            if not os.path.exists(self.quiz_generator_db):
                logger.info(f"Generated quizzes DB not found: {self.quiz_generator_db}")
                return []

            conn = sqlite3.connect(self.quiz_generator_db)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # FIX: Correct schema - generated_quizzes has: quiz_id, user_id, questions_data, title, document_id
            query = """
            SELECT quiz_id, user_id, questions_data, title, document_id, created_at
            FROM generated_quizzes 
            ORDER BY created_at DESC 
            LIMIT ?
            """
            cursor.execute(query, (limit,))
            results = cursor.fetchall()
            conn.close()

            quizzes = []
            for row in results:
                try:
                    questions_data = (
                        json.loads(row["questions_data"])
                        if isinstance(row["questions_data"], str)
                        else row["questions_data"] or []
                    )
                    quizzes.append({
                        "quiz_id": row["quiz_id"],
                        "user_id": row["user_id"],
                        "title": row["title"],
                        "questions_data": questions_data,
                        "document_id": row["document_id"],
                        "created_at": row["created_at"],
                    })
                except Exception as e:
                    logger.warning(f"Error parsing quiz: {e}")
                    continue

            logger.info(f"Retrieved {len(quizzes)} generated quizzes")
            return quizzes
        except Exception as e:
            logger.error(f"Error accessing generated quizzes: {e}")
            return []
    

    def get_evaluation_results(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent quiz evaluation results for context"""
        try:
            if not os.path.exists(self.quiz_evaluator_db):
                return []

            conn = sqlite3.connect(self.quiz_evaluator_db)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            query = """
            SELECT quiz_id, total_score, correct_answers, evaluation_details, created_at
            FROM evaluation_results 
            ORDER BY created_at DESC 
            LIMIT ?
            """
            cursor.execute(query, (limit,))
            results = cursor.fetchall()
            conn.close()

            return [dict(row) for row in results]
        except Exception as e:
            print(f"Error accessing evaluation results: {e}")
            return []

    def get_user_performance(
        self, user_id: Optional[str] = None, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get user performance data for context"""
        try:
            if not os.path.exists(self.quiz_evaluator_db):
                return []

            conn = sqlite3.connect(self.quiz_evaluator_db)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            if user_id:
                query = """
                SELECT user_id, average_score, total_quizzes, strong_subjects, weak_subjects, created_at
                FROM user_performance 
                WHERE user_id = ?
                ORDER BY created_at DESC 
                LIMIT ?
                """
                cursor.execute(query, (user_id, limit))
            else:
                query = """
                SELECT user_id, average_score, total_quizzes, strong_subjects, weak_subjects, created_at
                FROM user_performance 
                ORDER BY created_at DESC 
                LIMIT ?
                """
                cursor.execute(query, (limit,))

            results = cursor.fetchall()
            conn.close()

            return [dict(row) for row in results]
        except Exception as e:
            print(f"Error accessing user performance: {e}")
            return []

    def search_quiz_content(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search quiz content for relevant context"""
        results = []

        # Search in quiz templates
        templates = self.get_quiz_templates(limit * 2)
        for template in templates:
            if template.get("questions"):
                try:
                    questions = (
                        json.loads(template["questions"])
                        if isinstance(template["questions"], str)
                        else template["questions"]
                    )
                    content = (
                        f"Subject: {template['subject']}, Topic: {template['topic']}\n"
                    )
                    content += "\n".join(
                        [
                            q.get("question", "")
                            for q in questions
                            if isinstance(q, dict)
                        ]
                    )

                    if query.lower() in content.lower():
                        results.append(
                            {
                                "type": "quiz_template",
                                "subject": template["subject"],
                                "topic": template["topic"],
                                "content": content[:500],
                                "created_at": template["created_at"],
                            }
                        )
                except:
                    continue

        return results[:limit]


# Logging functions for RAG operations
async def log_conversation(
    conversation_id: str, user_id: Optional[str] = None, title: str = "New Conversation"
):
    """Log new conversation to database"""
    try:
        db = SessionLocal()

        conversation = ConversationModel(
            id=conversation_id, user_id=user_id, title=title
        )

        db.add(conversation)
        db.commit()
        db.refresh(conversation)

        return conversation
    except Exception as e:
        print(f"Error logging conversation: {e}")
        return None
    finally:
        db.close()


async def log_chat_message(
    conversation_id: str,
    user_query: str,
    assistant_response: str,
    retrieved_documents: List[Dict] = None,
    context_sources: List[str] = None,
    processing_time: float = None,
):
    """Log chat message to database"""
    try:
        db = SessionLocal()

        message = ChatMessageModel(
            conversation_id=conversation_id,
            user_query=user_query,
            assistant_response=assistant_response,
            retrieved_documents=retrieved_documents,
            context_sources=context_sources,
            processing_time=processing_time,
        )

        db.add(message)
        db.commit()
        db.refresh(message)

        # Update conversation
        conversation = (
            db.query(ConversationModel)
            .filter(ConversationModel.id == conversation_id)
            .first()
        )

        if conversation:
            conversation.message_count += 1
            conversation.last_message = user_query[:100]
            conversation.updated_at = datetime.utcnow()
            db.commit()

        return message
    except Exception as e:
        print(f"Error logging chat message: {e}")
        return None
    finally:
        db.close()


async def get_conversation_history(conversation_id: str, limit: int = 10) -> List[Dict]:
    """Get conversation history from database"""
    try:
        db = SessionLocal()

        messages = (
            db.query(ChatMessageModel)
            .filter(ChatMessageModel.conversation_id == conversation_id)
            .order_by(ChatMessageModel.created_at.desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "user_query": msg.user_query,
                "assistant_response": msg.assistant_response,
                "created_at": msg.created_at.isoformat(),
                "context_sources": msg.context_sources,
            }
            for msg in reversed(messages)
        ]

    except Exception as e:
        print(f"Error getting conversation history: {e}")
        return []
    finally:
        db.close()


# Initialize quiz data access
quiz_data_access = QuizDataAccess()
