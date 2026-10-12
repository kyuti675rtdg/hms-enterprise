from django import forms

from .models import Medicine, PharmacySale


class MedicineForm(forms.ModelForm):
    class Meta:
        model = Medicine
        fields = [
            "name",
            "category",
            "unit",
            "quantity_in_stock",
            "reorder_level",
            "unit_price",
            "expiry_date",
        ]
        widgets = {"expiry_date": forms.DateInput(attrs={"type": "date"})}


class DispenseForm(forms.Form):
    patient = forms.ModelChoiceField(
        queryset=None, label="Patient", widget=forms.Select(attrs={"class": "select2-patient"})
    )
    medicine = forms.ModelChoiceField(queryset=None, label="Medicine")
    quantity = forms.IntegerField(min_value=1, initial=1)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from patients.models import Patient

        self.fields["patient"].queryset = Patient.objects.all().order_by("first_name")
        self.fields["medicine"].queryset = Medicine.objects.filter(quantity_in_stock__gt=0)
