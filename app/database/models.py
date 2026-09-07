from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime
from sqlalchemy.sql import func

from app.database.connection import Base


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(String(100), unique=True, index=True, nullable=False)
    filename = Column(String(255), nullable=False)
    sha256 = Column(String(64), nullable=False)
    integrity_status = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Model(Base):
    __tablename__ = "models"

    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(String(100), unique=True, index=True, nullable=False)
    filename = Column(String(255), nullable=False)
    sha256 = Column(String(64), nullable=False)
    integrity_status = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Inference(Base):
    __tablename__ = "inferences"

    id = Column(Integer, primary_key=True, index=True)
    inference_id = Column(String(100), unique=True, index=True, nullable=False)
    input_hash = Column(String(64), nullable=False)
    model_hash = Column(String(64), nullable=False)
    output_hash = Column(String(64), nullable=False)
    integrity_status = Column(String(50), nullable=False)
    replay_detected = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Finding(Base):
    __tablename__ = "findings"

    id = Column(Integer, primary_key=True, index=True)
    asset_type = Column(String(50), nullable=False)
    asset_id = Column(String(100), nullable=False)
    severity = Column(String(20), nullable=False)
    reason = Column(Text, nullable=False)
    evidence = Column(Text)
    confidence = Column(Float)
    recommendation = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AssuranceAssessment(Base):
    __tablename__ = "assurance_assessments"

    id = Column(Integer, primary_key=True, index=True)
    assurance_id = Column(String(100), unique=True, index=True, nullable=False)
    overall_status = Column(String(50), nullable=False)
    risk_score = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(100), nullable=False)
    asset_type = Column(String(50))
    asset_id = Column(String(100))
    event_hash = Column(String(64), nullable=False)
    previous_hash = Column(String(64))
    created_at = Column(DateTime(timezone=True), server_default=func.now())