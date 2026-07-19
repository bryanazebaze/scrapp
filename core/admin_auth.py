"""Admin authentication: bcrypt password hashing, HS256 JWT issuance, and a
FastAPI ``require_admin`` dependency.

Separate from ``core/auth.py`` (which verifies Firebase ID tokens for
end-users): admin login is email/username + password, and the JWT is
issued by us (HS256 with ``settings.jwt_secret``). AdminUser is a separate
table from User, so admin tokens and user tokens are distinguishable by
the ``scope`` claim (``"admin"`` vs ``"user"``).

Seeding: ``seed_admins_if_empty(db)`` inserts two superadmin rows on first
startup if the table is empty. Called from ``lifespan`` after
``start_scheduler()``. Idempotent.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import Depends, Header, HTTPException
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from .models import AdminUser

logger = logging.getLogger(__name__)

# bcrypt context — used for both hashing and verification.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# --------------------------------------------------------------------------- #
# Password helpers
# --------------------------------------------------------------------------- #
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return pwd_context.verify(plain, hashed)
    except Exception:
        return False


# --------------------------------------------------------------------------- #
# JWT
# --------------------------------------------------------------------------- #
def create_access_token(sub: str, scope: str = "admin") -> str:
    """Issue an HS256 JWT for ``sub`` (admin identifier or user email).

    ``scope`` distinguishes admin vs user tokens. Expires after
    ``settings.jwt_expire_minutes``.
    """
    now = datetime.now(timezone.utc)
    payload = {
        "sub": sub,
        "scope": scope,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.jwt_expire_minutes)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def _decode_admin_token(token: str) -> dict:
    try:
        return jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token admin expiré")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token admin invalide")


# --------------------------------------------------------------------------- #
# Admin lookup
# --------------------------------------------------------------------------- #
def authenticate_admin(db: Session, identifier: str, password: str) -> Optional[AdminUser]:
    """Find an admin by lowercased email OR username, then verify the password.

    Returns the AdminUser row on success, None on any failure (so the caller
    can raise a uniform 401 without leaking which check failed).
    """
    ident = (identifier or "").strip().lower()
    if not ident:
        return None
    admin = (
        db.query(AdminUser)
        .filter(
            (AdminUser.email == ident) | (AdminUser.username == ident)
        )
        .first()
    )
    if admin is None or not admin.is_active or not admin.password_hash:
        return None
    if not verify_password(password, admin.password_hash):
        return None
    return admin


# --------------------------------------------------------------------------- #
# FastAPI dependency
# --------------------------------------------------------------------------- #
def require_admin(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> AdminUser:
    """Protect admin endpoints. Verifies the Bearer JWT and loads the AdminUser.

    Raises 401 on any failure (missing header, bad format, invalid/expired
    token, subject not found in admin_users, wrong scope, inactive admin).
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="En-tête d'autorisation manquant")
    parts = authorization.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Format d'autorisation invalide")
    token = parts[1]

    claims = _decode_admin_token(token)
    if claims.get("scope") != "admin":
        raise HTTPException(status_code=401, detail="Token admin invalide")
    sub = claims.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Token admin invalide")

    ident = sub.lower()
    admin = (
        db.query(AdminUser)
        .filter(
            (AdminUser.email == ident) | (AdminUser.username == ident)
        )
        .first()
    )
    if admin is None or not admin.is_active:
        raise HTTPException(status_code=401, detail="Token admin invalide")
    return admin


# --------------------------------------------------------------------------- #
# Seeding
# --------------------------------------------------------------------------- #
def seed_admins_if_empty(db: Session) -> None:
    """Insert the two default superadmins if the admin_users table is empty.

    Idempotent — a no-op if any admin row already exists. Called from the
    FastAPI lifespan startup after ``start_scheduler()``.
    """
    try:
        count = db.query(AdminUser).count()
        if count > 0:
            return
        pw_hash = hash_password(settings.admin_seed_password)
        db.add_all([
            AdminUser(
                username="aurel",
                email="azebazeaurel@gmail.com",
                password_hash=pw_hash,
                is_active=True,
                is_superadmin=True,
            ),
            AdminUser(
                username="kelcyazef",
                email=None,
                password_hash=pw_hash,
                is_active=True,
                is_superadmin=True,
            ),
        ])
        db.commit()
        logger.info("Seeded 2 default admin accounts (aurel, kelcyazef)")
    except Exception:
        db.rollback()
        logger.exception("Failed to seed admin accounts")