from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone


class Invoice(models.Model):
    STATUS_UNPAID = "unpaid"
    STATUS_PARTIAL = "partial"
    STATUS_PAID = "paid"
    STATUS_CHOICES = [
        (STATUS_UNPAID, "Unpaid"),
        (STATUS_PARTIAL, "Partially paid"),
        (STATUS_PAID, "Paid"),
    ]

    invoice_no = models.CharField(max_length=20, unique=True, blank=True, null=True)
    patient = models.ForeignKey(
        "patients.Patient", on_delete=models.PROTECT, related_name="invoices"
    )
    issue_date = models.DateField(default=timezone.localdate)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    tax = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_UNPAID)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-issue_date", "-created_at"]

    def __str__(self):
        return f"{self.invoice_no or 'DRAFT'} — {self.patient} ({self.total})"

    @property
    def balance(self):
        return self.total - self.amount_paid

    def refresh_status(self):
        if self.amount_paid >= self.total:
            self.status = self.STATUS_PAID
        elif self.amount_paid > 0:
            self.status = self.STATUS_PARTIAL
        else:
            self.status = self.STATUS_UNPAID

    def save(self, *args, **kwargs):
        creating = self.pk is None
        super().save(*args, **kwargs)
        if creating and not self.invoice_no:
            self.invoice_no = f"INV-{self.pk:04d}"
            super().save(update_fields=["invoice_no"])


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="items")
    description = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("1"))
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    line_total = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.description} × {self.quantity}"


class Payment(models.Model):
    METHOD_CHOICES = [
        ("cash", "Cash"),
        ("mpesa", "M-Pesa"),
        ("card", "Card"),
        ("insurance", "Insurance"),
        ("bank", "Bank transfer"),
    ]

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    method = models.CharField(max_length=20, choices=METHOD_CHOICES, default="cash")
    paid_at = models.DateTimeField(auto_now_add=True)
    received_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ["-paid_at"]

    def __str__(self):
        return f"{self.amount} on {self.invoice.invoice_no}"
