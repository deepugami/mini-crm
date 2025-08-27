from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models, schemas
from ..automation_engine import _execute_action as execute_action_internal

router = APIRouter()


@router.post("/rules", response_model=schemas.AutomationRuleOut, status_code=status.HTTP_201_CREATED)
def create_rule(payload: schemas.AutomationRuleCreate, db: Session = Depends(get_db)):
	rule = models.AutomationRule(
		name=payload.name,
		trigger_type=payload.trigger_type,
		trigger_payload=payload.trigger_payload,
		action_type=payload.action_type,
		action_payload=payload.action_payload,
		active=payload.active,
	)
	db.add(rule)
	db.commit()
	db.refresh(rule)
	return rule


@router.get("/rules", response_model=List[schemas.AutomationRuleOut])
def list_rules(db: Session = Depends(get_db)):
	return db.query(models.AutomationRule).order_by(models.AutomationRule.created_at.desc()).all()


@router.post("/execute/{rule_id}", response_model=schemas.Message)
def execute_rule(rule_id: int, db: Session = Depends(get_db)):
	rule = db.query(models.AutomationRule).get(rule_id)
	if not rule:
		raise HTTPException(status_code=404, detail="Rule not found")
	# Execute with empty payload for manual testing; user can supply richer payloads by design change later
	execute_action_internal(db, rule, payload={})
	return {"message": "executed"}


@router.get("/rules/{rule_id}/logs", response_model=List[schemas.WebhookLogOut])
def get_rule_logs(rule_id: int, db: Session = Depends(get_db)):
	rule = db.query(models.AutomationRule).get(rule_id)
	if not rule:
		raise HTTPException(status_code=404, detail="Rule not found")
	return (
		db.query(models.WebhookLog)
		.filter(models.WebhookLog.automation_rule_id == rule_id)
		.order_by(models.WebhookLog.created_at.desc())
		.all()
	)
