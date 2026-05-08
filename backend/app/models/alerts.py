"""
Alert and notification models for flood warnings.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, BigInteger, Boolean, Numeric, Text, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class UserAreaSubscription(Base):
    """User subscriptions to specific geographic areas for alerts."""
    __tablename__ = "user_area_subscriptions"

    subscription_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    area_id = Column(Integer, ForeignKey("geographic_areas.area_id"), nullable=False)
    preference_json = Column(Text, nullable=True)  # User preferences as JSON
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="subscriptions")
    area = relationship("GeographicArea", back_populates="subscriptions")

    def __repr__(self):
        return f"<UserAreaSubscription(subscription_id={self.subscription_id}, user_id={self.user_id}, area_id={self.area_id})>"


class AlertRule(Base):
    """Rules for triggering alerts based on sensor thresholds or model outputs."""
    __tablename__ = "alert_rules"

    alert_rule_id = Column(Integer, primary_key=True, index=True)
    station_id = Column(Integer, ForeignKey("stations.station_id"), nullable=False)
    area_id = Column(Integer, ForeignKey("geographic_areas.area_id"), nullable=False)
    rule_name = Column(String(120), nullable=False)
    metric = Column(String(80), nullable=False)  # e.g., 'water_level', 'rainfall'
    operator = Column(String(10), nullable=False)  # >, >=, <, <=, =, !=
    threshold_value = Column(Numeric(18, 6), nullable=False)
    window_minutes = Column(Integer, nullable=False)
    severity = Column(String(20), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    is_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    station = relationship("Station", back_populates="alert_rules")
    area = relationship("GeographicArea", back_populates="alert_rules")
    alerts = relationship("Alert", back_populates="alert_rule")

    def __repr__(self):
        return f"<AlertRule(alert_rule_id={self.alert_rule_id}, name='{self.rule_name}', threshold={self.threshold_value})>"


class Alert(Base):
    """Triggered alerts based on alert rules."""
    __tablename__ = "alerts"

    alert_id = Column(BigInteger, primary_key=True, index=True)
    alert_rule_id = Column(Integer, ForeignKey("alert_rules.alert_rule_id"), nullable=False)
    station_id = Column(Integer, ForeignKey("stations.station_id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    triggered_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    severity = Column(String(20), nullable=False)  # LOW, MEDIUM, HIGH, CRITICAL
    status = Column(String(30), nullable=False)  # TRIGGERED, ACKNOWLEDGED, RESOLVED, FALSE_POSITIVE
    summary = Column(String(1000), nullable=True)
    details_json = Column(Text, nullable=True)  # Alert details as JSON
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)

    alert_rule = relationship("AlertRule", back_populates="alerts")
    station = relationship("Station", back_populates="alerts")
    user = relationship("User", back_populates="alerts")
    notifications = relationship("Notification", back_populates="alert", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Alert(alert_id={self.alert_id}, status='{self.status}', severity='{self.severity}')>"


class Notification(Base):
    """Notifications sent to users about alerts."""
    __tablename__ = "notifications"

    notification_id = Column(BigInteger, primary_key=True, index=True)
    alert_id = Column(BigInteger, ForeignKey("alerts.alert_id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    channel = Column(String(20), nullable=False)  # EMAIL, SMS, PUSH, WEBHOOK
    destination = Column(String(256), nullable=False)  # Email address, phone number, etc.
    status = Column(String(30), nullable=False)  # QUEUED, SENT, FAILED
    queued_at = Column(DateTime(timezone=True), server_default=func.now())
    sent_at = Column(DateTime(timezone=True), nullable=True)
    provider_message_id = Column(String(128), nullable=True)

    alert = relationship("Alert", back_populates="notifications")
    user = relationship("User", back_populates="notifications")

    def __repr__(self):
        return f"<Notification(notification_id={self.notification_id}, channel='{self.channel}', status='{self.status}')>"