"""HEZQARA AI — FastAPI application entry point."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import (
    agents,
    analytics,
    appointments,
    billing,
    calls,
    health,
    insurance,
    patients,
    prior_auth,
    recalls,
    referrals,
    standalone,
    voice,
    waitlist,
    whatsapp,
)

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("HEZQARA AI starting on port %s", settings.app_port)
    yield
    logger.info("HEZQARA AI shutting down")


app = FastAPI(
    title="HEZQARA AI",
    description="AI healthcare front-office and administrative automation platform",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.app_env != "production" else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://hezqara.tinlance.com",
        "https://hezqara.ai",
        "http://localhost:3004",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)

for router_module in (
    health,
    voice,
    billing,
    whatsapp,
    agents,
    appointments,
    patients,
    calls,
    insurance,
    prior_auth,
    recalls,
    referrals,
    analytics,
    waitlist,
    standalone,
):
    app.include_router(router_module.router)
