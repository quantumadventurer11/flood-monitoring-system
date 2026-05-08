"""
Audit logging model for tracking user actions and system events.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class AuditLog(Base):
    """Audit trail for tracking user actions and system events."""
    __tablename__ = "audit_logs"

    audit_log_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    action_type = Column(String(50), nullable=False)  # e.g., 'LOGIN', 'CREATE', 'UPDATE', 'DELETE'
    entity_type = Column(String(50), nullable=False)  # e.g., 'USER', 'STATION', 'ALERT'
    entity_id = Column(String(64), nullable=False)  # ID of the affected entity
    metadata_json = Column(Text, nullable=True)  # Additional context as JSON
    occurred_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    source_ip = Column(String(45), nullable=True)

    user = relationship("User", back_populates="audit_logs")

    def __repr__(self):
        return f"<AuditLog(audit_log_id={self.audit_log_id}, action='{self.action_type}', entity='{self.entity_type}')>"