"""
Carenova AI — FastAPI Application Entry Point.
Port 8004 on EC2 Stockholm (13.50.16.19).
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import (
    voice, health, billing, whatsapp,
    agents, appointments, patients, calls,
    insurance, prior_auth, recalls, referrals, analytics, waitlist,
)

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Carenova AI starting on port %s", settings.app_port)
    yield
    logger.info("Carenova AI shutting down")


app = FastAPI(
    title="Carenova AI",
    description="AI Medical Front Office Platform",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.app_env != "production" else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://carenova.tinlance.com",
        "https://carenova.ai",
        "http://localhost:3004",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register all routers ───────────────────────────────────────────────────────
app.include_router(health.router)
app.include_router(voice.router)
app.include_router(billing.router)
app.include_router(whatsapp.router)
app.include_router(agents.router)
app.include_router(appointments.router)
app.include_router(patients.router)
app.include_router(calls.router)
app.include_router(insurance.router)
app.include_router(prior_auth.router)
app.include_router(recalls.router)
app.include_router(referrals.router)
app.include_router(analytics.router)
app.include_router(waitlist.router, prefix="/api")
