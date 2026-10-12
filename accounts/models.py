from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_ADMIN = "admin"
    ROLE_DOCTOR = "doctor"
    ROLE_RECEPTIONIST = "receptionist"
    ROLE_PHARMACIST = "pharmacist"
    ROLE_LABTECH = "labtech"

    ROLE_CHOICES = [
        (ROLE_ADMIN, "Administrator"),
        (ROLE_DOCTOR, "Doctor"),
        (ROLE_RECEPTIONIST, "Receptionist"),
        (ROLE_PHARMACIST, "Pharmacist"),
        (ROLE_LABTECH, "Lab Technician"),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_RECEPTIONIST)

    class Meta:
        ordering = ["username"]

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"
