"""Firebase ID-token verification using PyJWT + Google's public x509 certs.

No firebase-admin SDK required — we verify the JWT with Google's rotated
public keys and check aud/iss manually.  This is the FIRST authenticated
router pattern in the codebase; future authenticated routers should follow
the same ``Depends(get_current_user)`` convention.

Verification flow:
  1. Extract ``Bearer <token>`` from the Authorization header.
  2. Decode the JWT header (unverified) to read ``kid``.
  3. Look up the matching x509 cert in Google's public set (cached 1 h).
  4. ``jwt.decode(...)`` with RS256, audience ``centralimo-71b0d``,
     issuer ``https://securetoken.google.com/centralimo-71b0d``.
  5. Return ``{uid, email, email_verified}``.

On any failure raise ``HTTPException(401, "Token d'authentification invalide")``.
"""
from __future__ import annotations

import time
import logging
from typing import Any, Optional

import jwt
import requests
from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from .database import get_db

logger = logging.getLogger(__name__)

# --- Firebase project constants -------------------------------------------------
FIREBASE_PROJECT_ID = "centralimo-71b0d"
FIREBASE_ISSUER = f"https://securetoken.google.com/{FIREBASE_PROJECT_ID}"
GOOGLE_CERTS_URL = (
    "https://www.googleapis.com/robot/v1/metadata/x509/"
    "securetoken@system.gserviceaccount.com"
)
_CERTS_TTL = 3600  # seconds (1 hour)

# Module-level cert cache --------------------------------------------------------
_certs_cache: dict[str, str] | None = None
_certs_fetched_at: float = 0.0


def _fetch_google_certs() -> dict[str, str]:
    """Fetch Google's public x509 certs and cache them for ``_CERTS_TTL`` seconds."""
    global _certs_cache, _certs_fetched_at
    now = time.monotonic()
    if _certs_cache is not None and (now - _certs_fetched_at) < _CERTS_TTL:
        return _certs_cache
    try:
        resp = requests.get(GOOGLE_CERTS_URL, timeout=10)
        resp.raise_for_status()
        _certs_cache = resp.json()
        _certs_fetched_at = now
        return _certs_cache
    except Exception as exc:
        logger.warning("Failed to fetch Google x509 certs: %s", exc)
        # Return stale cache if we have one; otherwise re-raise (-> 401)
        if _certs_cache is not None:
            return _certs_cache
        raise


def _verify_firebase_token(token: str) -> dict[str, Any]:
    """Verify a Firebase ID token and return the decoded claims.

    Raises ``HTTPException(401)`` on any failure.
    """
    # 1. Read the JWT header to get the key id
    try:
        unverified_header = jwt.get_unverified_header(token)
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token d'authentification invalide")

    kid = unverified_header.get("kid")
    if not kid:
        raise HTTPException(status_code=401, detail="Token d'authentification invalide")

    certs = _fetch_google_certs()
    public_key_pem = certs.get(kid)
    if public_key_pem is None:
        # Maybe the cache is stale — try a forced refresh once
        global _certs_cache, _certs_fetched_at
        _certs_cache = None
        _certs_fetched_at = 0.0
        try:
            certs = _fetch_google_certs()
        except Exception:
            raise HTTPException(status_code=401, detail="Token d'authentification invalide")
        public_key_pem = certs.get(kid)
        if public_key_pem is None:
            raise HTTPException(status_code=401, detail="Token d'authentification invalide")

    try:
        claims = jwt.decode(
            token,
            public_key_pem,
            algorithms=["RS256"],
            audience=FIREBASE_PROJECT_ID,
            issuer=FIREBASE_ISSUER,
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expiré")
    except jwt.InvalidAudienceError:
        raise HTTPException(status_code=401, detail="Token d'authentification invalide")
    except jwt.InvalidIssuerError:
        raise HTTPException(status_code=401, detail="Token d'authentification invalide")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token d'authentification invalide")

    return claims


def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """FastAPI dependency that verifies the Firebase ID token in the
    ``Authorization: Bearer <token>`` header.

    Returns ``{"uid": str, "email": str | None, "email_verified": bool}``.
    Raises 401 on any verification failure.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="En-tête d'autorisation manquant")
    parts = authorization.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Format d'autorisation invalide")
    token = parts[1]

    claims = _verify_firebase_token(token)
    return {
        "uid": claims["sub"],
        "email": claims.get("email"),
        "email_verified": claims.get("email_verified", False),
    }


def require_verified_email(
    user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    """Dependency that additionally requires ``email_verified == True``.

    Use on payment-initiation endpoints so we don't let unverified emails pay.
    """
    if not user.get("email_verified"):
        raise HTTPException(
            status_code=403,
            detail="Adresse e-mail non vérifiée. Veuillez vérifier votre e-mail avant de continuer.",
        )
    return user