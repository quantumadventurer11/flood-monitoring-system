"""
Data ingestion models for satellite and sensor data pipelines.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class DataSource(Base):
    """External data sources (satellite APIs, weather services, etc.)."""
    __tablename__ = "data_sources"

    data_source_id = Column(Integer, primary_key=True, index=True)
    source_name = Column(String(120), nullable=False)
    source_type = Column(String(50), nullable=False)  # e.g., 'SATELLITE', 'WEATHER', 'SENSOR'
    provider = Column(String(120), nullable=True)  # e.g., 'Copernicus', 'NOAA'
    endpoint = Column(String(500), nullable=True)
    auth_method = Column(String(50), nullable=True)  # e.g., 'OAUTH2', 'API_KEY'
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    ingest_jobs = relationship("IngestJob", back_populates="data_source")

    def __repr__(self):
        return f"<DataSource(data_source_id={self.data_source_id}, name='{self.source_name}')>"


class IngestJob(Base):
    """Tracks data ingestion jobs (downloads, processing, etc.)."""
    __tablename__ = "ingest_jobs"

    ingest_job_id = Column(Integer, primary_key=True, index=True)
    data_source_id = Column(Integer, ForeignKey("data_sources.data_source_id"), nullable=False)
    job_type = Column(String(50), nullable=False)  # e.g., 'DOWNLOAD', 'PROCESS', 'VALIDATE'
    status = Column(String(30), nullable=False)  # PENDING, RUNNING, COMPLETED, FAILED
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    parameters_json = Column(Text, nullable=True)  # JSON parameters for the job
    output_location = Column(String(500), nullable=True)  # Path to output files

    data_source = relationship("DataSource", back_populates="ingest_jobs")
    errors = relationship("IngestError", back_populates="ingest_job", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<IngestJob(ingest_job_id={self.ingest_job_id}, status='{self.status}')>"


class IngestError(Base):
    """Errors encountered during data ingestion."""
    __tablename__ = "ingest_errors"

    ingest_error_id = Column(Integer, primary_key=True, index=True)
    ingest_job_id = Column(Integer, ForeignKey("ingest_jobs.ingest_job_id", ondelete="CASCADE"), nullable=False)
    error_code = Column(String(50), nullable=True)
    error_message = Column(String(4000), nullable=False)
    occurred_at = Column(DateTime(timezone=True), server_default=func.now())
    context_json = Column(Text, nullable=True)  # Additional error context

    ingest_job = relationship("IngestJob", back_populates="errors")

    def __repr__(self):
        return f"<IngestError(ingest_error_id={self.ingest_error_id}, error='{self.error_message}')>"