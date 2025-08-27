from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models, schemas
from ..automation_engine import dispatch_event

router = APIRouter()


@router.post("/", response_model=schemas.LeadOut, status_code=status.HTTP_201_CREATED)
def create_lead(payload: schemas.LeadCreate, db: Session = Depends(get_db)):
	contact = db.query(models.Contact).get(payload.contact_id)
	if not contact:
		raise HTTPException(status_code=400, detail="Invalid contact_id")
	lead = models.Lead(
		contact_id=payload.contact_id,
		source=payload.source,
		assigned_to=payload.assigned_to,
		last_touch_at=datetime.utcnow(),
	)
	db.add(lead)
	db.commit()
	db.refresh(lead)
	# Dispatch automation: on_create lead
	dispatch_event(db, event="create", entity="lead", payload={
		"lead_id": lead.id,
		"contact_id": lead.contact_id,
		"status": lead.status.value,
	})
	# Optional note
	if payload.notes:
		activity = models.ActivityLog(
			lead_id=lead.id,
			activity_type=models.ActivityType.note,
			text=payload.notes,
			created_by=payload.assigned_to,
		)
		db.add(activity)
		db.commit()
	return lead


@router.get("/", response_model=List[schemas.LeadOut])
def list_leads(status: Optional[models.LeadStatus] = Query(default=None), db: Session = Depends(get_db)):
	q = db.query(models.Lead)
	if status is not None:
		q = q.filter(models.Lead.status == status)
	return q.order_by(models.Lead.created_at.desc()).all()


@router.patch("/{lead_id}", response_model=schemas.LeadOut)
def update_lead(lead_id: str, payload: schemas.LeadUpdate, db: Session = Depends(get_db)):
	lead = db.query(models.Lead).get(lead_id)
	if not lead:
		raise HTTPException(status_code=404, detail="Lead not found")
	old_status = lead.status
	for field, value in payload.model_dump(exclude_unset=True).items():
		setattr(lead, field, value)
	lead.updated_at = datetime.utcnow()
	db.commit()
	db.refresh(lead)
	if payload.status is not None and payload.status != old_status:
		# Dispatch automation: status change
		dispatch_event(db, event="status_change", entity="lead", payload={
			"lead_id": lead.id,
			"status": lead.status.value,
		})
	return lead


@router.post("/{lead_id}/activity", response_model=schemas.ActivityOut, status_code=status.HTTP_201_CREATED)
def create_activity(lead_id: str, payload: schemas.ActivityCreate, db: Session = Depends(get_db)):
	lead = db.query(models.Lead).get(lead_id)
	if not lead:
		raise HTTPException(status_code=404, detail="Lead not found")
	activity = models.ActivityLog(
		lead_id=lead_id,
		activity_type=payload.activity_type,
		text=payload.text,
		created_by=payload.created_by,
	)
	db.add(activity)
	lead.last_touch_at = datetime.utcnow()
	db.commit()
	db.refresh(activity)
	return activity


@router.get("/{lead_id}/activity", response_model=List[schemas.ActivityOut])
def list_activities(lead_id: str, db: Session = Depends(get_db)):
	lead = db.query(models.Lead).get(lead_id)
	if not lead:
		raise HTTPException(status_code=404, detail="Lead not found")
	return (
		db.query(models.ActivityLog)
		.filter(models.ActivityLog.lead_id == lead_id)
		.order_by(models.ActivityLog.created_at.desc())
		.all()
	)
