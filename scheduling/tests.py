from datetime import date, time

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from hms_enterprise.testutils import login_as
from patients.models import Patient
from .models import Appointment, Doctor


def make_patient(**kw):
    defaults = dict(first_name="Test", last_name="Patient", dob=date(1990, 1, 1),
                    gender="M", phone="0700000000")
    defaults.update(kw)
    return Patient.objects.create(**defaults)


def make_doctor(**kw):
    defaults = dict(first_name="Greg", last_name="House", specialization="Diagnostics")
    defaults.update(kw)
    return Doctor.objects.create(**defaults)


class AppointmentTests(TestCase):
    def setUp(self):
        login_as(self.client, "receptionist")
        self.patient = make_patient()
        self.doctor = make_doctor()

    def _book(self, **kw):
        defaults = dict(patient=self.patient, doctor=self.doctor,
                        appt_date=date(2026, 10, 20), appt_time=time(9, 0),
                        status=Appointment.STATUS_SCHEDULED)
        defaults.update(kw)
        return Appointment.objects.create(**defaults)

    def test_double_booking_raises_integrity_error(self):
        self._book()
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self._book()

    def test_cancelled_slot_can_be_rebooked(self):
        self._book(status=Appointment.STATUS_CANCELLED)
        appt = self._book()  # must not raise
        self.assertEqual(appt.status, Appointment.STATUS_SCHEDULED)

    def test_different_doctor_same_slot_ok(self):
        self._book()
        other = make_doctor(first_name="Other")
        appt = self._book(doctor=other)
        self.assertIsNotNone(appt.pk)

    def test_booking_view_blocks_double_booking(self):
        self._book()
        resp = self.client.post(reverse("scheduling:appointment_book"), {
            "patient": self.patient.pk,
            "doctor": self.doctor.pk,
            "appt_date": "2026-10-20",
            "appt_time": "09:00",
            "reason": "checkup",
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "already has a scheduled appointment")
        self.assertEqual(
            Appointment.objects.filter(status=Appointment.STATUS_SCHEDULED).count(), 1
        )

    def test_complete_appointment(self):
        appt = self._book()
        resp = self.client.post(
            reverse("scheduling:appointment_status", args=[appt.pk, "completed"])
        )
        self.assertEqual(resp.status_code, 302)
        appt.refresh_from_db()
        self.assertEqual(appt.status, Appointment.STATUS_COMPLETED)
