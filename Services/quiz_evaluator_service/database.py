"""
Database models for Quiz Evaluator Service
==========================================

SQLAlchemy models for quiz evaluation, user performance, and analytics.
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
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import os

# Database setup
DATABASE_URL = "sqlite:///./quiz_evaluator_service.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class QuizSubmission(Base):
    """User quiz submissions and responses."""

    __tablename__ = "quiz_submissions"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(String(100), unique=True, index=True)
    quiz_id = Column(String(100), index=True)
    user_id = Column(String(100), index=True)

    # Submission data
    questions_data = Column(JSON)  # Questions with user answers
    user_answers = Column(JSON)  # User responses
    correct_answers = Column(JSON)  # Correct answers

    # Performance metrics
    total_questions = Column(Integer)
    correct_count = Column(Integer)
    score_percentage = Column(Float)
    completion_time = Column(Integer)  # seconds

    # Submission metadata
    submitted_at = Column(DateTime, default=datetime.utcnow)
    session_id = Column(String(100), nullable=True)
    user_agent = Column(String(500), nullable=True)
    ip_address = Column(String(45), nullable=True)


class EvaluationResult(Base):
    """Detailed evaluation results with AI analysis."""

    __tablename__ = "evaluation_results"

    id = Column(Integer, primary_key=True, index=True)
    evaluation_id = Column(String(100), unique=True, index=True)
    submission_id = Column(String(100), index=True)

    # Evaluation data
    detailed_analysis = Column(JSON)  # Per-question analysis
    performance_breakdown = Column(JSON)  # By topic, difficulty, etc.
    ai_feedback = Column(JSON)  # AI-generated feedback

    # Scoring details
    raw_score = Column(Float)
    weighted_score = Column(Float)
    grade_letter = Column(String(2))
    percentile_rank = Column(Float, nullable=True)

    # Analytics
    strengths = Column(JSON)  # Identified strong areas
    weaknesses = Column(JSON)  # Areas for improvement
    recommendations = Column(JSON)  # Learning recommendations

    # Processing metadata
    evaluated_at = Column(DateTime, default=datetime.utcnow)
    model_used = Column(String(50))
    processing_time = Column(Float)


class UserPerformance(Base):
    """Aggregated user performance analytics."""

    __tablename__ = "user_performance"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), index=True)

    # Overall statistics
    total_submissions = Column(Integer, default=0)
    total_questions = Column(Integer, default=0)
    total_correct = Column(Integer, default=0)
    average_score = Column(Float, default=0.0)

    # Performance trends
    best_score = Column(Float, default=0.0)
    worst_score = Column(Float, default=0.0)
    recent_trend = Column(String(20))  # improving, declining, stable

    # Topic performance
    topic_performance = Column(JSON)  # Performance by topic/subject
    difficulty_performance = Column(JSON)  # Performance by difficulty level

    # Time analytics
    average_completion_time = Column(Float)
    fastest_completion = Column(Float, nullable=True)

    # Timestamps
    first_submission = Column(DateTime)
    last_submission = Column(DateTime)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class LearningAnalytics(Base):
    """Learning analytics and insights."""

    __tablename__ = "learning_analytics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), index=True)

    # Learning patterns
    learning_style = Column(String(50))  # visual, auditory, kinesthetic
    preferred_difficulty = Column(String(20))  # easy, medium, hard
    peak_performance_time = Column(String(20))  # morning, afternoon, evening

    # Knowledge gaps
    knowledge_gaps = Column(JSON)  # Identified gaps
    mastery_topics = Column(JSON)  # Well-understood topics
    improvement_areas = Column(JSON)  # Areas needing work

    # Recommendations
    study_plan = Column(JSON)  # Personalized study recommendations
    next_topics = Column(JSON)  # Suggested next learning topics
    difficulty_progression = Column(JSON)  # Recommended difficulty path

    # Confidence tracking
    confidence_scores = Column(JSON)  # Self-reported confidence by topic
    actual_vs_perceived = Column(JSON)  # Actual performance vs confidence

    # Update tracking
    last_analyzed = Column(DateTime, default=datetime.utcnow)
    analysis_version = Column(String(10), default="1.0")


class EvaluationHistory(Base):
    """History of all evaluations for system analytics."""

    __tablename__ = "evaluation_history"

    id = Column(Integer, primary_key=True, index=True)
    evaluation_id = Column(String(100), index=True)

    # System metrics
    total_evaluations = Column(Integer)
    average_processing_time = Column(Float)
    success_rate = Column(Float)

    # Content metrics
    question_types_distribution = Column(JSON)
    difficulty_distribution = Column(JSON)
    topic_distribution = Column(JSON)

    # Performance metrics
    average_scores_by_topic = Column(JSON)
    common_mistakes = Column(JSON)
    trending_topics = Column(JSON)

    # Timestamp
    recorded_at = Column(DateTime, default=datetime.utcnow)


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
    print("Creating Quiz Evaluator database tables...")
    create_tables()
    print("✅ Database tables created successfully!")
