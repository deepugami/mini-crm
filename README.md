# Mini CRM (FastAPI + SQLite)

A small, production-style CRM backend storing contacts, leads and deals, with automation rules (webhooks, scheduled follow-ups, status transitions). Includes REST endpoints and OpenAPI docs.

## Quickstart (local)

1. Create venv and install deps:

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

2. Run API:

```bash
uvicorn app.main:app --reload
```

3. Open docs: http://localhost:8000/docs

Auth: Use bearer token `demo-token` for protected routes. Obtain via `POST /auth/token` (demo returns static token).

## Docker

```bash
docker build -t mini-crm .
docker run -p 8000:8000 mini-crm
# or
docker compose up --build
```

## Sample requests

- POST /auth/token → returns `{ token: "demo-token" }`
- POST /contacts
```json
{ "name":"Riya Singh","phone":"9123456789","email":"riya@example.com","company":"Riya's Store" }
```
- POST /leads
```json
{ "contact_id":"<uuid>", "source":"organic", "assigned_to":"me", "notes":"Walk-in - interested in WhatsApp commerce" }
```
- GET /leads?status=new
- PATCH /leads/{lead_id} → { "status": "contacted" }
- POST /deals
```json
{ "lead_id":"<uuid>", "title":"Pilot - Store A", "value":25000, "currency":"INR" }
```
- POST /leads/{lead_id}/activity

## Automation rules

- POST /automation/rules
```json
{
  "name":"NotifyWebhookOnNewLead",
  "trigger_type":"on_create",
  "trigger_payload":{"entity":"lead"},
  "action_type":"webhook",
  "action_payload":{"url":"https://webhook.site/<id>", "method":"POST"},
  "active":true
}
```
- POST /automation/execute/{rule_id} (manual trigger)
- GET /automation/rules/{id}/logs

## Scheduler

APScheduler runs every minute to evaluate `time_wait` rules, e.g. reminders after 24h of no touch.

## Notes

- SQLite file: `crm.db` in project root. Set `DATABASE_URL` to override.
- For demo only. Not production-hardened (no migrations, RBAC, rate limits, etc.).
