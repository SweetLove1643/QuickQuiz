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
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import os

DATABASE_URL = "sqlite:///./quiz_evaluator_service.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class QuizSubmission(Base):

    __tablename__ = "quiz_submissions"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(String(100), unique=True, index=True)
    quiz_id = Column(String(100), index=True)
    user_id = Column(String(100), index=True)

    questions_data = Column(JSON)  
    user_answers = Column(JSON) 
    correct_answers = Column(JSON)  

    total_questions = Column(Integer)
    correct_count = Column(Integer)
    score_percentage = Column(Float)
    completion_time = Column(Integer)  

    submitted_at = Column(DateTime, default=datetime.utcnow)
    session_id = Column(String(100), nullable=True)
    user_agent = Column(String(500), nullable=True)
    ip_address = Column(String(45), nullable=True)


class EvaluationResult(Base):

    __tablename__ = "evaluation_results"

    id = Column(Integer, primary_key=True, index=True)
    evaluation_id = Column(String(100), unique=True, index=True)
    submission_id = Column(String(100), index=True)


    detailed_analysis = Column(JSON) 
    performance_breakdown = Column(JSON) 
    ai_feedback = Column(JSON) 

    raw_score = Column(Float)
    weighted_score = Column(Float)
    grade_letter = Column(String(2))
    percentile_rank = Column(Float, nullable=True)


    strengths = Column(JSON) 
    weaknesses = Column(JSON)  
    recommendations = Column(JSON) 

    evaluated_at = Column(DateTime, default=datetime.utcnow)
    model_used = Column(String(50))
    processing_time = Column(Float)


class UserPerformance(Base):

    __tablename__ = "user_performance"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), index=True)


    total_submissions = Column(Integer, default=0)
    total_questions = Column(Integer, default=0)
    total_correct = Column(Integer, default=0)
    average_score = Column(Float, default=0.0)


    best_score = Column(Float, default=0.0)
    worst_score = Column(Float, default=0.0)
    recent_trend = Column(String(20))  

    topic_performance = Column(JSON)  
    difficulty_performance = Column(JSON)  

    average_completion_time = Column(Float)
    fastest_completion = Column(Float, nullable=True)

    first_submission = Column(DateTime)
    last_submission = Column(DateTime)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class LearningAnalytics(Base):

    __tablename__ = "learning_analytics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), index=True)

    learning_style = Column(String(50))
    preferred_difficulty = Column(String(20))
    peak_performance_time = Column(String(20)) 

    knowledge_gaps = Column(JSON)  
    mastery_topics = Column(JSON) 
    improvement_areas = Column(JSON) 

    study_plan = Column(JSON)  
    next_topics = Column(JSON)  
    difficulty_progression = Column(JSON)  

    confidence_scores = Column(JSON)
    actual_vs_perceived = Column(JSON) 

    last_analyzed = Column(DateTime, default=datetime.utcnow)
    analysis_version = Column(String(10), default="1.0")


class EvaluationHistory(Base):

    __tablename__ = "evaluation_history"

    id = Column(Integer, primary_key=True, index=True)
    evaluation_id = Column(String(100), index=True)


    total_evaluations = Column(Integer)
    average_processing_time = Column(Float)
    success_rate = Column(Float)

    question_types_distribution = Column(JSON)
    difficulty_distribution = Column(JSON)
    topic_distribution = Column(JSON)

    average_scores_by_topic = Column(JSON)
    common_mistakes = Column(JSON)
    trending_topics = Column(JSON)


    recorded_at = Column(DateTime, default=datetime.utcnow)


def create_tables():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


if __name__ == "__main__":
    print("Creating Quiz Evaluator database tables...")
    create_tables()
    print("Database tables created successfully!")
