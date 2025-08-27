from __future__ import annotations
from datetime import datetime
from typing import Optional, Literal, Any
from pydantic import BaseModel, Field

from .models import LeadSource, LeadStatus, DealStage, ActivityType, TriggerType, ActionType


# Shared
class Message(BaseModel):
	message: str


# Contacts
class ContactCreate(BaseModel):
	name: str
	phone: str
	email: Optional[str] = None
	company: Optional[str] = None


class ContactUpdate(BaseModel):
	name: Optional[str] = None
	phone: Optional[str] = None
	email: Optional[str] = None
	company: Optional[str] = None


class ContactOut(BaseModel):
	id: str
	name: str
	phone: str
	email: Optional[str]
	company: Optional[str]
	created_at: datetime
	updated_at: datetime

	class Config:
		from_attributes = True


# Leads
class LeadCreate(BaseModel):
	contact_id: str
	source: LeadSource
	assigned_to: str
	notes: Optional[str] = None


class LeadUpdate(BaseModel):
	status: Optional[LeadStatus] = None
	assigned_to: Optional[str] = None


class LeadOut(BaseModel):
	id: str
	contact_id: str
	source: LeadSource
	status: LeadStatus
	assigned_to: str
	created_at: datetime
	last_touch_at: Optional[datetime]
	updated_at: datetime

	class Config:
		from_attributes = True


# Deals
class DealCreate(BaseModel):
	lead_id: str
	title: str
	value: float
	currency: str


class DealOut(BaseModel):
	id: str
	lead_id: str
	title: str
	value: float
	currency: str
	stage: DealStage
	probability: int
	created_at: datetime
	updated_at: datetime

	class Config:
		from_attributes = True


# Activity
class ActivityCreate(BaseModel):
	activity_type: ActivityType
	text: str
	created_by: str


class ActivityOut(BaseModel):
	id: int
	lead_id: str
	activity_type: ActivityType
	text: str
	created_by: str
	created_at: datetime

	class Config:
		from_attributes = True


# Automation
class AutomationRuleCreate(BaseModel):
	name: str
	trigger_type: TriggerType
	trigger_payload: Optional[dict] = None
	action_type: ActionType
	action_payload: Optional[dict] = None
	active: bool = True


class AutomationRuleOut(BaseModel):
	id: int
	name: str
	trigger_type: TriggerType
	trigger_payload: Optional[dict]
	action_type: ActionType
	action_payload: Optional[dict]
	active: bool
	created_at: datetime

	class Config:
		from_attributes = True


class WebhookLogOut(BaseModel):
	id: int
	automation_rule_id: int
	request_payload: Optional[dict]
	response_status: Optional[int]
	response_body: Optional[str]
	created_at: datetime

	class Config:
		from_attributes = True
