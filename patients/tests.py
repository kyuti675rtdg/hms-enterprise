from datetime import date

from django.test import TestCase
from django.urls import reverse

from hms_enterprise.testutils import login_as
from .models import Patient


class PatientTests(TestCase):
    def setUp(self):
        login_as(self.client, "receptionist")

    def _form_data(self, **overrides):
        data = {
            "first_name": "Zubair",
            "last_name": "Mwakio",
            "dob": "1990-04-12",
            "gender": "M",
            "phone": "0722000111",
            "email": "",
            "address": "",
            "blood_group": "O+",
            "allergies": "",
        }
        data.update(overrides)
        return data

    def test_create_patient(self):
        resp = self.client.post(reverse("patients:create"), self._form_data())
        self.assertEqual(resp.status_code, 302)
        patient = Patient.objects.get(phone="0722000111")
        self.assertTrue(patient.patient_no.startswith("P-"))

    def test_create_patient_validation(self):
        resp = self.client.post(reverse("patients:create"), self._form_data(first_name=""))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "This field is required")
        self.assertEqual(Patient.objects.count(), 0)

    def test_fulltext_search_finds_patient(self):
        Patient.objects.create(**{
            "first_name": "Zubair", "last_name": "Mwakio", "dob": date(1990, 4, 12),
            "gender": "M", "phone": "0722000111",
        })
        resp = self.client.get(reverse("patients:list"), {"q": "zubair"})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Zubair Mwakio")

    def test_fulltext_search_by_phone(self):
        p = Patient.objects.create(**{
            "first_name": "Amina", "last_name": "Said", "dob": date(1985, 1, 1),
            "gender": "F", "phone": "0733999888",
        })
        resp = self.client.get(reverse("patients:list"), {"q": "0733999888"})
        self.assertContains(resp, p.patient_no)

    def test_search_no_match(self):
        resp = self.client.get(reverse("patients:list"), {"q": "zzzznothing"})
        self.assertContains(resp, "No patients found")

    def test_doctor_can_view_but_not_create(self):
        from hms_enterprise.testutils import login_as as la
        self.client.logout()
        la(self.client, "doctor")
        self.assertEqual(self.client.get(reverse("patients:list")).status_code, 200)
        self.assertEqual(
            self.client.post(reverse("patients:create"), self._form_data()).status_code, 403
        )
