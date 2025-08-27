from __future__ import annotations
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Callable
import json

import httpx
from sqlalchemy.orm import Session

from .models import (
	AutomationRule,
	WebhookLog,
	TriggerType,
	ActionType,
	Lead,
	LeadStatus,
	ActivityLog,
	ActivityType,
	Deal,
)


def dispatch_event(db: Session, event: str, entity: str, payload: Dict[str, Any]) -> None:
	"""Dispatch an internal event to evaluate and execute matching automation rules."""
	rules = db.query(AutomationRule).filter(AutomationRule.active == True).all()
	for rule in rules:
		if not _rule_matches_event(rule, event, entity, payload):
			continue
		_execute_action(db, rule, payload)


def _rule_matches_event(rule: AutomationRule, event: str, entity: str, payload: Dict[str, Any]) -> bool:
	if rule.trigger_type == TriggerType.on_create:
		config = rule.trigger_payload or {}
		return event == "create" and config.get("entity") == entity
	if rule.trigger_type == TriggerType.on_stage_change:
		config = rule.trigger_payload or {}
		# For leads, consider status change
		if entity == "lead" and event == "status_change":
			expected_status = config.get("status")
			return expected_status is None or payload.get("status") == expected_status
		return False
	# time_wait rules are handled by scheduler, not here
	return False


def _execute_action(db: Session, rule: AutomationRule, payload: Dict[str, Any]) -> None:
	if rule.action_type == ActionType.webhook:
		_do_webhook(db, rule, payload)
	elif rule.action_type == ActionType.create_activity:
		_create_activity(db, rule, payload)
	elif rule.action_type == ActionType.update_status:
		_update_status(db, rule, payload)
	elif rule.action_type == ActionType.create_deal:
		_create_deal(db, rule, payload)
	elif rule.action_type == ActionType.email:
		# Mock email: record as webhook log text
		_log_webhook(db, rule, request=payload, status_code=200, response_body="EMAIL_SENT")
	else:
		pass


def _do_webhook(db: Session, rule: AutomationRule, payload: Dict[str, Any]) -> None:
	conf = rule.action_payload or {}
	url = conf.get("url")
	method = (conf.get("method") or "POST").upper()
	if not url:
		return
	try:
		with httpx.Client(timeout=5.0) as client:
			resp = client.request(method, url, json=payload)
			_log_webhook(db, rule, request=payload, status_code=resp.status_code, response_body=resp.text)
	except Exception as exc:
		_log_webhook(db, rule, request=payload, status_code=0, response_body=str(exc))


def _log_webhook(db: Session, rule: AutomationRule, request: Optional[Dict[str, Any]], status_code: Optional[int], response_body: Optional[str]) -> None:
	log = WebhookLog(
		automation_rule_id=rule.id,
		request_payload=request,
		response_status=status_code,
		response_body=response_body,
		created_at=datetime.utcnow(),
	)
	db.add(log)
	db.commit()


def _create_activity(db: Session, rule: AutomationRule, payload: Dict[str, Any]) -> None:
	conf = rule.action_payload or {}
	lead_id = payload.get("lead_id") or conf.get("lead_id")
	if not lead_id:
		return
	text = conf.get("text") or "Automation note"
	created_by = conf.get("created_by") or "automation"
	activity = ActivityLog(
		lead_id=lead_id,
		activity_type=ActivityType.note,
		text=text,
		created_by=created_by,
		created_at=datetime.utcnow(),
	)
	db.add(activity)
	# update last_touch_at
	lead = db.query(Lead).get(lead_id)
	if lead:
		lead.last_touch_at = datetime.utcnow()
	db.commit()


def _update_status(db: Session, rule: AutomationRule, payload: Dict[str, Any]) -> None:
	conf = rule.action_payload or {}
	lead_id = payload.get("lead_id") or conf.get("lead_id")
	status_value = conf.get("status") or payload.get("status")
	if not lead_id or not status_value:
		return
	lead = db.query(Lead).get(lead_id)
	if not lead:
		return
	try:
		lead.status = LeadStatus(status_value)
	except Exception:
		return
	lead.updated_at = datetime.utcnow()
	db.commit()


def _create_deal(db: Session, rule: AutomationRule, payload: Dict[str, Any]) -> None:
	conf = rule.action_payload or {}
	lead_id = payload.get("lead_id") or conf.get("lead_id")
	title = conf.get("title") or "New Deal"
	value = float(conf.get("value") or 0)
	currency = conf.get("currency") or "USD"
	if not lead_id:
		return
	deal = Deal(
		lead_id=lead_id,
		title=title,
		value=value,
		currency=currency,
	)
	db.add(deal)
	db.commit()


# Scheduler support for time_wait rules
from apscheduler.schedulers.background import BackgroundScheduler

_scheduler: Optional[BackgroundScheduler] = None


def start_scheduler(open_session: Callable[[], Session]) -> None:
	global _scheduler
	if _scheduler:
		return
	_scheduler = BackgroundScheduler(timezone="UTC")
	_scheduler.add_job(lambda: _run_time_wait_rules(open_session), "interval", minutes=1, id="time_wait_scan", replace_existing=True)
	_scheduler.start()


def _run_time_wait_rules(open_session: Callable[[], Session]) -> None:
	from .models import AutomationRule
	with open_session() as db:
		rules = db.query(AutomationRule).filter(AutomationRule.active == True, AutomationRule.trigger_type == TriggerType.time_wait).all()
		for rule in rules:
			_try_run_time_wait_rule(db, rule)


def _try_run_time_wait_rule(db: Session, rule: AutomationRule) -> None:
	conf = rule.trigger_payload or {}
	entity = conf.get("entity") or "lead"
	if entity != "lead":
		return
	status_filter = conf.get("status")
	hours_without_touch = conf.get("hours_without_touch") or 24
	threshold = datetime.utcnow() - timedelta(hours=hours_without_touch)

	q = db.query(Lead)
	if status_filter:
		try:
			q = q.filter(Lead.status == LeadStatus(status_filter))
		except Exception:
			return
	q = q.filter((Lead.last_touch_at == None) | (Lead.last_touch_at < threshold))

	for lead in q.all():
		payload = {"lead_id": lead.id, "status": lead.status.value}
		_execute_action(db, rule, payload)
