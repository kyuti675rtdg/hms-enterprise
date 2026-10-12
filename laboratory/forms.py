from django import forms

from .models import LabOrder, LabTest


class LabTestForm(forms.ModelForm):
    class Meta:
        model = LabTest
        fields = ["name", "category", "price"]


class LabOrderForm(forms.ModelForm):
    class Meta:
        model = LabOrder
        fields = ["patient", "test"]
        widgets = {"result_text": forms.Textarea(attrs={"rows": 4})}


class LabResultForm(forms.ModelForm):
    class Meta:
        model = LabOrder
        fields = ["result_text"]
        widgets = {"result_text": forms.Textarea(attrs={"rows": 6})}
