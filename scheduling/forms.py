from django import forms

from .models import Appointment, Doctor


class DoctorForm(forms.ModelForm):
    class Meta:
        model = Doctor
        fields = [
            "first_name",
            "last_name",
            "specialization",
            "phone",
            "email",
            "consultation_fee",
            "active",
        ]


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ["patient", "doctor", "appt_date", "appt_time", "reason"]
        widgets = {
            "appt_date": forms.DateInput(attrs={"type": "date"}),
            "appt_time": forms.TimeInput(attrs={"type": "time"}),
            "reason": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["doctor"].queryset = Doctor.objects.filter(active=True)

    def clean(self):
        cleaned = super().clean()
        doctor = cleaned.get("doctor")
        appt_date = cleaned.get("appt_date")
        appt_time = cleaned.get("appt_time")
        if doctor and appt_date and appt_time:
            clash = Appointment.objects.filter(
                doctor=doctor,
                appt_date=appt_date,
                appt_time=appt_time,
                status=Appointment.STATUS_SCHEDULED,
            )
            if self.instance.pk:
                clash = clash.exclude(pk=self.instance.pk)
            if clash.exists():
                self.add_error(
                    "appt_time",
                    "This doctor already has a scheduled appointment at that date and time.",
                )
        return cleaned
