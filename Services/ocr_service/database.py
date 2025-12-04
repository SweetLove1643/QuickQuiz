from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

# Database setup
DATABASE_URL = "sqlite:///./ocr_service.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Database Models
class OCRRequestModel(Base):
    __tablename__ = "ocr_requests"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    processing_time = Column(Float, nullable=False)
    num_images = Column(Integer, nullable=False)
    extracted_text = Column(Text, nullable=False)
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


async def log_ocr_request(
    filename: str,
    file_size: int,
    processing_time: float,
    num_images: int,
    extracted_text: str,
):
    """Log OCR request to database"""
    try:
        db = SessionLocal()

        ocr_request = OCRRequestModel(
            filename=filename,
            file_size=file_size,
            processing_time=processing_time,
            num_images=num_images,
            extracted_text=extracted_text,
        )

        db.add(ocr_request)
        db.commit()
        db.refresh(ocr_request)

        return ocr_request
    except Exception as e:
        print(f"Error logging OCR request: {e}")
        return None
    finally:
        db.close()


async def get_ocr_stats():
    """Get OCR service statistics"""
    try:
        db = SessionLocal()

        total_requests = db.query(OCRRequestModel).count()
        total_images = (
            db.query(OCRRequestModel)
            .with_entities(db.func.sum(OCRRequestModel.num_images))
            .scalar()
            or 0
        )

        avg_processing_time = (
            db.query(OCRRequestModel)
            .with_entities(db.func.avg(OCRRequestModel.processing_time))
            .scalar()
            or 0.0
        )

        total_processing_time = (
            db.query(OCRRequestModel)
            .with_entities(db.func.sum(OCRRequestModel.processing_time))
            .scalar()
            or 0.0
        )

        return {
            "total_requests": total_requests,
            "total_images_processed": total_images,
            "average_processing_time": round(avg_processing_time, 3),
            "total_processing_time": round(total_processing_time, 3),
        }
    except Exception as e:
        print(f"Error getting OCR stats: {e}")
        return {
            "total_requests": 0,
            "total_images_processed": 0,
            "average_processing_time": 0.0,
            "total_processing_time": 0.0,
        }
    finally:
        db.close()
