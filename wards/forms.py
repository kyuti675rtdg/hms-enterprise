from django import forms

from .models import Admission, Bed


class AdmissionForm(forms.ModelForm):
    ward = forms.ModelChoiceField(
        queryset=None, label="Ward", required=True, empty_label="Select ward"
    )

    class Meta:
        model = Admission
        fields = ["patient", "doctor", "diagnosis"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from .models import Ward

        self.fields["ward"].queryset = Ward.objects.all()
        self.fields["doctor"].required = False


class BedForm(forms.ModelForm):
    class Meta:
        model = Bed
        fields = ["status"]
