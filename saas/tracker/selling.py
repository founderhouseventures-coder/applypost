import re
from urllib.parse import urlsplit

import requests
from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from .models import BillingSubscription, PilotTrial

PROJECT_KEY = "applypost"
PILOT_AMOUNT = 29900


class UpdatesForm(forms.Form):
    email = forms.EmailField(max_length=254)
    consent = forms.BooleanField(label="Email me ApplyPost product updates")


def leadhub_origin():
    try:
        url = urlsplit(settings.LEADHUB_BASE_URL)
    except ValueError:
        return ""
    if (
        not url.hostname
        or url.username
        or url.password
        or url.path
        or url.query
        or url.fragment
    ):
        return ""
    if url.scheme == "https" or (
        settings.DEBUG
        and url.scheme == "http"
        and url.hostname in {"127.0.0.1", "localhost"}
    ):
        return url.geturl()
    return ""


@require_POST
def subscribe(request):
    form = UpdatesForm(request.POST)
    origin = leadhub_origin()
    if form.is_valid() and origin:
        try:
            reply = requests.post(
                f"{origin}/api/subscribe",
                json={
                    "email": form.cleaned_data["email"].lower(),
                    "project": PROJECT_KEY,
                    "consent": True,
                },
                timeout=5,
                allow_redirects=False,
            )
            if reply.status_code == 200 and reply.json().get("ok") is True:
                messages.success(
                    request, "If eligible, check your inbox to confirm your signup."
                )
                return redirect(f"{reverse('home')}#updates")
        except (requests.RequestException, ValueError, AttributeError):
            pass
        messages.error(
            request,
            "Product updates are temporarily unavailable. Please try again later.",
        )
    elif not form.is_valid():
        messages.error(request, "Enter a valid email address and confirm your consent.")
    else:
        messages.error(request, "Product updates are unavailable right now.")
    return redirect(f"{reverse('home')}#updates")


def application_limit(user):
    if BillingSubscription.objects.filter(user=user, status="active").exists():
        return None
    trial = getattr(user, "pilot_trial", None)
    if trial and trial.ends_at > timezone.now():
        return None
    return 25


@login_required
@require_POST
def start_trial(request):
    _, started = PilotTrial.objects.get_or_create(user=request.user)
    if started:
        messages.success(
            request,
            "Your 14-day trial started. Add an application and set a follow-up date.",
        )
    return redirect("dashboard")


def pilot_checkout_ready():
    return (
        settings.RAZORPAY_PILOT_TEST_ENABLED
        and settings.RAZORPAY_MODE == "test"
        and not settings.LIVE_BILLING_ENABLED
        and settings.RAZORPAY_KEY_ID.startswith("rzp_test_")
        and bool(settings.RAZORPAY_KEY_SECRET)
    )


def create_order(trial):
    response = requests.post(
        "https://api.razorpay.com/v1/orders",
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET),
        json={
            "amount": PILOT_AMOUNT,
            "currency": "INR",
            "receipt": f"ap-{trial.receipt.hex}",
            "notes": {"project": PROJECT_KEY},
        },
        timeout=10,
        allow_redirects=False,
    )
    if response.status_code != 200:
        raise ValueError("Test order was unavailable.")
    order = response.json()
    if (
        not isinstance(order, dict)
        or order.get("amount") != PILOT_AMOUNT
        or order.get("currency") != "INR"
        or not isinstance(order.get("id"), str)
        or not re.fullmatch(r"order_[A-Za-z0-9]{1,70}", order["id"])
    ):
        raise ValueError("Unexpected test order response.")
    return order["id"]


@login_required
@never_cache
@require_POST
def pilot_checkout(request):
    if not pilot_checkout_ready():
        messages.error(
            request,
            "Test checkout is unavailable until the founder configures test billing.",
        )
        return redirect("dashboard")
    try:
        with transaction.atomic():
            user = User.objects.select_for_update().get(pk=request.user.pk)
            trial = PilotTrial.objects.filter(user=user).first()
            if not trial:
                messages.error(
                    request, "Start your trial before opening test checkout."
                )
                return redirect("dashboard")
            if not trial.order_id:
                trial.order_id = create_order(trial)
                trial.save(update_fields=["order_id"])
    except (requests.RequestException, ValueError, User.DoesNotExist):
        messages.error(
            request, "Test checkout could not start. Your trial access is unchanged."
        )
        return redirect("dashboard")
    return render(
        request,
        "tracker/pilot_checkout.html",
        {
            "order_id": trial.order_id,
            "key": settings.RAZORPAY_KEY_ID,
            "amount": PILOT_AMOUNT,
        },
    )
