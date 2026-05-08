"""
Alert rules and notification API routes.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional

from ...database import get_db
from ...models.alerts import AlertRule, Alert, Notification, UserAreaSubscription
from ...schemas.alerts import (
    AlertRuleCreate, AlertRuleResponse, AlertRuleUpdate,
    AlertResponse, AlertStatusUpdate, NotificationResponse
)

router = APIRouter()


# ─── ALERT RULES ───────────────────────────────────────────────────────────────

@router.get("/rules", response_model=List[AlertRuleResponse])
def list_alert_rules(
    area_id: Optional[int] = Query(None),
    station_id: Optional[int] = Query(None),
    is_enabled: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """List alert rules with optional filtering."""
    query = db.query(AlertRule)
    if area_id:
        query = query.filter(AlertRule.area_id == area_id)
    if station_id:
        query = query.filter(AlertRule.station_id == station_id)
    if is_enabled is not None:
        query = query.filter(AlertRule.is_enabled == is_enabled)
    return query.all()


@router.post("/rules", response_model=AlertRuleResponse, status_code=status.HTTP_201_CREATED)
def create_alert_rule(rule_in: AlertRuleCreate, db: Session = Depends(get_db)):
    """Create a new alert rule."""
    rule = AlertRule(**rule_in.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.patch("/rules/{rule_id}", response_model=AlertRuleResponse)
def update_alert_rule(rule_id: int, update: AlertRuleUpdate, db: Session = Depends(get_db)):
    """Update an existing alert rule."""
    rule = db.query(AlertRule).filter(AlertRule.alert_rule_id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Alert rule not found")
    update_data = update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(rule, field, value)
    db.commit()
    db.refresh(rule)
    return rule


@router.delete("/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_alert_rule(rule_id: int, db: Session = Depends(get_db)):
    """Delete an alert rule."""
    rule = db.query(AlertRule).filter(AlertRule.alert_rule_id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Alert rule not found")
    db.delete(rule)
    db.commit()


# ─── ALERTS ────────────────────────────────────────────────────────────────────

@router.get("/", response_model=List[AlertResponse])
def list_alerts(
    station_id: Optional[int] = Query(None),
    severity: Optional[str] = Query(None),
    alert_status: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, le=500),
    db: Session = Depends(get_db)
):
    """List recent alerts."""
    query = db.query(Alert)
    if station_id:
        query = query.filter(Alert.station_id == station_id)
    if severity:
        query = query.filter(Alert.severity == severity)
    if alert_status:
        query = query.filter(Alert.status == alert_status)
    return query.order_by(desc(Alert.triggered_at)).limit(limit).all()


@router.get("/{alert_id}", response_model=AlertResponse)
def get_alert(alert_id: int, db: Session = Depends(get_db)):
    """Get a specific alert."""
    alert = db.query(Alert).filter(Alert.alert_id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


@router.patch("/{alert_id}/status", response_model=AlertResponse)
def update_alert_status(alert_id: int, update: AlertStatusUpdate, db: Session = Depends(get_db)):
    """Update alert status (acknowledge, resolve, mark false positive)."""
    from datetime import datetime, timezone
    alert = db.query(Alert).filter(Alert.alert_id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.status = update.status
    if update.summary:
        alert.summary = update.summary
    if update.status == "ACKNOWLEDGED":
        alert.acknowledged_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(alert)
    return alert


# ─── SUBSCRIPTIONS ─────────────────────────────────────────────────────────────

@router.get("/subscriptions/user/{user_id}")
def get_user_subscriptions(user_id: int, db: Session = Depends(get_db)):
    """Get all area subscriptions for a user."""
    subs = db.query(UserAreaSubscription).filter(
        UserAreaSubscription.user_id == user_id,
        UserAreaSubscription.is_active == True
    ).all()
    return subs


@router.post("/subscriptions", status_code=status.HTTP_201_CREATED)
def create_subscription(user_id: int, area_id: int, db: Session = Depends(get_db)):
    """Subscribe a user to a geographic area for alerts."""
    existing = db.query(UserAreaSubscription).filter(
        UserAreaSubscription.user_id == user_id,
        UserAreaSubscription.area_id == area_id
    ).first()
    if existing:
        if not existing.is_active:
            existing.is_active = True
            db.commit()
            return existing
        raise HTTPException(status_code=400, detail="Already subscribed to this area")
    sub = UserAreaSubscription(user_id=user_id, area_id=area_id)
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub
