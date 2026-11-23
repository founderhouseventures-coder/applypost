import hashlib
import hmac
import json
from datetime import timedelta
from unittest.mock import Mock, patch
from urllib.parse import urlparse

from django.contrib.auth.models import User
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import OperationalError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import BillingEvent, BillingSubscription, JobApplication
from .services import verify_webhook_signature


class ProductFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="founder-test",
            email="test@example.com",
            password="Strong-password-123",
        )

    def test_auth_required_and_dashboard_is_user_scoped(self):
        self.assertRedirects(
            self.client.get(reverse("dashboard")),
            f"{reverse('login')}?next={reverse('dashboard')}",
        )
        self.client.force_login(self.user)
        other = User.objects.create_user(
            username="other", password="Strong-password-123"
        )
        JobApplication.objects.create(user=other, company="Hidden Co", role="Engineer")
        self.assertNotContains(self.client.get(reverse("dashboard")), "Hidden Co")

    def test_dashboard_paginates_all_of_the_users_applications(self):
        JobApplication.objects.bulk_create(
            [
                JobApplication(user=self.user, company=f"Company {index}", role="Role")
                for index in range(27)
            ]
        )
        self.client.force_login(self.user)
        first_page = self.client.get(reverse("dashboard"))
        second_page = self.client.get(reverse("dashboard"), {"page": "2"})
        self.assertEqual(len(first_page.context["applications"]), 25)
        self.assertEqual(len(second_page.context["applications"]), 2)
        self.assertContains(first_page, 'aria-label="Applications pages"')

    def test_dashboard_search_and_status_filters_are_combined(self):
        JobApplication.objects.create(
            user=self.user, company="Acme", role="Engineer", status="interview"
        )
        JobApplication.objects.create(
            user=self.user, company="Acme", role="Designer", status="applied"
        )
        JobApplication.objects.create(
            user=self.user, company="Other", role="Engineer", status="interview"
        )
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("dashboard"), {"q": "acme", "status": "interview"}
        )
        self.assertEqual(response.context["page_obj"].paginator.count, 1)
        roles = [item.role for item in response.context["applications"]]
        self.assertEqual(roles, ["Engineer"])

    def test_dashboard_due_follow_up_filter_shows_only_open_due_items(self):
        today = timezone.localdate()
        due = JobApplication.objects.create(
            user=self.user, company="Due Co", role="Today", follow_up_on=today
        )
        overdue = JobApplication.objects.create(
            user=self.user,
            company="Past Co",
            role="Overdue",
            follow_up_on=today - timedelta(days=1),
        )
        JobApplication.objects.create(
            user=self.user,
            company="Future Co",
            role="Later",
            follow_up_on=today + timedelta(days=1),
        )
        JobApplication.objects.create(
            user=self.user,
            company="Closed Co",
            role="Rejected",
            status="rejected",
            follow_up_on=today,
        )
        self.client.force_login(self.user)
        response = self.client.get(reverse("dashboard"), {"follow_up": "due"})
        visible_ids = {item.pk for item in response.context["applications"]}
        self.assertEqual(visible_ids, {due.pk, overdue.pk})

    def test_invalid_application_keeps_entered_values_and_field_errors(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("add_application"),
            {"company": "", "role": "Engineer", "status": "applied"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Engineer")
        self.assertContains(response, "This field is required.")
        self.assertEqual(JobApplication.objects.filter(user=self.user).count(), 0)

    def test_application_create_export_and_delete_account(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("add_application"),
            {"company": "Acme", "role": "Engineer", "status": "applied"},
        )
        self.assertRedirects(response, reverse("dashboard"))
        self.assertEqual(JobApplication.objects.filter(user=self.user).count(), 1)
        self.assertIn(b"Acme", self.client.get(reverse("export_data")).content)
        self.client.post(reverse("delete_account"), {"confirm": "DELETE"})
        self.assertFalse(User.objects.filter(pk=self.user.pk).exists())

    def test_csv_export_neutralizes_spreadsheet_formulas(self):
        self.client.force_login(self.user)
        JobApplication.objects.create(
            user=self.user, company='=HYPERLINK("https://bad.example")', role="Engineer"
        )
        response = self.client.get(reverse("export_data"))
        self.assertIn(b"'=HYPERLINK", response.content)

    def test_csv_import_previews_then_confirms_validated_rows(self):
        self.client.force_login(self.user)
        csv_file = SimpleUploadedFile(
            "applications.csv",
            (
                b"Company,Role,Status,Source,Job URL,Applied on,Follow-up,Notes\n"
                b"Acme,Engineer,Applied,Referral,,2026-11-01,2026-11-28,First round\n"
            ),
            content_type="text/csv",
        )
        url = reverse("import_applications")
        self.assertRedirects(self.client.post(url, {"file": csv_file}), url)
        self.assertEqual(JobApplication.objects.filter(user=self.user).count(), 0)
        preview = self.client.get(url)
        self.assertContains(preview, "1 valid row · 0 duplicates or rows with errors")
        self.assertContains(preview, "No applications are saved until you confirm")
        self.assertRedirects(
            self.client.post(
                url,
                {"confirm": "yes", "preview_id": preview.context["preview"]["id"]},
            ),
            reverse("dashboard"),
        )
        application = JobApplication.objects.get(user=self.user)
        self.assertEqual(application.status, "applied")
        self.assertEqual(application.notes, "First round")

    def test_csv_import_skips_duplicates_and_invalid_rows(self):
        self.client.force_login(self.user)
        JobApplication.objects.create(user=self.user, company="Acme", role="Engineer")
        csv_file = SimpleUploadedFile(
            "applications.csv",
            (
                b"Company,Role,Status\n"
                b"acme,Engineer,Applied\n"
                b"New Co,Designer,Saved\n"
                b",Missing Company,Applied\n"
            ),
            content_type="text/csv",
        )
        url = reverse("import_applications")
        self.client.post(url, {"file": csv_file})
        preview = self.client.get(url)
        self.assertContains(preview, "Duplicate company and role; skipped.")
        self.assertContains(preview, "company: This field is required.")
        self.assertEqual(len(preview.context["preview"]["rows"]), 1)
        self.client.post(
            url,
            {"confirm": "yes", "preview_id": preview.context["preview"]["id"]},
        )
        self.assertEqual(JobApplication.objects.filter(user=self.user).count(), 2)

    def test_csv_import_rejects_oversized_uploads(self):
        self.client.force_login(self.user)
        oversized = SimpleUploadedFile(
            "large.csv", b"x" * (1024 * 1024 + 1), content_type="text/csv"
        )
        response = self.client.post(
            reverse("import_applications"), {"file": oversized}, follow=True
        )
        self.assertContains(response, "CSV files must be 1 MB or smaller.")
        self.assertEqual(JobApplication.objects.filter(user=self.user).count(), 0)

    def test_csv_import_respects_free_beta_capacity_without_partial_import(self):
        self.client.force_login(self.user)
        JobApplication.objects.bulk_create(
            [
                JobApplication(user=self.user, company=f"Existing {index}", role="Role")
                for index in range(24)
            ]
        )
        csv_file = SimpleUploadedFile(
            "applications.csv",
            b"Company,Role\nNew Co,Engineer\nOther Co,Designer\n",
            content_type="text/csv",
        )
        url = reverse("import_applications")
        self.client.post(url, {"file": csv_file})
        preview = self.client.get(url)
        self.assertContains(preview, "room for 1 more application;")
        self.client.post(
            url,
            {"confirm": "yes", "preview_id": preview.context["preview"]["id"]},
        )
        self.assertEqual(JobApplication.objects.filter(user=self.user).count(), 24)

    def test_csv_import_rejects_a_stale_preview_from_another_tab(self):
        self.client.force_login(self.user)
        url = reverse("import_applications")
        first_file = SimpleUploadedFile(
            "first.csv", b"Company,Role\nFirst Co,Engineer\n", content_type="text/csv"
        )
        second_file = SimpleUploadedFile(
            "second.csv", b"Company,Role\nSecond Co,Designer\n", content_type="text/csv"
        )
        self.client.post(url, {"file": first_file})
        first_preview = self.client.get(url).context["preview"]
        self.client.post(url, {"file": second_file})
        self.client.get(url)
        response = self.client.post(
            url, {"confirm": "yes", "preview_id": first_preview["id"]}
        )
        self.assertRedirects(response, url)
        self.assertEqual(JobApplication.objects.filter(user=self.user).count(), 0)

    @override_settings(RAZORPAY_WEBHOOK_SECRET="test-secret")
    def test_webhook_signature_and_duplicate_event_are_safe(self):
        body = json.dumps(
            {
                "event": "subscription.activated",
                "payload": {
                    "subscription": {"entity": {"id": "sub_1", "status": "active"}}
                },
            }
        ).encode()
        signature = hmac.new(b"test-secret", body, hashlib.sha256).hexdigest()
        self.assertTrue(verify_webhook_signature(body, signature))
        self.assertFalse(verify_webhook_signature(body + b" ", signature))
        self.assertFalse(verify_webhook_signature(body, "É" * 64))
        BillingSubscription.objects.create(
            user=self.user, provider_id="sub_1", status="created", plan_id="plan_1"
        )
        url = reverse("razorpay_webhook")
        headers = {
            "HTTP_X_RAZORPAY_SIGNATURE": signature,
            "HTTP_X_RAZORPAY_EVENT_ID": "evt_1",
        }
        self.assertEqual(
            self.client.post(
                url, body, content_type="application/json", **headers
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.post(
                url, body, content_type="application/json", **headers
            ).status_code,
            200,
        )
        self.assertEqual(BillingEvent.objects.count(), 1)
        self.assertEqual(
            BillingSubscription.objects.get(provider_id="sub_1").status, "active"
        )

    @override_settings(RAZORPAY_WEBHOOK_SECRET="test-secret")
    def test_early_webhook_retries_after_subscription_is_recorded(self):
        body = json.dumps(
            {
                "event": "subscription.activated",
                "payload": {
                    "subscription": {"entity": {"id": "sub_early", "status": "active"}}
                },
            }
        ).encode()
        signature = hmac.new(b"test-secret", body, hashlib.sha256).hexdigest()
        url = reverse("razorpay_webhook")
        headers = {
            "HTTP_X_RAZORPAY_SIGNATURE": signature,
            "HTTP_X_RAZORPAY_EVENT_ID": "evt_early",
        }
        early = self.client.post(url, body, content_type="application/json", **headers)
        self.assertEqual(early.status_code, 503)
        self.assertFalse(BillingEvent.objects.filter(event_id="evt_early").exists())
        subscription = BillingSubscription.objects.create(
            user=self.user, provider_id="sub_early", status="created", plan_id="plan_1"
        )
        applied = self.client.post(
            url, body, content_type="application/json", **headers
        )
        self.assertEqual(applied.status_code, 200)
        subscription.refresh_from_db()
        self.assertEqual(subscription.status, "active")
        self.assertTrue(BillingEvent.objects.filter(event_id="evt_early").exists())

    @override_settings(RAZORPAY_WEBHOOK_SECRET="test-secret")
    def test_malformed_signed_events_are_rejected_without_recording(self):
        url = reverse("razorpay_webhook")
        cases = (
            ([], "evt_root"),
            ({"event": "subscription.activated", "payload": []}, "evt_nested"),
            ({"event": ["subscription.activated"]}, "evt_type"),
            ({"event": "subscription.activated"}, "x" * 121),
        )
        for event, event_id in cases:
            with self.subTest(event=event, event_id=event_id):
                body = json.dumps(event).encode()
                signature = hmac.new(b"test-secret", body, hashlib.sha256).hexdigest()
                response = self.client.post(
                    url,
                    body,
                    content_type="application/json",
                    HTTP_X_RAZORPAY_SIGNATURE=signature,
                    HTTP_X_RAZORPAY_EVENT_ID=event_id,
                )
                self.assertEqual(response.status_code, 400)
        self.assertFalse(BillingEvent.objects.exists())

    def test_health_detects_failed_queries_and_does_not_cache(self):
        response = self.client.get(reverse("health"))
        self.assertEqual(response.json(), {"status": "ok"})
        self.assertIn("no-store", response.headers["Cache-Control"])
        self.assertEqual(self.client.post(reverse("health")).status_code, 405)
        with patch("tracker.views.connection.cursor", side_effect=OperationalError):
            self.assertEqual(self.client.get(reverse("health")).status_code, 503)

    def test_checkout_is_not_fake_when_keys_missing(self):
        self.client.force_login(self.user)
        with override_settings(
            RAZORPAY_KEY_ID="", RAZORPAY_KEY_SECRET="", RAZORPAY_PLAN_ID=""
        ):
            response = self.client.post(reverse("checkout"), follow=True)
        self.assertContains(response, "not configured")
        self.assertEqual(BillingSubscription.objects.count(), 0)

    @override_settings(
        RAZORPAY_KEY_ID="rzp_test_fake",
        RAZORPAY_KEY_SECRET="test-secret",
        RAZORPAY_PLAN_ID="plan_test",
        RAZORPAY_MODE="test",
    )
    @patch("tracker.services.requests.post")
    def test_test_checkout_creates_link_and_never_uses_live_mode(self, post):
        post.return_value = Mock(
            ok=True,
            json=lambda: {
                "id": "sub_test_1",
                "status": "created",
                "short_url": "https://rzp.io/rzp/test-checkout",
            },
        )
        self.client.force_login(self.user)
        response = self.client.post(reverse("checkout"))
        self.assertRedirects(
            response,
            "https://rzp.io/rzp/test-checkout",
            fetch_redirect_response=False,
        )
        subscription = BillingSubscription.objects.get(user=self.user)
        self.assertEqual(subscription.provider_mode, "test")
        self.assertEqual(post.call_args.kwargs["json"]["total_count"], 1200)

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_signup_requires_activation_and_stores_marketing_opt_in(self):
        response = self.client.post(
            reverse("signup"),
            {
                "username": "new-jobseeker",
                "email": " New@Example.com ",
                "password1": "A-long-unique-password-824!",
                "password2": "A-long-unique-password-824!",
                "product_updates": "on",
            },
        )
        self.assertRedirects(response, reverse("login"))
        user = User.objects.get(username="new-jobseeker")
        self.assertFalse(user.is_active)
        self.assertEqual(user.email, "new@example.com")
        self.assertTrue(user.marketing_preference.opted_in)
        activation_url = mail.outbox[0].body.strip().split()[-1]
        token = activation_url.rstrip("/").rsplit("/", 1)[-1]
        response = self.client.get(reverse("activate", args=[token]))
        self.assertRedirects(response, reverse("dashboard"))
        user.refresh_from_db()
        self.assertTrue(user.is_active)

    def test_signup_renders_one_optional_marketing_checkbox(self):
        response = self.client.get(reverse("signup"))
        self.assertEqual(response.content.count(b'name="product_updates"'), 1)
        self.assertContains(response, "Email me occasional product updates")

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        RAZORPAY_KEY_ID="rzp_test_fake",
        RAZORPAY_KEY_SECRET="test-secret",
        RAZORPAY_PLAN_ID="plan_test",
        RAZORPAY_MODE="test",
    )
    @patch("tracker.services.requests.post")
    def test_signup_to_checkout_preserves_an_existing_subscription(self, post):
        response = self.client.post(reverse("signup"), {
            "username": "journey-jobseeker", "email": "journey@example.test",
            "password1": "A-long-unique-password-824!",
            "password2": "A-long-unique-password-824!",
        })
        self.assertRedirects(response, reverse("login"))
        activation_path = urlparse(mail.outbox[0].body.strip().split()[-1]).path
        self.assertRedirects(self.client.get(activation_path), reverse("dashboard"))
        user = User.objects.get(username="journey-jobseeker")
        entry = self.client.post(reverse("add_application"), {
            "company": "Journey Co", "role": "Engineer", "status": "applied",
        })
        self.assertRedirects(entry, reverse("dashboard"))
        self.assertIn(b"Journey Co", self.client.get(reverse("export_data")).content)

        checkout_url = "https://rzp.io/rzp/test-checkout"
        post.return_value.json.return_value = {
            "id": "sub_journey", "status": "created", "short_url": checkout_url,
        }
        self.assertRedirects(
            self.client.post(reverse("checkout")),
            checkout_url,
            fetch_redirect_response=False,
        )
        subscription = BillingSubscription.objects.get(user=user)
        self.assertEqual(subscription.provider_mode, "test")
        for status in ("paused", "halted"):
            with self.subTest(status=status):
                subscription.status = status
                subscription.save(update_fields=["status"])
                self.assertRedirects(
                    self.client.post(reverse("checkout")), reverse("dashboard"),
                )
                self.assertRedirects(
                    self.client.post(reverse("delete_account"), {"confirm": "DELETE"}),
                    reverse("dashboard"),
                )
                subscription.refresh_from_db()
                self.assertEqual(subscription.provider_id, "sub_journey")
                self.assertEqual(subscription.status, status)
        post.assert_called_once()
        subscription.status = "cancelled"
        subscription.save(update_fields=["status"])
        self.assertRedirects(
            self.client.post(reverse("delete_account"), {"confirm": "DELETE"}),
            reverse("home"),
        )
        self.assertFalse(User.objects.filter(pk=user.pk).exists())
        self.assertFalse(JobApplication.objects.filter(company="Journey Co").exists())

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_password_reset_email_link_changes_password(self):
        response = self.client.post(
            reverse("password_reset"), {"email": self.user.email}
        )
        self.assertRedirects(response, reverse("password_reset_done"))
        self.assertEqual(len(mail.outbox), 1)
        reset_url = next(
            line for line in mail.outbox[0].body.splitlines() if line.startswith("http")
        )
        response = self.client.get(urlparse(reset_url).path, follow=True)
        self.assertContains(response, 'name="new_password1"')
        response = self.client.post(
            response.request["PATH_INFO"],
            {
                "new_password1": "New-strong-password-826!",
                "new_password2": "New-strong-password-826!",
            },
        )
        self.assertRedirects(response, reverse("password_reset_complete"))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("New-strong-password-826!"))
