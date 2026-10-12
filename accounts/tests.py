from django.test import TestCase
from django.urls import reverse

from hms_enterprise.testutils import login_as


class AuthGateTests(TestCase):
    def test_anonymous_redirected_to_login(self):
        resp = self.client.get(reverse("reports:dashboard"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("accounts:login"), resp.url)

    def test_anonymous_cannot_post(self):
        resp = self.client.post(reverse("patients:create"), {})
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("accounts:login"), resp.url)

    def test_wrong_role_gets_403(self):
        login_as(self.client, "doctor")
        resp = self.client.get(reverse("pharmacy:inventory"))
        self.assertEqual(resp.status_code, 403)

    def test_labtech_cannot_manage_users(self):
        login_as(self.client, "labtech")
        resp = self.client.get(reverse("accounts:user_list"))
        self.assertEqual(resp.status_code, 403)

    def test_admin_can_access_everything(self):
        login_as(self.client, "admin")
        for name in [
            "reports:dashboard",
            "patients:list",
            "scheduling:appointment_list",
            "pharmacy:inventory",
            "laboratory:order_list",
            "billing:invoice_list",
            "wards:ward_list",
            "reports:reports",
            "auditlog:event_list",
            "accounts:user_list",
        ]:
            with self.subTest(page=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 200)

    def test_login_page_renders(self):
        resp = self.client.get(reverse("accounts:login"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Sign in")
