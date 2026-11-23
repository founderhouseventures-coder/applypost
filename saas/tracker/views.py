import csv
import io
import secrets

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core import signing
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db import DatabaseError, connection, transaction
from django.db.models import Q
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_safe

from .forms import JobApplicationForm, SignUpForm
from .models import (
    BillingEvent,
    BillingSubscription,
    JobApplication,
    MarketingPreference,
)
from .selling import (
    UpdatesForm,
    application_limit,
    leadhub_origin,
    pilot_checkout_ready,
)
from .services import (
    BillingConfigurationError,
    BillingSubscriptionPending,
    billing_available,
    create_subscription,
    parse_verified_event,
    update_subscription_from_event,
    verify_webhook_signature,
)

IMPORT_PREVIEW_KEY = "jobmail_import_preview"
IMPORT_MAX_BYTES = 1024 * 1024
IMPORT_MAX_ROWS = 100
OPEN_SUBSCRIPTION_STATUSES = (
    "created",
    "authenticated",
    "active",
    "pending",
    "paused",
    "halted",
)


def home(request):
    return render(
        request,
        "tracker/home.html",
        {
            "price": settings.PRO_PRICE_DISPLAY,
            "updates_form": UpdatesForm(),
            "updates_ready": bool(leadhub_origin()),
        },
    )


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


def dashboard_context(request, form=None):
    all_applications = JobApplication.objects.filter(user=request.user)
    applications = all_applications
    search_query = request.GET.get("q", "").strip()[:120]
    status_filter = request.GET.get("status", "")
    follow_up_filter = request.GET.get("follow_up", "")
    valid_statuses = {value for value, _ in JobApplication.Status.choices}
    if search_query:
        applications = applications.filter(
            Q(company__icontains=search_query)
            | Q(role__icontains=search_query)
            | Q(source__icontains=search_query)
        )
    if status_filter in valid_statuses:
        applications = applications.filter(status=status_filter)
    else:
        status_filter = ""
    if follow_up_filter == "due":
        applications = applications.filter(
            follow_up_on__lte=timezone.localdate(),
            status__in=["saved", "applied", "interview"],
        )
    else:
        follow_up_filter = ""
    page_obj = Paginator(applications, 25).get_page(request.GET.get("page"))
    counts = {
        status: all_applications.filter(status=status).count()
        for status, _ in JobApplication.Status.choices
    }
    return {
        "applications": page_obj.object_list,
        "page_obj": page_obj,
        "counts": counts,
        "total_count": sum(counts.values()),
        "search_query": search_query,
        "status_filter": status_filter,
        "follow_up_filter": follow_up_filter,
        "status_choices": JobApplication.Status.choices,
        "form": form or JobApplicationForm(),
        "subscription": getattr(request.user, "billing_subscription", None),
        "price": settings.PRO_PRICE_DISPLAY,
        "billing_ready": billing_available(),
        "pilot_trial": getattr(request.user, "pilot_trial", None),
        "pilot_checkout_ready": pilot_checkout_ready(),
    }


@login_required
def dashboard(request):
    return render(request, "tracker/dashboard.html", dashboard_context(request))


@login_required
@require_POST
def add_application(request):
    form = JobApplicationForm(request.POST)
    if form.is_valid():
        with transaction.atomic():
            user = User.objects.select_for_update().get(pk=request.user.pk)
            limit = application_limit(user)
            if (
                limit is not None
                and JobApplication.objects.filter(user=user).count() >= limit
            ):
                capacity_reached = True
            else:
                application = form.save(commit=False)
                application.user = user
                application.save()
                capacity_reached = False
        if capacity_reached:
            messages.error(
                request,
                "Free beta includes 25 tracked applications. "
                "Upgrade to continue adding more.",
            )
            return redirect("dashboard")
        messages.success(request, "Application saved.")
    else:
        messages.error(request, "Check the application fields and try again.")
        return render(
            request, "tracker/dashboard.html", dashboard_context(request, form)
        )
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


def _import_context(request):
    limit = application_limit(request.user)
    tracked = JobApplication.objects.filter(user=request.user).count()
    remaining = None if limit is None else max(0, limit - tracked)
    return {
        "preview": request.session.get(IMPORT_PREVIEW_KEY),
        "remaining_slots": remaining,
        "unlimited": limit is None,
    }


@login_required
def import_applications(request):
    if request.method == "GET":
        return render(request, "tracker/import_page.html", _import_context(request))

    if request.POST.get("confirm") == "yes":
        preview = request.session.get(IMPORT_PREVIEW_KEY)
        if (
            not preview
            or not preview.get("rows")
            or request.POST.get("preview_id") != preview.get("id")
        ):
            messages.error(request, "Upload a CSV and review its preview first.")
            return redirect("import_applications")
        rows = preview["rows"]
        capacity_error = None
        stale_preview = False
        with transaction.atomic():
            user = User.objects.select_for_update().get(pk=request.user.pk)
            limit = application_limit(user)
            tracked = JobApplication.objects.filter(user=user).count()
            remaining = None if limit is None else max(0, limit - tracked)
            if remaining is not None and len(rows) > remaining:
                noun = "application" if remaining == 1 else "applications"
                capacity_error = (
                    f"Your free beta has room for {remaining} more {noun}; "
                    f"this preview has {len(rows)} valid rows. Remove some rows "
                    "from the CSV or free up space, then upload it again."
                )
            else:
                existing = {
                    (company.strip().casefold(), role.strip().casefold())
                    for company, role in JobApplication.objects.filter(
                        user=user
                    ).values_list("company", "role")
                }
                applications = []
                for row in rows:
                    form = JobApplicationForm(row)
                    if not form.is_valid():
                        stale_preview = True
                        break
                    data = form.cleaned_data
                    key = (
                        data["company"].strip().casefold(),
                        data["role"].strip().casefold(),
                    )
                    if key in existing:
                        stale_preview = True
                        break
                    existing.add(key)
                    applications.append(JobApplication(user=user, **data))
                if not stale_preview:
                    JobApplication.objects.bulk_create(applications)
        if capacity_error:
            preview["capacity_error"] = capacity_error
            request.session[IMPORT_PREVIEW_KEY] = preview
            messages.error(request, capacity_error)
            return render(request, "tracker/import_page.html", _import_context(request))
        if stale_preview:
            messages.error(
                request,
                "Your applications changed after preview. Upload the CSV again.",
            )
            return redirect("import_applications")
        request.session.pop(IMPORT_PREVIEW_KEY, None)
        messages.success(request, f"Imported {len(applications)} applications.")
        return redirect("dashboard")

    request.session.pop(IMPORT_PREVIEW_KEY, None)
    uploaded = request.FILES.get("file")
    if not uploaded:
        messages.error(request, "Choose a CSV file to preview.")
        return redirect("import_applications")
    if uploaded.size > IMPORT_MAX_BYTES:
        messages.error(request, "CSV files must be 1 MB or smaller.")
        return redirect("import_applications")
    try:
        content = uploaded.read().decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(content, newline=""))
        columns = {
            "company": "company",
            "role": "role",
            "status": "status",
            "source": "source",
            "job url": "job_url",
            "applied on": "applied_on",
            "follow-up": "follow_up_on",
            "notes": "notes",
        }
        source_columns = {
            str(name).strip().casefold(): name for name in (reader.fieldnames or [])
        }
        if not {"company", "role"}.issubset(source_columns):
            raise ValueError("CSV needs Company and Role columns.")
        status_values = {
            label.casefold(): value for value, label in JobApplication.Status.choices
        }
        status_values.update(
            {value.casefold(): value for value, _ in JobApplication.Status.choices}
        )
        existing = {
            (company.strip().casefold(), role.strip().casefold())
            for company, role in JobApplication.objects.filter(
                user=request.user
            ).values_list("company", "role")
        }
        rows, errors = [], []
        data_rows = 0
        for line, raw in enumerate(reader, start=2):
            if not raw or not any(str(value or "").strip() for value in raw.values()):
                continue
            data_rows += 1
            if data_rows > IMPORT_MAX_ROWS:
                raise ValueError(f"CSV is limited to {IMPORT_MAX_ROWS} data rows.")
            normalized = {
                str(key).strip().casefold(): value for key, value in raw.items() if key
            }
            data = {
                target: str(normalized.get(header, "") or "").strip()
                for header, target in columns.items()
                if header in source_columns
            }
            raw_status = data.get("status", "").casefold()
            data["status"] = status_values.get(raw_status, raw_status) or "saved"
            form = JobApplicationForm(data)
            if not form.is_valid():
                detail = "; ".join(
                    f"{field}: {', '.join(str(message) for message in messages)}"
                    for field, messages in form.errors.items()
                )
                errors.append({"line": line, "message": detail})
                continue
            cleaned = form.cleaned_data
            key = (cleaned["company"].casefold(), cleaned["role"].casefold())
            if key in existing:
                errors.append(
                    {"line": line, "message": "Duplicate company and role; skipped."}
                )
                continue
            existing.add(key)
            rows.append(
                {
                    field: value.isoformat() if hasattr(value, "isoformat") else value
                    for field, value in cleaned.items()
                }
            )
    except (UnicodeDecodeError, csv.Error, ValueError) as error:
        messages.error(request, str(error) or "This file is not a valid UTF-8 CSV.")
        return redirect("import_applications")

    preview = {"id": secrets.token_urlsafe(16), "rows": rows, "errors": errors}
    context = _import_context(request)
    remaining = context["remaining_slots"]
    if remaining is not None and len(rows) > remaining:
        noun = "application" if remaining == 1 else "applications"
        preview["capacity_error"] = (
            f"Your free beta has room for {remaining} more {noun}; "
            f"this preview has {len(rows)} valid rows. Remove some rows "
            "from the CSV or free up space, then upload it again."
        )
    request.session[IMPORT_PREVIEW_KEY] = preview
    request.session.set_expiry(10 * 60)
    return redirect("import_applications")


@login_required
@require_POST
def delete_account(request):
    if request.POST.get("confirm") != "DELETE":
        messages.error(request, "Type DELETE to confirm account removal.")
        return redirect("dashboard")
    if BillingSubscription.objects.filter(
        user=request.user,
        status__in=OPEN_SUBSCRIPTION_STATUSES,
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
                status__in=OPEN_SUBSCRIPTION_STATUSES,
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
        if (
            not event_id
            or len(event_id) > 120
            or not isinstance(event_type, str)
            or not event_type
            or len(event_type) > 100
        ):
            return HttpResponseBadRequest("Missing event metadata")
        with transaction.atomic():
            _, created = BillingEvent.objects.get_or_create(
                event_id=event_id, defaults={"event_type": event_type}
            )
            if created:
                update_subscription_from_event(event)
    except BillingSubscriptionPending:
        return HttpResponse("Subscription is not recorded yet", status=503)
    except ValueError:
        return HttpResponseBadRequest("Invalid webhook payload")
    return HttpResponse(status=200)


@never_cache
@require_safe
def health(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except DatabaseError:
        return JsonResponse({"status": "unavailable"}, status=503)
    return JsonResponse({"status": "ok"})


def robots_txt(request):
    return HttpResponse(
        "User-agent: *\nAllow: /\nDisallow: /dashboard/\nDisallow: /accounts/\n"
        + "Sitemap: "
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
