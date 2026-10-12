from datetime import date

from django.test import TestCase
from django.urls import reverse

from hms_enterprise.testutils import login_as
from patients.models import Patient
from .models import MedicalRecord


class ClinicalTests(TestCase):
    def setUp(self):
        login_as(self.client, "doctor")
        self.patient = Patient.objects.create(
            first_name="Clinic", last_name="Test", dob=date(1990, 1, 1),
            gender="M", phone="0700000007",
        )

    def test_create_medical_record(self):
        resp = self.client.post(
            reverse("clinical:record_create", args=[self.patient.pk]), {
                "patient": self.patient.pk,
                "visit_date": "2026-10-10",
                "diagnosis": "Acute malaria",
                "prescription": "AL tablets",
                "notes": "",
                "doctor": "",
            })
        self.assertEqual(resp.status_code, 302)
        record = MedicalRecord.objects.get()
        self.assertEqual(record.diagnosis, "Acute malaria")
        self.assertEqual(record.patient, self.patient)

    def test_receptionist_cannot_create_record(self):
        self.client.logout()
        login_as(self.client, "receptionist")
        resp = self.client.post(
            reverse("clinical:record_create", args=[self.patient.pk]), {})
        self.assertEqual(resp.status_code, 403)

    def test_record_list_renders(self):
        resp = self.client.get(reverse("clinical:record_list"))
        self.assertEqual(resp.status_code, 200)
