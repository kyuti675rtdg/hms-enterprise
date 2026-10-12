from django.contrib import messages
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import role_required

from .forms import PatientForm
from .models import Patient

VIEW_ROLES = ("admin", "doctor", "receptionist", "pharmacist", "labtech")
EDIT_ROLES = ("admin", "receptionist")


@role_required(*VIEW_ROLES)
def patient_list(request):
    q = request.GET.get("q", "").strip()
    patients = Patient.objects.all()
    if q:
        vector = SearchVector("first_name", "last_name", "phone", "patient_no", config="english")
        query = SearchQuery(q, config="english")
        patients = (
            patients.annotate(rank=SearchRank(vector, query))
            .filter(rank__gte=0.01)
            .order_by("-rank")
        )
    patients = patients[:100]
    if request.headers.get("HX-Request"):
        return render(request, "patients/_rows.html", {"patients": patients})
    return render(request, "patients/list.html", {"patients": patients, "q": q})


@role_required(*EDIT_ROLES)
def patient_create(request):
    if request.method == "POST":
        form = PatientForm(request.POST)
        if form.is_valid():
            patient = form.save()
            messages.success(request, f"Patient {patient.patient_no} registered.")
            return redirect("patients:detail", pk=patient.pk)
    else:
        form = PatientForm()
    return render(request, "patients/form.html", {"form": form, "title": "Register Patient"})


@role_required(*VIEW_ROLES)
def patient_detail(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    context = {
        "patient": patient,
        "records": patient.medical_records.select_related("doctor")[:10],
        "appointments": patient.appointments.select_related("doctor")[:10],
        "invoices": patient.invoices.all()[:10],
        "lab_orders": patient.lab_orders.select_related("test")[:10],
        "admissions": patient.admissions.select_related("bed__ward")[:10],
    }
    return render(request, "patients/detail.html", context)


@role_required(*EDIT_ROLES)
def patient_edit(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    if request.method == "POST":
        form = PatientForm(request.POST, instance=patient)
        if form.is_valid():
            form.save()
            messages.success(request, "Patient record updated.")
            return redirect("patients:detail", pk=patient.pk)
    else:
        form = PatientForm(instance=patient)
    return render(
        request, "patients/form.html", {"form": form, "title": f"Edit {patient.patient_no}"}
    )
