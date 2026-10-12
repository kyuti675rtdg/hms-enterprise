from django.conf import settings
from django.db import models
from django.utils import timezone


class Ward(models.Model):
    WARD_TYPES = [
        ("general", "General"),
        ("pediatric", "Pediatric"),
        ("maternity", "Maternity"),
        ("icu", "ICU"),
        ("private", "Private"),
    ]

    name = models.CharField(max_length=100)
    ward_type = models.CharField(max_length=20, choices=WARD_TYPES, default="general")
    capacity = models.PositiveIntegerField(default=10)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.get_ward_type_display()})"

    @property
    def occupied_count(self):
        return self.beds.filter(status=Bed.STATUS_OCCUPIED).count()

    @property
    def available_count(self):
        return self.beds.filter(status=Bed.STATUS_AVAILABLE).count()


class Bed(models.Model):
    STATUS_AVAILABLE = "available"
    STATUS_OCCUPIED = "occupied"
    STATUS_MAINTENANCE = "maintenance"
    STATUS_CHOICES = [
        (STATUS_AVAILABLE, "Available"),
        (STATUS_OCCUPIED, "Occupied"),
        (STATUS_MAINTENANCE, "Maintenance"),
    ]

    ward = models.ForeignKey(Ward, on_delete=models.CASCADE, related_name="beds")
    bed_no = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_AVAILABLE)

    class Meta:
        ordering = ["ward__name", "bed_no"]
        constraints = [
            models.UniqueConstraint(fields=["ward", "bed_no"], name="unique_bed_per_ward")
        ]

    def __str__(self):
        return f"{self.ward.name} — Bed {self.bed_no}"


class Admission(models.Model):
    STATUS_ADMITTED = "admitted"
    STATUS_DISCHARGED = "discharged"
    STATUS_CHOICES = [
        (STATUS_ADMITTED, "Admitted"),
        (STATUS_DISCHARGED, "Discharged"),
    ]

    patient = models.ForeignKey(
        "patients.Patient", on_delete=models.CASCADE, related_name="admissions"
    )
    bed = models.ForeignKey(Bed, on_delete=models.PROTECT, related_name="admissions")
    doctor = models.ForeignKey(
        "scheduling.Doctor", on_delete=models.SET_NULL, null=True, blank=True
    )
    admit_date = models.DateField(default=timezone.localdate)
    discharge_date = models.DateField(null=True, blank=True)
    diagnosis = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ADMITTED)
    admitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ["-admit_date"]

    def __str__(self):
        return f"{self.patient} in {self.bed} ({self.status})"
