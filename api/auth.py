"""End-user authentication: email/password register and login.

Google sign-in stays on the Firebase path (core/auth.py verifies the ID
token). This router handles the email/password path the Flutter app now
offers alongside the Google button.

Tokens issued here are HS256 JWTs signed with ``settings.jwt_secret`` and
carry ``scope="user"``. They are distinct from admin tokens
(``scope="admin"``, issued by api/admin_auth.py) and from Firebase ID
tokens (verified by core/auth.py:get_current_user).
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.admin_auth import create_access_token, hash_password, verify_password
from core.config import settings
from core.database import get_db
from core.models import User
from core.schemas import (
    UserLoginSchema,
    UserOutSchema,
    UserRegisterSchema,
    UserTokenSchema,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserTokenSchema)
def register(body: UserRegisterSchema, db: Session = Depends(get_db)) -> UserTokenSchema:
    """Create a new email/password user and return a JWT."""
    email = body.email.strip().lower()
    if not email or not body.password or len(body.password) < 8:
        raise HTTPException(status_code=400, detail="Données invalides")
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Cet e-mail est déjà enregistré")
    user = User(
        email=email,
        password_hash=hash_password(body.password),
        display_name=body.display_name,
        phone=body.phone,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(sub=email, scope="user")
    return UserTokenSchema(
        access_token=token,
        token_type="bearer",
        user=UserOutSchema.model_validate(user),
    )


@router.post("/login", response_model=UserTokenSchema)
def login(body: UserLoginSchema, db: Session = Depends(get_db)) -> UserTokenSchema:
    """Verify email/password and return a JWT."""
    email = body.email.strip().lower()
    user = db.query(User).filter(User.email == email).first()
    if user is None or not user.is_active or not user.password_hash:
        raise HTTPException(status_code=401, detail="Identifiants invalides")
    if not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Identifiants invalides")
    token = create_access_token(sub=email, scope="user")
    return UserTokenSchema(
        access_token=token,
        token_type="bearer",
        user=UserOutSchema.model_validate(user),
    )