"""
Alert and notification schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal


class AlertRuleCreate(BaseModel):
    """Schema for creating an alert rule."""
    station_id: int
    area_id: int
    rule_name: str = Field(..., min_length=1, max_length=120)
    metric: str = Field(..., min_length=1, max_length=80)
    operator: str = Field(..., pattern=r"^(>|>=|<|<=|=|!=)$")
    threshold_value: Decimal = Field(..., decimal_places=6)
    window_minutes: int = Field(..., gt=0)
    severity: str = Field(..., pattern=r"^(LOW|MEDIUM|HIGH|CRITICAL)$")
    is_enabled: bool = True


class AlertRuleResponse(BaseModel):
    """Schema for alert rule data in responses."""
    alert_rule_id: int
    station_id: int
    area_id: int
    rule_name: str
    metric: str
    operator: str
    threshold_value: Decimal
    window_minutes: int
    severity: str
    is_enabled: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AlertResponse(BaseModel):
    """Schema for alert data in responses."""
    alert_id: int
    alert_rule_id: int
    station_id: int
    user_id: int
    triggered_at: datetime
    severity: str
    status: str
    summary: Optional[str] = None
    details_json: Optional[str] = None
    acknowledged_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class NotificationResponse(BaseModel):
    """Schema for notification data in responses."""
    notification_id: int
    alert_id: int
    user_id: int
    channel: str
    destination: str
    status: str
    queued_at: datetime
    sent_at: Optional[datetime] = None
    provider_message_id: Optional[str] = None

    class Config:
        from_attributes = True


class AlertRuleUpdate(BaseModel):
    """Schema for updating an alert rule."""
    rule_name: Optional[str] = Field(None, min_length=1, max_length=120)
    threshold_value: Optional[Decimal] = None
    is_enabled: Optional[bool] = None


class AlertStatusUpdate(BaseModel):
    """Schema for updating alert status."""
    status: str = Field(..., pattern=r"^(TRIGGERED|ACKNOWLEDGED|RESOLVED|FALSE_POSITIVE)$")
    summary: Optional[str] = None