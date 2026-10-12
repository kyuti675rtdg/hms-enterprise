from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from billing.models import Invoice

from hms_enterprise.testutils import login_as
from patients.models import Patient
from .models import Medicine, PharmacySale


class DispenseTests(TestCase):
    def setUp(self):
        login_as(self.client, "pharmacist")
        self.patient = Patient.objects.create(
            first_name="Test", last_name="Patient", dob=date(1990, 1, 1),
            gender="M", phone="0700000001",
        )
        self.medicine = Medicine.objects.create(
            name="Paracetamol 500mg", unit="tablet", quantity_in_stock=100,
            reorder_level=10, unit_price=Decimal("5.00"),
        )

    def test_dispense_decrements_stock_and_creates_invoice(self):
        resp = self.client.post(reverse("pharmacy:dispense"), {
            "patient": self.patient.pk,
            "medicine": self.medicine.pk,
            "quantity": 5,
        })
        self.assertEqual(resp.status_code, 302)
        self.medicine.refresh_from_db()
        self.assertEqual(self.medicine.quantity_in_stock, 95)
        sale = PharmacySale.objects.get()
        self.assertEqual(sale.quantity, 5)
        self.assertEqual(sale.total, Decimal("25.00"))
        invoice = Invoice.objects.get()
        self.assertEqual(invoice.total, Decimal("25.00"))
        self.assertEqual(invoice.status, Invoice.STATUS_UNPAID)
        self.assertEqual(invoice.items.count(), 1)

    def test_over_dispense_blocked(self):
        resp = self.client.post(reverse("pharmacy:dispense"), {
            "patient": self.patient.pk,
            "medicine": self.medicine.pk,
            "quantity": 500,
        })
        self.assertEqual(resp.status_code, 200)  # form re-rendered with error
        self.medicine.refresh_from_db()
        self.assertEqual(self.medicine.quantity_in_stock, 100)
        self.assertEqual(PharmacySale.objects.count(), 0)
        self.assertEqual(Invoice.objects.count(), 0)

    def test_receptionist_cannot_dispense(self):
        self.client.logout()
        login_as(self.client, "receptionist")
        resp = self.client.get(reverse("pharmacy:dispense"))
        self.assertEqual(resp.status_code, 403)
