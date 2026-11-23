from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import connection
from django.test import Client, TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from tracker.models import JobApplication


class QualityBarTests(TestCase):
    @patch("jobmail.throttle.time", return_value=123)
    def test_rate_limit_post_and_retry_boundary(self, clock) -> None:
        cache.clear()
        self.addCleanup(cache.clear)
        address = "192.0.2.10"
        for route, limit in (("signup", 5), ("login", 10), ("subscribe_updates", 5)):
            with self.subTest(route=route):
                url = reverse(route)
                for _ in range(limit):
                    self.assertLess(
                        self.client.post(url, REMOTE_ADDR=address).status_code, 429
                    )
                response = self.client.post(
                    url, REMOTE_ADDR=address, HTTP_X_FORWARDED_FOR="192.0.2.99"
                )
                self.assertContains(response, "Too many requests", status_code=429)
                self.assertEqual(response.headers["Retry-After"], "57")
                self.assertLess(
                    self.client.post(url, REMOTE_ADDR="192.0.2.11").status_code, 429
                )
        clock.return_value = 180
        self.assertLess(
            self.client.post(reverse("login"), REMOTE_ADDR=address).status_code, 429
        )

    @override_settings(DEBUG=False, SECURE_SSL_REDIRECT=False)
    def test_safe_error_pages(self) -> None:
        self.assertContains(
            self.client.get("/missing-route/"), "Page unavailable", status_code=404
        )
        client = Client(raise_request_exception=False)
        with patch(
            "tracker.views.leadhub_origin",
            side_effect=RuntimeError("private failure marker"),
        ):
            response = client.get("/")
        self.assertContains(response, "Something went wrong", status_code=500)
        self.assertNotContains(response, "private failure marker", status_code=500)
        self.assertIn(
            "frame-ancestors 'none'", response.headers["Content-Security-Policy"]
        )

    def test_lookup_index_exists_after_migrations(self) -> None:
        with connection.cursor() as cursor:
            indexes = connection.introspection.get_constraints(
                cursor, JobApplication._meta.db_table
            )
        self.assertTrue(
            any(
                index["index"]
                and index["columns"] == ["user_id", "status", "updated_at"]
                for index in indexes.values()
            )
        )

    def test_dashboard_query_count_stays_constant_as_applications_grow(self) -> None:
        user = get_user_model().objects.create_user(username="query-proof")
        self.client.force_login(user)
        applications = [
            JobApplication(user=user, company=f"Demo Company {i}", role="Developer")
            for i in range(12)
        ]
        JobApplication.objects.bulk_create(applications[:2])
        with CaptureQueriesContext(connection) as first:
            self.assertContains(self.client.get(reverse("dashboard")), "Demo Company 1")
        JobApplication.objects.bulk_create(applications[2:])
        with CaptureQueriesContext(connection) as last:
            self.assertContains(
                self.client.get(reverse("dashboard")), "Demo Company 11"
            )
        self.assertEqual(len(first), len(last))
