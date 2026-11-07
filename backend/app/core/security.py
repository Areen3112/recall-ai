from typing import Any, Literal
from datetime import datetime, timezone
from uuid import UUID

import jwt
from fastapi import HTTPException, status
from pydantic import BaseModel

from app.core.config import Settings


class VerifiedIdentity(BaseModel):
    workspace_id: str
    identity_type: Literal["customer", "visitor"]
    subject_id: str


def _decode_identity_token(token: str | None, settings: Settings) -> dict[str, Any]:
    if (
        not token
        or not settings.identity_token_secret
        or not settings.identity_token_issuer
        or not settings.identity_token_audience
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid identity credentials")
    try:
        claims = jwt.decode(
            token,
            settings.identity_token_secret.get_secret_value(),
            algorithms=["HS256"],
            issuer=settings.identity_token_issuer,
            audience=settings.identity_token_audience,
            options={"require": ["exp", "iat", "iss", "aud", "workspace_id", "identity_type"]},
        )
        issued_at = claims.get("iat")
        expires_at = claims.get("exp")
        if not isinstance(issued_at, (int, float)) or not isinstance(expires_at, (int, float)):
            raise jwt.InvalidTokenError()
        lifetime = expires_at - issued_at
        if lifetime <= 0 or lifetime > settings.identity_token_max_ttl_seconds:
            raise jwt.InvalidTokenError()
        if issued_at > datetime.now(timezone.utc).timestamp() + 5:
            raise jwt.InvalidTokenError()
        return claims
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid identity credentials") from exc


def _canonical_uuid(value: str | None) -> str | None:
    if not isinstance(value, str):
        return None
    try:
        return str(UUID(value))
    except (ValueError, AttributeError):
        return None


def verify_identity_token(
    token: str | None,
    *,
    workspace_id: str,
    expected_customer_id: str | None,
    settings: Settings,
) -> VerifiedIdentity:
    """Verify an issuer-signed registered-customer token; visitor tokens are rejected.

    Customer token claims: iss, aud, iat, exp, workspace_id, identity_type="customer", customer_id;
    lifetime is bounded by IDENTITY_TOKEN_MAX_TTL_SECONDS.
    The trusted business identity issuer must authenticate the end user, resolve the
    customer inside that workspace, require customers.identity_verified=true, and
    issue a short-lived token only after that check. Browser input is never proof.
    The browser-supplied customer ID is only accepted when it matches the signed UUID.
    """
    claims = _decode_identity_token(token, settings)
    token_workspace = claims.get("workspace_id")
    customer_id = _canonical_uuid(claims.get("customer_id"))
    expected_id = _canonical_uuid(expected_customer_id)
    if (
        claims.get("identity_type") != "customer"
        or "visitor_id" in claims
        or not isinstance(token_workspace, str)
        or token_workspace != workspace_id
        or customer_id is None
        or expected_id is None
        or customer_id != expected_id
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid identity credentials")
    return VerifiedIdentity(workspace_id=token_workspace, identity_type="customer", subject_id=customer_id)


def verify_visitor_token(
    token: str | None,
    *,
    workspace_id: str,
    expected_visitor_id: str | None,
    settings: Settings,
) -> VerifiedIdentity:
    """Verify a server-issued anonymous token, which can never identify a customer.

    Visitor token claims: exp, workspace_id, identity_type="visitor", visitor_id.
    A trusted backend issuer creates an opaque UUID and short-lived token with iat, exp,
    workspace_id, identity_type="visitor", visitor_id; customer_id must be absent.
    Visitor claims may only be issued by the dedicated anonymous visitor flow and can
    never be upgraded or exchanged for a registered-customer identity.
    """
    claims = _decode_identity_token(token, settings)
    token_workspace = claims.get("workspace_id")
    visitor_id = _canonical_uuid(claims.get("visitor_id"))
    expected_id = _canonical_uuid(expected_visitor_id)
    if (
        claims.get("identity_type") != "visitor"
        or "customer_id" in claims
        or not isinstance(token_workspace, str)
        or token_workspace != workspace_id
        or visitor_id is None
        or expected_id is None
        or visitor_id != expected_id
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid identity credentials")
    return VerifiedIdentity(workspace_id=token_workspace, identity_type="visitor", subject_id=visitor_id)
