import hashlib
import hmac
import json

import requests
from django.conf import settings


class BillingConfigurationError(RuntimeError):
    pass


class BillingSubscriptionPending(RuntimeError):
    pass


def billing_available():
    if not all(
        (
            settings.RAZORPAY_KEY_ID,
            settings.RAZORPAY_KEY_SECRET,
            settings.RAZORPAY_PLAN_ID,
        )
    ):
        return False
    if settings.RAZORPAY_MODE == "test":
        return settings.RAZORPAY_KEY_ID.startswith("rzp_test_")
    return (
        settings.RAZORPAY_MODE == "live"
        and settings.LIVE_BILLING_ENABLED
        and settings.RAZORPAY_KEY_ID.startswith("rzp_live_")
    )


def create_subscription(user):
    if not all(
        (
            settings.RAZORPAY_KEY_ID,
            settings.RAZORPAY_KEY_SECRET,
            settings.RAZORPAY_PLAN_ID,
        )
    ):
        raise BillingConfigurationError(
            "Razorpay test plan and keys are not configured yet."
        )
    if settings.RAZORPAY_MODE == "test" and not settings.RAZORPAY_KEY_ID.startswith(
        "rzp_test_"
    ):
        raise BillingConfigurationError("Test mode only accepts Razorpay test keys.")
    if settings.RAZORPAY_MODE == "live" and (
        not settings.LIVE_BILLING_ENABLED
        or not settings.RAZORPAY_KEY_ID.startswith("rzp_live_")
    ):
        raise BillingConfigurationError(
            "Live billing has not been explicitly enabled by the owner."
        )
    if settings.RAZORPAY_MODE not in {"test", "live"}:
        raise BillingConfigurationError("Razorpay mode must be test or live.")
    response = requests.post(
        "https://api.razorpay.com/v1/subscriptions",
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET),
        json={
            "plan_id": settings.RAZORPAY_PLAN_ID,
            "total_count": 1200,
            "quantity": 1,
            "customer_notify": True,
            "notes": {"user_id": str(user.pk), "product": "JobMail"},
        },
        timeout=12,
    )
    response.raise_for_status()
    return response.json()


def verify_webhook_signature(body, signature):
    if (
        not settings.RAZORPAY_WEBHOOK_SECRET
        or not isinstance(signature, str)
        or len(signature) != 64
    ):
        return False
    try:
        actual = bytes.fromhex(signature)
    except ValueError:
        return False
    expected = hmac.new(
        settings.RAZORPAY_WEBHOOK_SECRET.encode(), body, hashlib.sha256
    ).digest()
    return hmac.compare_digest(expected, actual)


def update_subscription_from_event(event):
    payload = event
    for field in ("payload", "subscription", "entity"):
        payload = payload.get(field, {})
        if not isinstance(payload, dict):
            raise ValueError("Invalid subscription event structure.")
    provider_id = payload.get("id")
    status = payload.get("status")
    allowed = {
        "created",
        "authenticated",
        "active",
        "pending",
        "halted",
        "cancelled",
        "completed",
        "paused",
    }
    if (
        isinstance(provider_id, str)
        and provider_id
        and isinstance(status, str)
        and status in allowed
    ):
        from .models import BillingSubscription

        subscription = (
            BillingSubscription.objects.select_for_update()
            .filter(provider_id=provider_id)
            .first()
        )
        if subscription is None:
            raise BillingSubscriptionPending
        if subscription.status in {"cancelled", "completed"} and status not in {
            "cancelled",
            "completed",
        }:
            return
        if subscription.status == "active" and status in {
            "created",
            "authenticated",
            "pending",
        }:
            return
        subscription.status = status
        subscription.save(update_fields=["status", "updated_at"])


def parse_verified_event(body):
    event = json.loads(body.decode("utf-8"))
    if not isinstance(event, dict):
        raise ValueError("Webhook event must be an object.")
    return event
