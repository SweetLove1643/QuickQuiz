from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

DATABASE_URL = "sqlite:///./summary_service.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class SummaryRequestModel(Base):
    __tablename__ = "summary_requests"

    id = Column(Integer, primary_key=True, index=True)
    content_type = Column(String, nullable=False) 
    input_text = Column(Text, nullable=False)
    summary = Column(Text, nullable=False)
    processing_method = Column(String, nullable=False)
    num_files = Column(Integer, nullable=True)
    processing_time = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def log_summary_request(
    content_type: str,
    input_text: str,
    summary: str,
    processing_method: str,
    num_files: int = None,
    processing_time: float = None,
):
    try:
        db = SessionLocal()

        summary_request = SummaryRequestModel(
            content_type=content_type,
            input_text=input_text,
            summary=summary,
            processing_method=processing_method,
            num_files=num_files,
            processing_time=processing_time,
        )

        db.add(summary_request)
        db.commit()
        db.refresh(summary_request)

        return summary_request
    except Exception as e:
        print(f"Error logging summary request: {e}")
        return None
    finally:
        db.close()


async def get_summary_stats():
    try:
        db = SessionLocal()

        total_requests = db.query(SummaryRequestModel).count()

        avg_processing_time = (
            db.query(SummaryRequestModel)
            .with_entities(db.func.avg(SummaryRequestModel.processing_time))
            .scalar()
            or 0.0
        )

        content_types = (
            db.query(
                SummaryRequestModel.content_type, db.func.count(SummaryRequestModel.id)
            )
            .group_by(SummaryRequestModel.content_type)
            .all()
        )

        summary_types = {ct: count for ct, count in content_types}

        return {
            "total_requests": total_requests,
            "average_processing_time": round(avg_processing_time, 3),
            "summary_types": summary_types,
        }
    except Exception as e:
        print(f"Error getting summary stats: {e}")
        return {
            "total_requests": 0,
            "average_processing_time": 0.0,
            "summary_types": {},
        }
    finally:
        db.close()
