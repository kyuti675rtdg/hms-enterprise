from django import forms

from .models import MedicalRecord


class MedicalRecordForm(forms.ModelForm):
    class Meta:
        model = MedicalRecord
        fields = ["patient", "doctor", "visit_date", "diagnosis", "prescription", "notes"]
        widgets = {
            "visit_date": forms.DateInput(attrs={"type": "date"}),
            "diagnosis": forms.Textarea(attrs={"rows": 3}),
            "prescription": forms.Textarea(attrs={"rows": 3}),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }
