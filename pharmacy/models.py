from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class Medicine(models.Model):
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=100, blank=True)
    unit = models.CharField(max_length=30, default="tablet")
    quantity_in_stock = models.PositiveIntegerField(default=0)
    reorder_level = models.PositiveIntegerField(default=10)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    expiry_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.quantity_in_stock} {self.unit} in stock)"

    @property
    def is_low_stock(self):
        return self.quantity_in_stock <= self.reorder_level

    @property
    def is_expiring_soon(self):
        if not self.expiry_date:
            return False
        return self.expiry_date <= timezone.localdate() + timedelta(days=90)

    @property
    def is_expired(self):
        if not self.expiry_date:
            return False
        return self.expiry_date < timezone.localdate()


class PharmacySale(models.Model):
    patient = models.ForeignKey(
        "patients.Patient", on_delete=models.PROTECT, related_name="pharmacy_sales"
    )
    medicine = models.ForeignKey(Medicine, on_delete=models.PROTECT, related_name="sales")
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    sold_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    sold_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-sold_at"]

    def __str__(self):
        return f"{self.quantity}× {self.medicine.name} for {self.patient}"
