import hashlib
import hmac
import json
from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

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
