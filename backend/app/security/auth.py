"""Clerk authentication and organization authorization for the API."""
from typing import Any

from clerk_backend_api import AuthenticateRequestOptions, authenticate_request
from fastapi import Depends, HTTPException, Request

from app.config import settings


PUBLIC_PATHS = {
    "/",
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/voice/webhook",
    "/whatsapp/webhook",
    "/billing/webhook",
    "/webhooks/clerk",
}


def _is_public_path(path: str) -> bool:
    return path in PUBLIC_PATHS or path.startswith("/docs/")


def authenticate(request: Request) -> Any:
    """Validate a Clerk session token and return its RequestState."""
    if settings.app_env in {"test", "development"} and request.headers.get("x-test-auth") == "1":
        return {"payload": {"sub": "test_user", "org_id": "test_clinic", "org_role": "admin"}, "is_signed_in": True}

    if not settings.clerk_secret_key:
        raise HTTPException(status_code=503, detail="Authentication is not configured")

    state = authenticate_request(
        request,
        AuthenticateRequestOptions(
            secret_key=settings.clerk_secret_key,
            jwt_key=settings.clerk_jwt_key or None,
            authorized_parties=settings.clerk_authorized_parties_list or None,
            accepts_token=["session_token"],
        ),
    )
    if not state.is_signed_in:
        reason = getattr(getattr(state, "reason", None), "name", None) or "unauthorized"
        raise HTTPException(status_code=401, detail=reason, headers={"WWW-Authenticate": "Bearer"})
    return state


def require_auth(request: Request) -> Any:
    return authenticate(request)


def get_current_user(state: Any = Depends(require_auth)) -> str:
    payload = state.get("payload", {}) if isinstance(state, dict) else state.payload
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="missing user identity")
    return user_id


def get_clinic_id(state: Any = Depends(require_auth)) -> str:
    payload = state.get("payload", {}) if isinstance(state, dict) else state.payload
    clinic_id = payload.get("org_id") or payload.get("organization_id")
    if not clinic_id:
        raise HTTPException(status_code=403, detail="organization context required")
    return clinic_id


def require_permission(permission: str):
    def _check(state: Any = Depends(require_auth)) -> Any:
        payload = state.get("payload", {}) if isinstance(state, dict) else state.payload
        permissions = payload.get("org_permissions") or []
        if permission not in permissions:
            raise HTTPException(status_code=403, detail=f"missing permission: {permission}")
        return state

    return _check
