from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from hms_enterprise.testutils import login_as
from patients.models import Patient
from .models import Invoice, InvoiceItem, Payment


class BillingTests(TestCase):
    def setUp(self):
        login_as(self.client, "receptionist")
        self.patient = Patient.objects.create(
            first_name="Test", last_name="Patient", dob=date(1990, 1, 1),
            gender="F", phone="0700000002",
        )

    def _invoice(self, total="1000.00"):
        inv = Invoice.objects.create(
            patient=self.patient, subtotal=Decimal(total), total=Decimal(total)
        )
        InvoiceItem.objects.create(
            invoice=inv, description="Consultation", quantity=Decimal("1"),
            unit_price=Decimal(total), line_total=Decimal(total),
        )
        return inv

    def test_create_invoice_with_line_items(self):
        resp = self.client.post(reverse("billing:invoice_create"), {
            "patient": self.patient.pk,
            "description[]": ["Consultation", "X-Ray"],
            "quantity[]": ["1", "2"],
            "unit_price[]": ["1500", "2000"],
            "discount": "500",
            "tax": "0",
        })
        self.assertEqual(resp.status_code, 302)
        inv = Invoice.objects.get()
        self.assertEqual(inv.subtotal, Decimal("5500"))
        self.assertEqual(inv.total, Decimal("5000"))
        self.assertEqual(inv.items.count(), 2)

    def test_payment_marks_invoice_paid(self):
        inv = self._invoice()
        resp = self.client.post(reverse("billing:record_payment", args=[inv.pk]), {
            "amount": "1000.00", "method": "cash",
        })
        self.assertEqual(resp.status_code, 302)
        inv.refresh_from_db()
        self.assertEqual(inv.amount_paid, Decimal("1000.00"))
        self.assertEqual(inv.status, Invoice.STATUS_PAID)
        self.assertEqual(Payment.objects.count(), 1)

    def test_partial_payment(self):
        inv = self._invoice()
        self.client.post(reverse("billing:record_payment", args=[inv.pk]), {
            "amount": "400.00", "method": "mpesa",
        })
        inv.refresh_from_db()
        self.assertEqual(inv.status, Invoice.STATUS_PARTIAL)
        self.assertEqual(inv.balance, Decimal("600.00"))

    def test_overpay_blocked(self):
        inv = self._invoice()
        self.client.post(reverse("billing:record_payment", args=[inv.pk]), {
            "amount": "600.00", "method": "cash",
        })
        resp = self.client.post(reverse("billing:record_payment", args=[inv.pk]), {
            "amount": "500.00", "method": "cash",
        })
        self.assertEqual(resp.status_code, 302)
        inv.refresh_from_db()
        self.assertEqual(inv.amount_paid, Decimal("600.00"))  # unchanged
        self.assertEqual(inv.status, Invoice.STATUS_PARTIAL)
        self.assertEqual(Payment.objects.count(), 1)

    def test_receipt_renders(self):
        inv = self._invoice()
        resp = self.client.get(reverse("billing:receipt", args=[inv.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, inv.invoice_no)
