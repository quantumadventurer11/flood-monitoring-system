from datetime import date, datetime
from sqlalchemy import Date, DateTime, Float, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Region(Base):
    __tablename__ = "regions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    country: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    lat: Mapped[float] = mapped_column(Float)
    lon: Mapped[float] = mapped_column(Float)
    buffer_km: Mapped[float] = mapped_column(Float, default=50.0)
    risk_level: Mapped[str] = mapped_column(String(24), default="Low")


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    country: Mapped[str] = mapped_column(String(120), index=True)
    event_date: Mapped[date] = mapped_column(Date)
    flood_probability: Mapped[float] = mapped_column(Float)
    risk_level: Mapped[str] = mapped_column(String(24))
    classification: Mapped[str] = mapped_column(String(32))
    source: Mapped[str] = mapped_column(String(80), default="simulated")


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    country: Mapped[str] = mapped_column(String(120), index=True)
    message: Mapped[str] = mapped_column(Text)
    risk_level: Mapped[str] = mapped_column(String(24))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    country: Mapped[str] = mapped_column(String(120), index=True)
    lat: Mapped[float] = mapped_column(Float)
    lon: Mapped[float] = mapped_column(Float)
    target_date: Mapped[date] = mapped_column(Date)
    flood_probability: Mapped[float] = mapped_column(Float)
    risk_level: Mapped[str] = mapped_column(String(24))
    classification: Mapped[str] = mapped_column(String(32))
    confidence: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PaperResult(Base):
    __tablename__ = "paper_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    payload: Mapped[dict] = mapped_column(JSON)
