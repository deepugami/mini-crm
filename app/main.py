from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine, get_db, SessionLocal
from . import models
from .auth import issue_token, get_current_user
from .automation_engine import start_scheduler

from .routers import contacts, leads, deals, automation, health

app = FastAPI(title="Mini CRM", version="0.1.0")

app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=True,
	allow_methods=["*"]
	,
	allow_headers=["*"],
)

# Create tables
Base.metadata.create_all(bind=engine)

# Start scheduler
start_scheduler(lambda: SessionLocal())

# Root
@app.get("/")
async def root():
	return {"message": "Mini CRM API", "docs": "/docs", "health": "/health"}

# Auth endpoints
@app.post("/auth/token")
async def auth_token(resp = Depends(issue_token)):
	return resp

# Routers (protected)
app.include_router(health.router, tags=["health"])
app.include_router(contacts.router, prefix="/contacts", tags=["contacts"], dependencies=[Depends(get_current_user)])
app.include_router(leads.router, prefix="/leads", tags=["leads"], dependencies=[Depends(get_current_user)])
app.include_router(deals.router, prefix="/deals", tags=["deals"], dependencies=[Depends(get_current_user)])
app.include_router(automation.router, prefix="/automation", tags=["automation"], dependencies=[Depends(get_current_user)])
