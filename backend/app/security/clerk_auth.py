"""
Clerk Auth — JWT token verification and claim extraction.
Multi-tenant: every request must have an org_id (clinic_id).
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def verify_clerk_token(token: str) -> dict:
    """
    Verify Clerk JWT token.
    In production, uses Clerk SDK to verify signature.
    Returns decoded claims dict.
    """
    # Production: use clerk_backend_api to verify
    # For now: placeholder structure
    return {}


def extract_clinic_id(claims: dict) -> str:
    """
    Extract clinic_id from Clerk JWT claims.
    clinic_id = Clerk Organisation ID (org_id).
    Personal tokens (no org_id) are rejected.
    """
    org_id = claims.get("org_id")
    if not org_id:
        raise ValueError("org_id missing from token claims — personal tokens not permitted")
    return org_id


def extract_user_role(claims: dict) -> str:
    """Extract user role from Clerk claims for RBAC."""
    return claims.get("org_role", "member")
