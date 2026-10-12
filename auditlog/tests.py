from datetime import date

from django.test import TestCase
from django.urls import reverse

from hms_enterprise.testutils import login_as
from patients.models import Patient
from .models import AuditEvent


class AuditLogTests(TestCase):
    def test_audit_event_recorded_on_patient_update(self):
        admin = login_as(self.client, "admin")
        patient = Patient.objects.create(
            first_name="Audit", last_name="Me", dob=date(1990, 1, 1),
            gender="M", phone="0700000005",
        )
        AuditEvent.objects.all().delete()  # ignore the create event
        resp = self.client.post(reverse("patients:edit", args=[patient.pk]), {
            "first_name": "Audit", "last_name": "Me", "dob": "1990-01-01",
            "gender": "M", "phone": "0711111111", "email": "",
            "address": "", "blood_group": "", "allergies": "",
        })
        self.assertEqual(resp.status_code, 302)
        event = AuditEvent.objects.get()
        self.assertEqual(event.action, "update")
        self.assertEqual(event.model_name, "patients.patient")
        self.assertEqual(event.actor, admin)
        self.assertIn("phone", event.diff)
        self.assertEqual(event.diff["phone"]["old"], "0700000005")
        self.assertEqual(event.diff["phone"]["new"], "0711111111")

    def test_audit_event_on_create(self):
        login_as(self.client, "receptionist")
        Patient.objects.create(
            first_name="New", last_name="Patient", dob=date(1992, 3, 3),
            gender="F", phone="0700000006",
        )
        event = AuditEvent.objects.get(action="create", model_name="patients.patient")
        self.assertIn("first_name", event.diff)

    def test_audit_log_admin_only(self):
        self.client.logout()
        login_as(self.client, "doctor")
        resp = self.client.get(reverse("auditlog:event_list"))
        self.assertEqual(resp.status_code, 403)
