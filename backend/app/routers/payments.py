import base64
import hashlib
import hmac
import json
from datetime import datetime, timedelta
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Header, Request, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Payment, PaymentStatus, User
from app.routers.dependencies import get_current_user

router = APIRouter()


def _razorpay_auth_header() -> Optional[str]:
    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        return None
    creds = f"{settings.RAZORPAY_KEY_ID}:{settings.RAZORPAY_KEY_SECRET}"
    return "Basic " + base64.b64encode(creds.encode()).decode()


@router.post("/razorpay/order")
async def create_razorpay_order(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a Razorpay order for the premium plan.
    Returns order_id and key_id for the frontend to open Razorpay Checkout.
    """
    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Razorpay is not configured. Please set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET.",
        )

    amount_in_paise = settings.PREMIUM_PRICE_INR * 100  # INR -> paise
    payload = {
        "amount": amount_in_paise,
        "currency": "INR",
        "receipt": f"premium_{current_user.id}_{int(datetime.utcnow().timestamp())}",
        "notes": {"user_id": current_user.id, "plan": "premium_30d"},
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": _razorpay_auth_header(),
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post("https://api.razorpay.com/v1/orders", headers=headers, json=payload)

    if resp.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to create Razorpay order: {resp.text}",
        )

    data = resp.json()
    order_id = data.get("id")
    if not order_id:
        raise HTTPException(status_code=500, detail="Invalid response from Razorpay: missing order id")

    # Store payment record
    payment = Payment(
        user_id=current_user.id,
        order_id=order_id,
        amount=amount_in_paise,
        currency="INR",
        status=PaymentStatus.CREATED,
        notes=payload.get("notes"),
    )
    db.add(payment)
    db.commit()

    return {
        "order_id": order_id,
        "key_id": settings.RAZORPAY_KEY_ID,
        "amount": amount_in_paise,
        "currency": "INR",
    }


def _verify_webhook_signature(body: bytes, signature: str) -> bool:
    if not settings.RAZORPAY_WEBHOOK_SECRET:
        return False
    expected = hmac.new(
        settings.RAZORPAY_WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


@router.post("/razorpay/webhook")
async def razorpay_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_razorpay_signature: str = Header(None),
):
    """
    Handle Razorpay webhook events. Expects signature verification.
    Upgrades user to premium on payment capture/order paid.
    """
    body = await request.body()
    if not _verify_webhook_signature(body, x_razorpay_signature or ""):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid webhook signature")

    payload = json.loads(body.decode())
    event = payload.get("event")
    payload_obj = payload.get("payload", {})

    # Extract order_id and payment_id if present
    order_id = None
    payment_id = None
    amount = None
    method = None
    entity = None

    if "payment" in payload_obj:
        entity = payload_obj["payment"].get("entity", {})
        order_id = entity.get("order_id")
        payment_id = entity.get("id")
        amount = entity.get("amount")
        method = entity.get("method")
    elif "order" in payload_obj:
        entity = payload_obj["order"].get("entity", {})
        order_id = entity.get("id")
        amount = entity.get("amount_paid")

    if not order_id:
        return {"status": "ignored", "reason": "no_order_id"}

    payment = db.query(Payment).filter(Payment.order_id == order_id).first()
    if not payment:
        return {"status": "ignored", "reason": "order_not_found"}

    # Only accept captured/paid events
    if event not in ("payment.captured", "order.paid"):
        return {"status": "ignored", "reason": f"unhandled_event_{event}"}

    # Update payment record
    payment.payment_id = payment_id or payment.payment_id
    payment.method = method or payment.method
    if amount:
        payment.amount = amount
    payment.status = PaymentStatus.CAPTURED
    db.commit()

    # Upgrade user to premium for configured validity
    user = db.query(User).filter(User.id == payment.user_id).first()
    if user:
        now = datetime.utcnow()
        current_valid = user.premium_valid_until or now
        new_valid_until = max(current_valid, now) + timedelta(days=settings.PREMIUM_VALID_DAYS)
        user.premium_status = "approved"
        user.premium_valid_until = new_valid_until
        db.commit()

    return {"status": "ok", "order_id": order_id, "payment_id": payment_id}

