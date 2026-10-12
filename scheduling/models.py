from django.conf import settings
from django.db import models
from django.db.models import Q


class Doctor(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    specialization = models.CharField(max_length=100)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"Dr. {self.first_name} {self.last_name} ({self.specialization})"


class Appointment(models.Model):
    STATUS_SCHEDULED = "scheduled"
    STATUS_COMPLETED = "completed"
    STATUS_CANCELLED = "cancelled"
    STATUS_NO_SHOW = "no_show"

    STATUS_CHOICES = [
        (STATUS_SCHEDULED, "Scheduled"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_CANCELLED, "Cancelled"),
        (STATUS_NO_SHOW, "No-show"),
    ]

    patient = models.ForeignKey(
        "patients.Patient", on_delete=models.CASCADE, related_name="appointments"
    )
    doctor = models.ForeignKey(
        Doctor, on_delete=models.SET_NULL, null=True, related_name="appointments"
    )
    appt_date = models.DateField()
    appt_time = models.TimeField()
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_SCHEDULED)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["appt_date", "appt_time"]
        constraints = [
            # A doctor can only hold one *scheduled* slot at a given date/time.
            # Cancelled/completed appointments don't block re-booking.
            models.UniqueConstraint(
                fields=["doctor", "appt_date", "appt_time"],
                condition=Q(status="scheduled"),
                name="no_double_booking",
            )
        ]

    def __str__(self):
        return f"{self.patient} with {self.doctor} on {self.appt_date} {self.appt_time}"
