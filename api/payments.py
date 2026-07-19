"""Payment endpoints — proxy to Notch Pay with the server-side API key.

This is the first authenticated router in the codebase: every endpoint
verifies the Firebase ID token (via ``core.auth``) so we know WHO paid.

Endpoints:
  POST /payments/upgrade            — initiate a Notch Pay payment (verified email required)
  GET  /payments/{reference}/status — check payment status and record result
  GET  /payments/me                 — check if the current user has paid
"""
from __future__ import annotations

import random
import string
import time
import logging
from datetime import datetime, timezone

import requests
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from core.auth import get_current_user, require_verified_email
from core.config import settings
from core.database import get_db
from core.models import PaymentRecord
from core.schemas import UpgradeRequest, PaymentStatusResponse, PaymentMeResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payments", tags=["payments"])

NOTCHPAY_BASE_URL = "https://api.notchpay.co"
DEFAULT_AMOUNT = 2000  # XAF — "Coffee" tier
PAYMENT_DESCRIPTION = "CentralImmo Premium — Coffee"


def _random_suffix(n: int = 4) -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=n))


def _make_reference(uid: str) -> str:
    """Generate a unique payment reference: CENTRAL-<uid>-<timestamp>-<random4>."""
    ts = int(time.time())
    return f"CENTRAL-{uid}-{ts}-{_random_suffix()}"


def _notchpay_headers() -> dict[str, str]:
    """Build the Authorization header for Notch Pay (raw key, no Bearer)."""
    if not settings.notchpay_public_key:
        raise HTTPException(
            status_code=503,
            detail="Service de paiement non configuré. Veuillez réessayer plus tard.",
        )
    return {"Authorization": settings.notchpay_public_key, "Content-Type": "application/json"}


# --------------------------------------------------------------------------- #
# POST /payments/upgrade
# --------------------------------------------------------------------------- #
@router.post("/upgrade", response_model=dict)
def initiate_upgrade(
    body: UpgradeRequest,
    user: dict = Depends(require_verified_email),
    db: Session = Depends(get_db),
):
    """Initiate a Notch Pay payment for the premium upgrade.

    1. Create the payment on Notch Pay (POST /payments).
    2. Trigger the USSD push to the user's phone (PUT /payments/{reference}).
    3. Return the reference so the frontend can poll /payments/{reference}/status.
    """
    if not settings.notchpay_keys_loaded:
        raise HTTPException(
            status_code=503,
            detail="Service de paiement non configuré. Veuillez réessayer plus tard.",
        )

    reference = _make_reference(user["uid"])
    email = user.get("email") or ""

    # --- Step 1: create payment ---
    create_payload = {
        "amount": body.amount,
        "currency": "XAF",
        "customer": {"email": email, "phone": body.phone},
        "description": PAYMENT_DESCRIPTION,
        "reference": reference,
    }
    try:
        resp = requests.post(
            f"{NOTCHPAY_BASE_URL}/payments",
            json=create_payload,
            headers=_notchpay_headers(),
            timeout=30,
        )
    except requests.RequestException as exc:
        logger.error("Notch Pay create request failed: %s", exc)
        raise HTTPException(status_code=502, detail="Erreur de communication avec Notch Pay.")

    if resp.status_code >= 400:
        detail = "Erreur lors de la création du paiement."
        try:
            err = resp.json()
            detail = err.get("message", detail)
        except Exception:
            pass
        raise HTTPException(status_code=502, detail=detail)

    # --- Step 2: trigger USSD push ---
    charge_payload = {
        "channel": body.channel,
        "data": {"phone": body.phone},
    }
    try:
        resp2 = requests.put(
            f"{NOTCHPAY_BASE_URL}/payments/{reference}",
            json=charge_payload,
            headers=_notchpay_headers(),
            timeout=30,
        )
    except requests.RequestException as exc:
        logger.error("Notch Pay charge request failed: %s", exc)
        raise HTTPException(status_code=502, detail="Erreur lors du déclenchement du paiement.")

    if resp2.status_code >= 400:
        detail = "Erreur lors du déclenchement du paiement."
        try:
            err = resp2.json()
            detail = err.get("message", detail)
        except Exception:
            pass
        raise HTTPException(status_code=502, detail=detail)

    return {"reference": reference}


# --------------------------------------------------------------------------- #
# GET /payments/{reference}/status
# --------------------------------------------------------------------------- #
@router.get("/{reference}/status", response_model=PaymentStatusResponse)
def check_payment_status(
    reference: str,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Check the Notch Pay payment status for ``reference``.

    If the status is terminal (complete | failed | canceled | expired) and
    we don't already have a PaymentRecord for this reference, insert one
    for the audit trail.
    """
    if not settings.notchpay_keys_loaded:
        raise HTTPException(
            status_code=503,
            detail="Service de paiement non configuré. Veuillez réessayer plus tard.",
        )

    try:
        resp = requests.get(
            f"{NOTCHPAY_BASE_URL}/payments/{reference}",
            headers=_notchpay_headers(),
            timeout=30,
        )
    except requests.RequestException as exc:
        logger.error("Notch Pay status request failed: %s", exc)
        raise HTTPException(status_code=502, detail="Erreur de communication avec Notch Pay.")

    if resp.status_code >= 400:
        detail = "Erreur lors de la vérification du paiement."
        try:
            err = resp.json()
            detail = err.get("message", detail)
        except Exception:
            pass
        raise HTTPException(status_code=502, detail=detail)

    data = resp.json()
    transaction = data.get("transaction", {})
    status = transaction.get("status", "pending")

    terminal_statuses = {"complete", "failed", "canceled", "expired"}
    is_paid = status == "complete"

    if status in terminal_statuses:
        # Check if we already have a record for this reference
        existing = db.execute(
            select(PaymentRecord).where(PaymentRecord.reference == reference)
        ).scalar_one_or_none()

        if existing is None:
            # Use the amount reported by Notch Pay if present; fall back to
            # the default tier amount when the field is missing/null.
            raw_amount = transaction.get("amount")
            recorded_amount = int(raw_amount) if raw_amount is not None else DEFAULT_AMOUNT
            record = PaymentRecord(
                firebase_uid=user["uid"],
                email=user.get("email"),
                amount=recorded_amount,
                reference=reference,
                status=status,
                notchpay_response=data,
                paid_at=datetime.now(timezone.utc) if is_paid else None,
            )
            db.add(record)
            db.commit()

    return PaymentStatusResponse(status=status, is_paid=is_paid, reference=reference)


# --------------------------------------------------------------------------- #
# GET /payments/me
# --------------------------------------------------------------------------- #
@router.get("/me", response_model=PaymentMeResponse)
def get_my_payment_status(
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return whether the current user has a completed payment on record."""
    record = db.execute(
        select(PaymentRecord)
        .where(
            PaymentRecord.firebase_uid == user["uid"],
            PaymentRecord.status == "complete",
        )
        .order_by(PaymentRecord.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()

    if record is None:
        return PaymentMeResponse(is_paid=False)

    return PaymentMeResponse(
        is_paid=True,
        paid_at=record.paid_at.isoformat() if record.paid_at else None,
        amount=record.amount,
    )