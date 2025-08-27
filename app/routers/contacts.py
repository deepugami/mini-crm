from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models, schemas

router = APIRouter()


@router.post("/", response_model=schemas.ContactOut, status_code=status.HTTP_201_CREATED)
def create_contact(contact: schemas.ContactCreate, db: Session = Depends(get_db)):
	obj = models.Contact(
		name=contact.name,
		phone=contact.phone,
		email=contact.email,
		company=contact.company,
	)
	db.add(obj)
	db.commit()
	db.refresh(obj)
	return obj


@router.get("/", response_model=List[schemas.ContactOut])
def list_contacts(db: Session = Depends(get_db)):
	return db.query(models.Contact).order_by(models.Contact.created_at.desc()).all()


@router.get("/{contact_id}", response_model=schemas.ContactOut)
def get_contact(contact_id: str, db: Session = Depends(get_db)):
	obj = db.query(models.Contact).get(contact_id)
	if not obj:
		raise HTTPException(status_code=404, detail="Contact not found")
	return obj


@router.patch("/{contact_id}", response_model=schemas.ContactOut)
def update_contact(contact_id: str, payload: schemas.ContactUpdate, db: Session = Depends(get_db)):
	obj = db.query(models.Contact).get(contact_id)
	if not obj:
		raise HTTPException(status_code=404, detail="Contact not found")
	for field, value in payload.model_dump(exclude_unset=True).items():
		setattr(obj, field, value)
	db.commit()
	db.refresh(obj)
	return obj


@router.delete("/{contact_id}", response_model=schemas.Message)
def delete_contact(contact_id: str, db: Session = Depends(get_db)):
	obj = db.query(models.Contact).get(contact_id)
	if not obj:
		raise HTTPException(status_code=404, detail="Contact not found")
	db.delete(obj)
	db.commit()
	return {"message": "deleted"}
