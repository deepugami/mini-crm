from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models, schemas

router = APIRouter()


@router.post("/", response_model=schemas.DealOut, status_code=status.HTTP_201_CREATED)
def create_deal(payload: schemas.DealCreate, db: Session = Depends(get_db)):
	lead = db.query(models.Lead).get(payload.lead_id)
	if not lead:
		raise HTTPException(status_code=400, detail="Invalid lead_id")
	deal = models.Deal(
		lead_id=payload.lead_id,
		title=payload.title,
		value=payload.value,
		currency=payload.currency,
	)
	db.add(deal)
	db.commit()
	db.refresh(deal)
	return deal


@router.get("/", response_model=List[schemas.DealOut])
def list_deals(db: Session = Depends(get_db)):
	return db.query(models.Deal).order_by(models.Deal.created_at.desc()).all()
