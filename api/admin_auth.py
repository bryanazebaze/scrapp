"""Admin login endpoint. Issues an HS256 JWT for admins.

The admin JWT carries ``scope="admin"`` and is verified by
``core.admin_auth.require_admin``. End-user JWTs (``scope="user"``) and
Firebase ID tokens are NOT accepted by admin endpoints.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.admin_auth import authenticate_admin, create_access_token
from core.database import get_db
from core.schemas import AdminLoginSchema, AdminTokenSchema, AdminUserOutSchema

router = APIRouter(prefix="/admin", tags=["admin-auth"])


@router.post("/login", response_model=AdminTokenSchema)
def admin_login(body: AdminLoginSchema, db: Session = Depends(get_db)) -> AdminTokenSchema:
    """Authenticate an admin by username OR email + password and return a JWT."""
    admin = authenticate_admin(db, body.identifier, body.password)
    if admin is None:
        raise HTTPException(status_code=401, detail="Identifiants admin invalides")
    # Use username for the sub if present, else email — require_admin looks
    # up both.
    sub = (admin.username or admin.email or "")
    token = create_access_token(sub=sub, scope="admin")
    return AdminTokenSchema(
        access_token=token,
        token_type="bearer",
        admin=AdminUserOutSchema.model_validate(admin),
    )