"""
ML model run tracking and input/output management.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class ModelRun(Base):
    """Tracks ML model execution runs for flood detection."""
    __tablename__ = "model_runs"

    model_run_id = Column(BigInteger, primary_key=True, index=True)
    model_name = Column(String(120), nullable=False)  # e.g., 'UNet', 'FPN', 'VisionTransformer'
    model_version = Column(String(50), nullable=False)
    run_started_at = Column(DateTime(timezone=True), server_default=func.now())
    run_completed_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(30), nullable=False)  # PENDING, RUNNING, COMPLETED, FAILED
    parameters_json = Column(Text, nullable=True)  # Model parameters as JSON
    notes = Column(String(1000), nullable=True)

    inputs = relationship("ModelInput", back_populates="model_run", cascade="all, delete-orphan")
    outputs = relationship("ModelOutput", back_populates="model_run", cascade="all, delete-orphan")
    flood_events = relationship("FloodEvent", back_populates="model_run")

    def __repr__(self):
        return f"<ModelRun(model_run_id={self.model_run_id}, model='{self.model_name}', status='{self.status}')>"


class ModelInput(Base):
    """Inputs used in a model run (satellite images, parameters, etc.)."""
    __tablename__ = "model_inputs"

    model_input_id = Column(BigInteger, primary_key=True, index=True)
    model_run_id = Column(BigInteger, ForeignKey("model_runs.model_run_id", ondelete="CASCADE"), nullable=False)
    input_type = Column(String(50), nullable=False)  # e.g., 'SATELLITE_IMAGE', 'RAINFALL_DATA'
    source_ref = Column(String(500), nullable=True)  # Reference to source data (file path, URL, etc.)
    time_start = Column(DateTime(timezone=True), nullable=True)
    time_end = Column(DateTime(timezone=True), nullable=True)
    input_metadata_json = Column(Text, nullable=True)  # Metadata about the input

    model_run = relationship("ModelRun", back_populates="inputs")

    def __repr__(self):
        return f"<ModelInput(model_input_id={self.model_input_id}, type='{self.input_type}')>"


class ModelOutput(Base):
    """Outputs produced by a model run (flood maps, predictions, etc.)."""
    __tablename__ = "model_outputs"

    model_output_id = Column(BigInteger, primary_key=True, index=True)
    model_run_id = Column(BigInteger, ForeignKey("model_runs.model_run_id", ondelete="CASCADE"), nullable=False)
    output_type = Column(String(50), nullable=False)  # e.g., 'FLOOD_MAP', 'RISK_SCORE'
    output_ref = Column(String(500), nullable=True)  # Reference to output (file path, URL, etc.)
    output_metadata_json = Column(Text, nullable=True)  # Metadata about the output
    produced_at = Column(DateTime(timezone=True), server_default=func.now())

    model_run = relationship("ModelRun", back_populates="outputs")

    def __repr__(self):
        return f"<ModelOutput(model_output_id={self.model_output_id}, type='{self.output_type}')>"