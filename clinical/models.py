from django.conf import settings
from django.db import models
from django.utils import timezone


class MedicalRecord(models.Model):
    patient = models.ForeignKey(
        "patients.Patient", on_delete=models.CASCADE, related_name="medical_records"
    )
    doctor = models.ForeignKey(
        "scheduling.Doctor",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="medical_records",
    )
    visit_date = models.DateField(default=timezone.localdate)
    diagnosis = models.TextField()
    prescription = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-visit_date", "-created_at"]

    def __str__(self):
        return f"Record for {self.patient} on {self.visit_date}"
