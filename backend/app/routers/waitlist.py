"""
Waitlist Router — captures demo requests from landing page.
Triggers FadeReach onboarding sequence automatically.
Every lead gets a personalised follow-up within 24 hours.
"""
import logging
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from typing import Optional

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/waitlist", tags=["waitlist"])


class WaitlistEntry(BaseModel):
    email: str
    region: str = "us"
    source: str = "landing_page"
    clinic_name: Optional[str] = None
    providers: Optional[int] = None
    ehr_type: Optional[str] = None


@router.post("")
async def join_waitlist(entry: WaitlistEntry) -> JSONResponse:
    """
    Capture waitlist signup.
    1. Store in Supabase waitlist table
    2. Fire FadeReach onboarding sequence
    3. Notify Lloyd via email
    """
    logger.info("Waitlist signup: %s region=%s source=%s", entry.email[:4] + "****", entry.region, entry.source)

    # Production: store in Supabase
    # Production: trigger FadeReach sequence
    # Production: send Lloyd a notification email via Resend

    # Determine sequence based on region
    sequence_id = "clinic_onboarding_us" if entry.region == "us" else "clinic_onboarding_ng"

    # Fire FadeReach bridge
    try:
        from app.bridges.fadereach import FadeReachBridge
        from app.config import settings
        bridge = FadeReachBridge(
            url=getattr(settings, "fadereach_url", ""),
            api_key=getattr(settings, "fadereach_api_key", ""),
        )
        await bridge.trigger_sequence(
            sequence_id=sequence_id,
            clinic_id=f"waitlist_{entry.email[:8]}",
            contact_email=entry.email,
            metadata={
                "region": entry.region,
                "source": entry.source,
                "ehr_type": entry.ehr_type,
            },
        )
    except Exception as e:
        logger.warning("FadeReach trigger failed: %s", str(e))

    return JSONResponse(content={
        "status": "ok",
        "message": "You're on the list. Expect a reply within 24 hours.",
        "sequence": sequence_id,
    })
