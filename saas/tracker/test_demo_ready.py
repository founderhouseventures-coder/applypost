import io
from unittest import mock

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse


class DemoReadyTests(TestCase):
    def test_demo_login_is_off_by_default(self):
        self.assertEqual(self.client.post("/demo/").status_code, 404)

    def test_seeded_demo_user_sees_board_insights_and_export(self):
        call_command("seed_demo", stdout=io.StringIO())
        call_command("seed_demo", stdout=io.StringIO())
        with mock.patch.dict("os.environ", {"DEMO_MODE": "1"}):
            self.assertContains(self.client.get("/"), "Try the demo")
            response = self.client.post("/demo/")
        self.assertRedirects(response, reverse("board"), fetch_redirect_response=False)
        board = self.client.get(reverse("board"))
        self.assertContains(board, "Northstar Labs")
        self.assertContains(board, "Interview")
        insights = self.client.get(reverse("insights"))
        self.assertContains(insights, "24")
        self.assertContains(insights, "Design v3")
        self.assertContains(insights, "<rect", count=8)
        export = self.client.get(reverse("export_data")).content.decode()
        self.assertIn("Resume version", export.splitlines()[0])

    def test_board_and_insights_need_login(self):
        for name in ("board", "insights"):
            self.assertEqual(self.client.get(reverse(name)).status_code, 302)

    def test_pricing_has_three_plans_and_faq(self):
        page = self.client.get("/")
        for text in ("Starter", "JobMail Pro", "Career coach", "Questions, answered"):
            self.assertContains(page, text)
