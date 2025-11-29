"""
Database models for Quiz Generator Service
=========================================

SQLAlchemy models for quiz generation, templates, and history.
"""

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Float,
    Boolean,
    JSON,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./quiz_generator.db")
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)

Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class QuizTemplate(Base):
    """Quiz generation templates for reuse."""

    __tablename__ = "quiz_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True)
    description = Column(Text)
    content_sections = Column(JSON)  # Structured content data
    default_config = Column(JSON)  # Default generation settings
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    usage_count = Column(Integer, default=0)


class GenerationHistory(Base):
    """History of quiz generations for analytics."""

    __tablename__ = "generation_history"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(100), unique=True, index=True)
    quiz_id = Column(String(100), index=True)

    # Input data
    sections_count = Column(Integer)
    requested_questions = Column(Integer)
    question_types = Column(JSON)

    # Generation results
    generated_questions = Column(Integer)
    generation_time = Column(Float)  # seconds
    model_used = Column(String(50))

    # Validation results
    validation_score = Column(Float)
    high_risk_count = Column(Integer, default=0)
    validation_issues = Column(JSON)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default="completed")  # completed, failed, pending
    error_message = Column(Text, nullable=True)


class GeneratedQuiz(Base):
    """Store generated quizzes for caching and reuse."""

    __tablename__ = "generated_quizzes"

    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(String(100), unique=True, index=True)

    # Quiz content
    questions_data = Column(JSON)  # Full quiz JSON
    quiz_metadata = Column(JSON)  # Generation metadata

    # Source information
    source_sections = Column(JSON)
    generation_config = Column(JSON)

    # Validation info
    validation_summary = Column(JSON)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # For cache expiration

    # Usage tracking
    access_count = Column(Integer, default=0)
    last_accessed = Column(DateTime, default=datetime.utcnow)


class ContentCache(Base):
    """Cache for processed content to avoid re-processing."""

    __tablename__ = "content_cache"

    id = Column(Integer, primary_key=True, index=True)
    content_hash = Column(String(64), unique=True, index=True)  # SHA256 hash

    # Original content
    sections_data = Column(JSON)

    # Processed content
    processed_content = Column(Text)
    extraction_metadata = Column(JSON)

    # Cache metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    hits_count = Column(Integer, default=0)
    last_hit = Column(DateTime, default=datetime.utcnow)


# Database initialization
def create_tables():
    """Create all tables in the database."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


if __name__ == "__main__":
    print("Creating Quiz Generator database tables...")
    create_tables()
    print("✅ Database tables created successfully!")
