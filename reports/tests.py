from django.test import TestCase
from django.urls import reverse

from hms_enterprise.testutils import login_as


class DashboardTests(TestCase):
    def test_dashboard_renders_for_all_roles(self):
        for role in ["admin", "doctor", "receptionist", "pharmacist", "labtech"]:
            with self.subTest(role=role):
                self.client.logout()
                login_as(self.client, role)
                resp = self.client.get(reverse("reports:dashboard"))
                self.assertEqual(resp.status_code, 200)
                self.assertContains(resp, "Revenue")

    def test_reports_csv_export(self):
        login_as(self.client, "admin")
        for kind in ["revenue", "appointments", "medicines"]:
            with self.subTest(kind=kind):
                resp = self.client.get(reverse("reports:export_csv", args=[kind]))
                self.assertEqual(resp.status_code, 200)
                self.assertEqual(resp["Content-Type"], "text/csv")
