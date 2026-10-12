from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from hms_enterprise.testutils import login_as
from patients.models import Patient
from .models import LabOrder, LabTest


class LaboratoryTests(TestCase):
    def setUp(self):
        login_as(self.client, "labtech")
        self.patient = Patient.objects.create(
            first_name="Lab", last_name="Test", dob=date(1990, 1, 1),
            gender="F", phone="0700000008",
        )
        self.test = LabTest.objects.create(
            name="Full Blood Count", category="Hematology", price=Decimal("800")
        )

    def test_order_test(self):
        resp = self.client.post(reverse("laboratory:order_create"), {
            "patient": self.patient.pk, "test": self.test.pk,
        })
        self.assertEqual(resp.status_code, 302)
        order = LabOrder.objects.get()
        self.assertEqual(order.status, LabOrder.STATUS_ORDERED)

    def test_result_entry_completes_order(self):
        order = LabOrder.objects.create(patient=self.patient, test=self.test)
        resp = self.client.post(reverse("laboratory:result_entry", args=[order.pk]), {
            "result_text": "WBC normal, Hb 13.2 g/dL.",
        })
        self.assertEqual(resp.status_code, 302)
        order.refresh_from_db()
        self.assertEqual(order.status, LabOrder.STATUS_COMPLETED)
        self.assertIsNotNone(order.completed_at)
        self.assertIn("WBC", order.result_text)

    def test_catalog_viewable_by_labtech_but_edit_admin_only(self):
        self.assertEqual(self.client.get(reverse("laboratory:catalog")).status_code, 200)
        resp = self.client.post(reverse("laboratory:test_create"), {
            "name": "X", "price": "100",
        })
        self.assertEqual(resp.status_code, 403)
