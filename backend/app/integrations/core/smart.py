from __future__ import annotations

import base64
import hashlib
import secrets
from dataclasses import dataclass
from urllib.parse import urlencode, urlsplit


class SMARTValidationError(ValueError):
    pass


def _https_url(value: object, field: str, *, allow_query: bool = True) -> str:
    if not isinstance(value, str) or not value:
        raise SMARTValidationError(f"{field} must be a non-empty URL")
    parsed = urlsplit(value)
    if parsed.scheme != "https" or parsed.username or parsed.password or parsed.fragment:
        raise SMARTValidationError(f"{field} must be an HTTPS URL without credentials or fragments")
    if not parsed.netloc:
        raise SMARTValidationError(f"{field} must contain a host")
    if not allow_query and parsed.query:
        raise SMARTValidationError(f"{field} must not contain a query")
    return value


@dataclass(frozen=True)
class SMARTConfiguration:
    issuer: str
    authorization_endpoint: str
    token_endpoint: str
    jwks_uri: str | None
    scopes_supported: tuple[str, ...]
    capabilities: tuple[str, ...]

    @classmethod
    def from_document(cls, document: dict) -> "SMARTConfiguration":
        if not isinstance(document, dict):
            raise SMARTValidationError("SMART configuration must be an object")
        required = ("issuer", "authorization_endpoint", "token_endpoint")
        missing = [key for key in required if not document.get(key)]
        if missing:
            raise SMARTValidationError(f"missing SMART configuration fields: {', '.join(missing)}")
        issuer = _https_url(document["issuer"], "issuer", allow_query=False)
        authorization_endpoint = _https_url(document["authorization_endpoint"], "authorization_endpoint")
        token_endpoint = _https_url(document["token_endpoint"], "token_endpoint")
        jwks_uri = document.get("jwks_uri")
        if jwks_uri is not None:
            jwks_uri = _https_url(jwks_uri, "jwks_uri")
        scopes = document.get("scopes_supported", ())
        capabilities = document.get("capabilities", ())
        if not isinstance(scopes, (list, tuple)) or not all(isinstance(scope, str) and scope for scope in scopes):
            raise SMARTValidationError("scopes_supported must be a sequence of non-empty strings")
        if not isinstance(capabilities, (list, tuple)) or not all(isinstance(cap, str) and cap for cap in capabilities):
            raise SMARTValidationError("capabilities must be a sequence of non-empty strings")
        return cls(
            issuer,
            authorization_endpoint,
            token_endpoint,
            jwks_uri,
            tuple(dict.fromkeys(scopes)),
            tuple(dict.fromkeys(capabilities)),
        )


@dataclass(frozen=True)
class PKCEChallenge:
    verifier: str
    challenge: str
    method: str = "S256"

    def __post_init__(self) -> None:
        if self.method != "S256":
            raise SMARTValidationError("SMART authorization requires PKCE S256")


def create_pkce() -> PKCEChallenge:
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode()
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    return PKCEChallenge(verifier, challenge)


def create_oauth_state() -> str:
    return secrets.token_urlsafe(32)


def build_authorization_url(
    config: SMARTConfiguration,
    client_id: str,
    redirect_uri: str,
    scopes: list[str],
    state: str,
    pkce: PKCEChallenge,
    launch_context: dict | None = None,
    nonce: str | None = None,
) -> str:
    if not client_id or any(char.isspace() for char in client_id):
        raise SMARTValidationError("client_id is required")
    if not state:
        raise SMARTValidationError("state is required")
    _https_url(redirect_uri, "redirect_uri")
    if not isinstance(scopes, list) or not all(isinstance(scope, str) and scope for scope in scopes):
        raise SMARTValidationError("scopes must be a list of non-empty strings")

    requested_scopes = list(dict.fromkeys(scopes))
    if launch_context:
        if not isinstance(launch_context, dict):
            raise SMARTValidationError("launch_context must be an object")
        if launch_context.get("launch"):
            if "launch" not in requested_scopes:
                requested_scopes.append("launch")
        if launch_context.get("patient"):
            if "launch/patient" not in requested_scopes:
                requested_scopes.append("launch/patient")

    if "openid" in requested_scopes and not nonce:
        raise SMARTValidationError("nonce is required when openid is requested")

    allowed = set(config.scopes_supported)
    if allowed and any(scope not in allowed for scope in requested_scopes):
        raise SMARTValidationError("requested scope is not supported by discovered SMART server")

    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": " ".join(requested_scopes),
        "state": state,
        "code_challenge": pkce.challenge,
        "code_challenge_method": pkce.method,
    }
    if nonce:
        params["nonce"] = nonce
    if launch_context and launch_context.get("launch"):
        params["launch"] = str(launch_context["launch"])
    return config.authorization_endpoint + "?" + urlencode(params)


def validate_token_response(response: dict) -> dict:
    if not isinstance(response, dict) or not response.get("access_token"):
        raise SMARTValidationError("SMART token response must contain access_token")
    token_type = response.get("token_type", "Bearer")
    if not isinstance(token_type, str) or token_type.lower() != "bearer":
        raise SMARTValidationError("only Bearer token type is supported")

    expires_in = response.get("expires_in")
    if expires_in is not None and (not isinstance(expires_in, int) or isinstance(expires_in, bool) or expires_in <= 0):
        raise SMARTValidationError("expires_in must be a positive integer when supplied")

    raw_scopes = response.get("scope", "")
    scopes = tuple(dict.fromkeys(raw_scopes.split())) if isinstance(raw_scopes, str) else ()
    if response.get("scope") is not None and not isinstance(raw_scopes, str):
        raise SMARTValidationError("scope must be a space-delimited string")

    # Raw access/refresh tokens are intentionally never returned by this boundary.
    return {
        "token_type": "Bearer",
        "scope": scopes,
        "expires_in": expires_in,
        "refresh_token_present": bool(response.get("refresh_token")),
    }
