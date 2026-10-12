from django.conf import settings
from django.db import models


class LabTest(models.Model):
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=100, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class LabOrder(models.Model):
    STATUS_ORDERED = "ordered"
    STATUS_COMPLETED = "completed"
    STATUS_CHOICES = [
        (STATUS_ORDERED, "Ordered"),
        (STATUS_COMPLETED, "Completed"),
    ]

    patient = models.ForeignKey(
        "patients.Patient", on_delete=models.CASCADE, related_name="lab_orders"
    )
    test = models.ForeignKey(LabTest, on_delete=models.PROTECT, related_name="orders")
    ordered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ORDERED)
    result_text = models.TextField(blank=True)
    ordered_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-ordered_at"]

    def __str__(self):
        return f"{self.test.name} for {self.patient} ({self.status})"
