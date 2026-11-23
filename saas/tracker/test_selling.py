from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import JobApplication, PilotTrial


class SellingPathTests(TestCase):
    @override_settings(LEADHUB_BASE_URL="https://leads.example.test")
    @patch("tracker.selling.requests.post")
    def test_opt_in_relays_only_to_leadhub(self, post):
        url = reverse("subscribe_updates")
        self.client.post(url, {"email": "seeker@example.test"})
        post.assert_not_called()
        post.return_value.status_code = 200
        post.return_value.json.return_value = {"ok": True}
        response = self.client.post(
            url, {"email": "Seeker@example.test", "consent": "on"}, follow=True
        )
        self.assertContains(response, "check your inbox to confirm")
        post.assert_called_once_with(
            "https://leads.example.test/api/subscribe",
            json={
                "email": "seeker@example.test",
                "project": "applypost",
                "consent": True,
            },
            timeout=5,
            allow_redirects=False,
        )

    def test_trial_adds_capacity_and_expiry_preserves_existing_items(self):
        user = User.objects.create_user("pilot-user")
        self.client.force_login(user)
        JobApplication.objects.bulk_create(
            [
                JobApplication(user=user, company=f"Example {index}", role="Engineer")
                for index in range(25)
            ]
        )
        add = reverse("add_application")
        payload = {
            "company": "First follow-up",
            "role": "Engineer",
            "status": "applied",
        }
        self.client.post(add, payload)
        self.assertEqual(JobApplication.objects.count(), 25)
        self.assertRedirects(
            self.client.post(reverse("start_trial")), reverse("dashboard")
        )
        started_at = PilotTrial.objects.get().started_at
        self.client.post(reverse("start_trial"))
        self.assertEqual(PilotTrial.objects.get().started_at, started_at)
        self.client.post(add, payload)
        self.assertEqual(JobApplication.objects.count(), 26)

        PilotTrial.objects.update(started_at=timezone.now() - timedelta(days=15))
        self.client.post(add, payload)
        self.assertEqual(JobApplication.objects.count(), 26)
        self.assertContains(self.client.get(reverse("export_data")), "First follow-up")

    @override_settings(
        RAZORPAY_PILOT_TEST_ENABLED=True,
        RAZORPAY_MODE="test",
        LIVE_BILLING_ENABLED=False,
        RAZORPAY_KEY_ID="rzp_test_fixture",
        RAZORPAY_KEY_SECRET="synthetic-secret",
    )
    @patch("tracker.selling.requests.post")
    def test_pilot_checkout_creates_test_order_once_and_rejects_live_keys(self, post):
        user = User.objects.create_user("checkout-user")
        self.client.force_login(user)
        url = reverse("pilot_checkout")
        self.assertRedirects(self.client.post(url), reverse("dashboard"))
        post.assert_not_called()
        self.client.post(reverse("start_trial"))
        with self.settings(RAZORPAY_KEY_ID="rzp_live_fixture"):
            self.assertRedirects(self.client.post(url), reverse("dashboard"))
        post.assert_not_called()
        post.return_value.status_code = 200
        post.return_value.json.return_value = {
            "id": "order_fixture",
            "amount": 29900,
            "currency": "INR",
        }
        page = self.client.post(url)
        self.assertContains(page, "order_fixture")
        self.assertNotContains(page, "synthetic-secret")
        self.assertIn(
            "https://checkout.razorpay.com", page.headers["Content-Security-Policy"]
        )
        self.assertNotIn(
            "checkout.razorpay.com",
            self.client.get(reverse("home")).headers["Content-Security-Policy"],
        )
        self.assertContains(self.client.post(url), "order_fixture")
        post.assert_called_once()
        self.assertEqual(
            post.call_args.kwargs["json"]["notes"], {"project": "applypost"}
        )
        self.assertEqual(post.call_args.kwargs["json"]["amount"], 29900)
