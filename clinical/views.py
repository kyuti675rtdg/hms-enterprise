from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import role_required
from patients.models import Patient

from .forms import MedicalRecordForm
from .models import MedicalRecord

CLINICAL_ROLES = ("admin", "doctor")


@role_required(*CLINICAL_ROLES)
def record_list(request):
    records = MedicalRecord.objects.select_related("patient", "doctor")[:200]
    return render(request, "clinical/record_list.html", {"records": records})


@role_required(*CLINICAL_ROLES)
def record_create(request, patient_pk):
    patient = get_object_or_404(Patient, pk=patient_pk)
    if request.method == "POST":
        form = MedicalRecordForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            record.created_by = request.user
            record.save()
            messages.success(request, "Medical record saved.")
            return redirect("patients:detail", pk=patient.pk)
    else:
        form = MedicalRecordForm(initial={"patient": patient})
    return render(request, "clinical/record_form.html", {"form": form, "patient": patient})


@role_required(*CLINICAL_ROLES)
def record_detail(request, pk):
    record = get_object_or_404(
        MedicalRecord.objects.select_related("patient", "doctor"), pk=pk
    )
    return render(request, "clinical/record_detail.html", {"record": record})
