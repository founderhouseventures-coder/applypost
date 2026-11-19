import csv
import json

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core import signing
from django.core.mail import send_mail
from django.db import connection, transaction
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .forms import JobApplicationForm, SignUpForm
from .models import (
    BillingEvent,
    BillingSubscription,
    JobApplication,
    MarketingPreference,
)
from .services import (
    BillingConfigurationError,
    billing_available,
    create_subscription,
    parse_verified_event,
    update_subscription_from_event,
    verify_webhook_signature,
)


def home(request):
    return render(request, "tracker/home.html", {"price": settings.PRO_PRICE_DISPLAY})


def signup(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = SignUpForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save(commit=False)
        user.email = form.cleaned_data["email"].lower()
        user.is_active = False
        user.save()
        MarketingPreference.objects.create(
            user=user, opted_in=form.cleaned_data["product_updates"]
        )
        token = signing.dumps({"uid": user.pk}, salt="jobmail-email-activation")
        link = request.build_absolute_uri(reverse("activate", args=[token]))
        try:
            send_mail(
                "Confirm your JobMail account",
                f"Confirm your email to activate your account: {link}",
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
            )
        except Exception:
            user.delete()
            messages.error(
                request,
                "We could not send the activation email. Please try again later.",
            )
            return redirect("signup")
        messages.success(request, "Check your email for the account activation link.")
        return redirect("login")
    return render(
        request,
        "tracker/form_page.html",
        {"form": form, "title": "Create your account", "submit": "Create account"},
    )


def activate(request, token):
    try:
        data = signing.loads(
            token, salt="jobmail-email-activation", max_age=60 * 60 * 24
        )
        user = User.objects.get(pk=data["uid"], is_active=False)
    except (
        signing.BadSignature,
        signing.SignatureExpired,
        User.DoesNotExist,
        KeyError,
        TypeError,
    ):
        messages.error(
            request,
            "That activation link is invalid or expired. Please create a new account.",
        )
        return redirect("signup")
    user.is_active = True
    user.save(update_fields=["is_active"])
    login(request, user)
    messages.success(request, "Your account is ready.")
    return redirect("dashboard")


@login_required
def dashboard(request):
    applications = JobApplication.objects.filter(user=request.user)
    counts = {
        status: applications.filter(status=status).count()
        for status, _ in JobApplication.Status.choices
    }
    return render(
        request,
        "tracker/dashboard.html",
        {
            "applications": applications[:100],
            "counts": counts,
            "form": JobApplicationForm(),
            "subscription": getattr(request.user, "billing_subscription", None),
            "price": settings.PRO_PRICE_DISPLAY,
            "billing_ready": billing_available(),
        },
    )


@login_required
@require_POST
def add_application(request):
    subscription = BillingSubscription.objects.filter(
        user=request.user, status="active"
    ).exists()
    if (
        not subscription
        and JobApplication.objects.filter(user=request.user).count() >= 25
    ):
        messages.error(
            request,
            "Free beta includes 25 tracked applications. "
            "Upgrade to continue adding more.",
        )
        return redirect("dashboard")
    form = JobApplicationForm(request.POST)
    if form.is_valid():
        application = form.save(commit=False)
        application.user = request.user
        application.save()
        messages.success(request, "Application saved.")
    else:
        messages.error(request, "Check the application fields and try again.")
    return redirect("dashboard")


@login_required
@require_POST
def delete_application(request, pk):
    get_object_or_404(JobApplication, pk=pk, user=request.user).delete()
    messages.success(request, "Application removed.")
    return redirect("dashboard")


@login_required
def edit_application(request, pk):
    application = get_object_or_404(JobApplication, pk=pk, user=request.user)
    form = JobApplicationForm(request.POST or None, instance=application)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Application updated.")
        return redirect("dashboard")
    return render(
        request,
        "tracker/form_page.html",
        {"form": form, "title": "Update application", "submit": "Save changes"},
    )


@login_required
def export_data(request):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="jobmail-applications.csv"'
    writer = csv.writer(response)
    writer.writerow(
        [
            "Company",
            "Role",
            "Status",
            "Source",
            "Job URL",
            "Applied on",
            "Follow-up",
            "Notes",
        ]
    )

    def safe_cell(value):
        value = str(value or "")
        return (
            f"'{value}" if value.startswith(("=", "+", "-", "@", "\t", "\r")) else value
        )

    for item in JobApplication.objects.filter(user=request.user).iterator():
        writer.writerow(
            [
                safe_cell(value)
                for value in [
                    item.company,
                    item.role,
                    item.get_status_display(),
                    item.source,
                    item.job_url,
                    item.applied_on or "",
                    item.follow_up_on or "",
                    item.notes,
                ]
            ]
        )
    return response


@login_required
@require_POST
def delete_account(request):
    if request.POST.get("confirm") != "DELETE":
        messages.error(request, "Type DELETE to confirm account removal.")
        return redirect("dashboard")
    if BillingSubscription.objects.filter(
        user=request.user,
        status__in=[
            "created",
            "authenticated",
            "active",
            "pending",
            "paused",
            "halted",
        ],
    ).exists():
        messages.error(
            request,
            "Cancel your subscription first. Once the billing provider confirms "
            "cancellation, you can delete your account.",
        )
        return redirect("dashboard")
    request.user.delete()
    messages.success(request, "Your account and tracked applications were deleted.")
    return redirect("home")


@login_required
@require_POST
def checkout(request):
    try:
        with transaction.atomic():
            user = User.objects.select_for_update().get(pk=request.user.pk)
            existing = BillingSubscription.objects.filter(
                user=user,
                status__in=["created", "authenticated", "active", "pending"],
            ).exists()
            if existing:
                messages.info(
                    request, "A subscription is already linked to this account."
                )
                return redirect("dashboard")
            data = create_subscription(user)
            BillingSubscription.objects.update_or_create(
                user=user,
                defaults={
                    "provider_id": data["id"],
                    "status": data.get("status", "created"),
                    "provider_mode": settings.RAZORPAY_MODE,
                    "plan_id": settings.RAZORPAY_PLAN_ID,
                },
            )
        if data.get("short_url", "").startswith("https://rzp.io/"):
            return redirect(data["short_url"])
        messages.error(
            request, "Payment link response was not valid. Please try again."
        )
    except BillingConfigurationError as exc:
        messages.error(request, str(exc))
    except (requests.RequestException, KeyError, ValueError):
        messages.error(request, "Payment setup could not start. No payment was taken.")
    return redirect("dashboard")


@login_required
@require_POST
def cancel_subscription(request):
    subscription = get_object_or_404(BillingSubscription, user=request.user)
    if subscription.provider_mode != settings.RAZORPAY_MODE or not billing_available():
        messages.error(request, "Billing is not configured yet.")
        return redirect("dashboard")
    try:
        response = requests.post(
            f"https://api.razorpay.com/v1/subscriptions/{subscription.provider_id}/cancel",
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET),
            json={"cancel_at_cycle_end": 1},
            timeout=12,
        )
    except requests.RequestException:
        messages.error(
            request, "Razorpay could not be reached. No cancellation was confirmed."
        )
        return redirect("dashboard")
    if response.ok:
        messages.success(
            request,
            "Cancellation requested. Access remains until the current billing "
            "cycle ends.",
        )
    else:
        messages.error(
            request,
            "Cancellation could not be confirmed. Please try again from billing "
            "support.",
        )
    return redirect("dashboard")


@csrf_exempt
@require_POST
def razorpay_webhook(request):
    if not verify_webhook_signature(
        request.body, request.headers.get("X-Razorpay-Signature", "")
    ):
        return HttpResponseBadRequest("Invalid webhook signature")
    try:
        event = parse_verified_event(request.body)
        event_id = request.headers.get("X-Razorpay-Event-Id")
        event_type = event.get("event")
        if not event_id or not event_type:
            return HttpResponseBadRequest("Missing event metadata")
        with transaction.atomic():
            _, created = BillingEvent.objects.get_or_create(
                event_id=event_id, defaults={"event_type": event_type}
            )
            if created:
                update_subscription_from_event(event)
    except (ValueError, TypeError, json.JSONDecodeError):
        return HttpResponseBadRequest("Invalid webhook payload")
    return HttpResponse(status=200)


def health(request):
    try:
        connection.ensure_connection()
    except Exception:
        return JsonResponse({"status": "unavailable"}, status=503)
    return JsonResponse({"status": "ok"})


def robots_txt(request):
    return HttpResponse(
        "User-agent: *\nAllow: /\nDisallow: /dashboard/\nDisallow: /accounts/\n"
        + request.build_absolute_uri(reverse("sitemap"))
        + "\n",
        content_type="text/plain",
    )


def sitemap(request):
    base = request.build_absolute_uri("/").rstrip("/")
    return HttpResponse(
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"<url><loc>{base}/</loc></url><url><loc>{base}/pricing/</loc></url>"
        "</urlset>",
        content_type="application/xml",
    )
