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

DATABASE_URL = "sqlite:///./quiz_generator_service.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class QuizTemplate(Base):

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

    __tablename__ = "generation_history"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(100), unique=True, index=True)
    quiz_id = Column(String(100), index=True)

    sections_count = Column(Integer)
    requested_questions = Column(Integer)
    question_types = Column(JSON)

    generated_questions = Column(Integer)
    generation_time = Column(Float) 
    model_used = Column(String(50))

    validation_score = Column(Float)
    high_risk_count = Column(Integer, default=0)
    validation_issues = Column(JSON)

    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20), default="completed")
    error_message = Column(Text, nullable=True)


class GeneratedQuiz(Base):
    __tablename__ = "generated_quizzes"

    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(String(100), unique=True, index=True)
    user_id = Column(String(100), index=True) 

    questions_data = Column(JSON) 
    quiz_metadata = Column(JSON) 
    title = Column(String(500), nullable=True)

    source_sections = Column(JSON)
    generation_config = Column(JSON)
    document_id = Column(String(100), nullable=True, index=True)  

    validation_summary = Column(JSON)

    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True) 

    access_count = Column(Integer, default=0)
    last_accessed = Column(DateTime, default=datetime.utcnow)


class ContentCache(Base):
    __tablename__ = "content_cache"

    id = Column(Integer, primary_key=True, index=True)
    content_hash = Column(String(64), unique=True, index=True)  

    sections_data = Column(JSON)

    processed_content = Column(Text)
    extraction_metadata = Column(JSON)

    created_at = Column(DateTime, default=datetime.utcnow)
    hits_count = Column(Integer, default=0)
    last_hit = Column(DateTime, default=datetime.utcnow)


def create_tables():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


if __name__ == "__main__":
    print("Creating Quiz Generator database tables...")
    create_tables()
    print("Database tables created successfully!")
