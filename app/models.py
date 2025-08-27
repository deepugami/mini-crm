import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
	Boolean,
	CheckConstraint,
	Column,
	DateTime,
	Enum,
	Float,
	ForeignKey,
	Integer,
	JSON,
	String,
	Text,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column

from .database import Base


class LeadSource(str, enum.Enum):
	organic = "organic"
	ad = "ad"
	referral = "referral"
	manual = "manual"


class LeadStatus(str, enum.Enum):
	new = "new"
	contacted = "contacted"
	qualified = "qualified"
	unqualified = "unqualified"


class DealStage(str, enum.Enum):
	new = "new"
	demo = "demo"
	proposal = "proposal"
	won = "won"
	lost = "lost"


class ActivityType(str, enum.Enum):
	call = "call"
	message = "message"
	note = "note"


class TriggerType(str, enum.Enum):
	on_create = "on_create"
	on_stage_change = "on_stage_change"
	time_wait = "time_wait"


class ActionType(str, enum.Enum):
	webhook = "webhook"
	create_activity = "create_activity"
	update_status = "update_status"
	create_deal = "create_deal"
	email = "email"


def generate_uuid_str() -> str:
	return str(uuid.uuid4())


class Contact(Base):
	__tablename__ = "contacts"

	id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid_str)
	name: Mapped[str] = mapped_column(String, nullable=False)
	phone: Mapped[str] = mapped_column(String, nullable=False)
	email: Mapped[Optional[str]] = mapped_column(String, nullable=True)
	company: Mapped[Optional[str]] = mapped_column(String, nullable=True)
	created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
	updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

	leads = relationship("Lead", back_populates="contact", cascade="all, delete-orphan")


class Lead(Base):
	__tablename__ = "leads"

	id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid_str)
	contact_id: Mapped[str] = mapped_column(String, ForeignKey("contacts.id"), nullable=False)
	source: Mapped[LeadSource] = mapped_column(Enum(LeadSource), nullable=False)
	status: Mapped[LeadStatus] = mapped_column(Enum(LeadStatus), default=LeadStatus.new, nullable=False)
	assigned_to: Mapped[str] = mapped_column(String, nullable=False)
	created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
	last_touch_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
	updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

	contact = relationship("Contact", back_populates="leads")
	deals = relationship("Deal", back_populates="lead", cascade="all, delete-orphan")
	activities = relationship("ActivityLog", back_populates="lead", cascade="all, delete-orphan")


class Deal(Base):
	__tablename__ = "deals"

	id: Mapped[str] = mapped_column(String, primary_key=True, default=generate_uuid_str)
	lead_id: Mapped[str] = mapped_column(String, ForeignKey("leads.id"), nullable=False)
	title: Mapped[str] = mapped_column(String, nullable=False)
	value: Mapped[float] = mapped_column(Float, nullable=False)
	currency: Mapped[str] = mapped_column(String, nullable=False)
	stage: Mapped[DealStage] = mapped_column(Enum(DealStage), default=DealStage.new, nullable=False)
	probability: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
	created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
	updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

	lead = relationship("Lead", back_populates="deals")

	__table_args__ = (
		CheckConstraint("probability >= 0 AND probability <= 100", name="probability_range"),
	)


class ActivityLog(Base):
	__tablename__ = "activity_logs"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
	lead_id: Mapped[str] = mapped_column(String, ForeignKey("leads.id"), nullable=False)
	activity_type: Mapped[ActivityType] = mapped_column(Enum(ActivityType), nullable=False)
	text: Mapped[str] = mapped_column(Text, nullable=False)
	created_by: Mapped[str] = mapped_column(String, nullable=False)
	created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

	lead = relationship("Lead", back_populates="activities")


class AutomationRule(Base):
	__tablename__ = "automation_rules"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
	name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
	trigger_type: Mapped[TriggerType] = mapped_column(Enum(TriggerType), nullable=False)
	trigger_payload: Mapped[dict] = mapped_column(JSON, nullable=True)
	action_type: Mapped[ActionType] = mapped_column(Enum(ActionType), nullable=False)
	action_payload: Mapped[dict] = mapped_column(JSON, nullable=True)
	active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
	created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

	webhook_logs = relationship("WebhookLog", back_populates="rule", cascade="all, delete-orphan")


class WebhookLog(Base):
	__tablename__ = "webhook_logs"

	id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
	automation_rule_id: Mapped[int] = mapped_column(Integer, ForeignKey("automation_rules.id"), nullable=False)
	request_payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
	response_status: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
	response_body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
	created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

	rule = relationship("AutomationRule", back_populates="webhook_logs")
