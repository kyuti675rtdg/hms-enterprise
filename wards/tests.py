from datetime import date

from django.test import TestCase
from django.urls import reverse

from hms_enterprise.testutils import login_as
from patients.models import Patient
from .models import Admission, Bed, Ward


class WardTests(TestCase):
    def setUp(self):
        login_as(self.client, "receptionist")
        self.ward = Ward.objects.create(name="General A", ward_type="general", capacity=4)
        self.beds = [
            Bed.objects.create(ward=self.ward, bed_no=f"G-{i+1:02d}") for i in range(4)
        ]
        self.patient = Patient.objects.create(
            first_name="Test", last_name="Patient", dob=date(1990, 1, 1),
            gender="M", phone="0700000003",
        )

    def test_admit_occupies_bed(self):
        resp = self.client.post(reverse("wards:admission_create"), {
            "patient": self.patient.pk,
            "ward": self.ward.pk,
            "bed": self.beds[0].pk,
            "diagnosis": "Observation",
        })
        self.assertEqual(resp.status_code, 302)
        self.beds[0].refresh_from_db()
        self.assertEqual(self.beds[0].status, Bed.STATUS_OCCUPIED)
        admission = Admission.objects.get()
        self.assertEqual(admission.status, Admission.STATUS_ADMITTED)
        self.assertEqual(admission.bed, self.beds[0])

    def test_discharge_frees_bed(self):
        self.client.post(reverse("wards:admission_create"), {
            "patient": self.patient.pk,
            "ward": self.ward.pk,
            "bed": self.beds[1].pk,
            "diagnosis": "Observation",
        })
        admission = Admission.objects.get()
        resp = self.client.post(reverse("wards:discharge", args=[admission.pk]))
        self.assertEqual(resp.status_code, 302)
        admission.refresh_from_db()
        self.beds[1].refresh_from_db()
        self.assertEqual(admission.status, Admission.STATUS_DISCHARGED)
        self.assertIsNotNone(admission.discharge_date)
        self.assertEqual(self.beds[1].status, Bed.STATUS_AVAILABLE)

    def test_cannot_admit_to_occupied_bed(self):
        self.client.post(reverse("wards:admission_create"), {
            "patient": self.patient.pk, "ward": self.ward.pk,
            "bed": self.beds[2].pk, "diagnosis": "x",
        })
        patient2 = Patient.objects.create(
            first_name="Second", last_name="Patient", dob=date(1991, 2, 2),
            gender="F", phone="0700000004",
        )
        resp = self.client.post(reverse("wards:admission_create"), {
            "patient": patient2.pk, "ward": self.ward.pk,
            "bed": self.beds[2].pk, "diagnosis": "y",
        })
        self.assertEqual(resp.status_code, 200)  # re-rendered with error
        self.assertEqual(Admission.objects.count(), 1)
