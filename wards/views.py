from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.decorators import role_required

from .forms import AdmissionForm, BedForm
from .models import Admission, Bed, Ward

WARD_ROLES = ("admin", "doctor", "receptionist")
ADMIT_ROLES = ("admin", "receptionist")


@role_required(*WARD_ROLES)
def ward_list(request):
    wards = Ward.objects.prefetch_related("beds").all()
    return render(request, "wards/ward_list.html", {"wards": wards})


@role_required(*WARD_ROLES)
def ward_detail(request, pk):
    ward = get_object_or_404(Ward.objects.prefetch_related("beds"), pk=pk)
    return render(request, "wards/ward_detail.html", {"ward": ward})


@role_required(*ADMIT_ROLES)
def admission_create(request):
    if request.method == "POST":
        form = AdmissionForm(request.POST)
        bed_id = request.POST.get("bed")
        if form.is_valid() and bed_id:
            try:
                with transaction.atomic():
                    bed = Bed.objects.select_for_update().get(pk=bed_id)
                    if bed.status != Bed.STATUS_AVAILABLE:
                        raise ValueError("That bed is no longer available.")
                    bed.status = Bed.STATUS_OCCUPIED
                    bed.save(update_fields=["status"])
                    admission = form.save(commit=False)
                    admission.bed = bed
                    admission.admitted_by = request.user
                    admission.save()
            except (Bed.DoesNotExist, ValueError) as exc:
                messages.error(request, str(exc))
            else:
                messages.success(
                    request, f"Patient admitted to {bed.ward.name}, bed {bed.bed_no}."
                )
                return redirect("wards:ward_detail", pk=bed.ward.pk)
        elif not bed_id:
            messages.error(request, "Please select an available bed.")
    else:
        form = AdmissionForm()
    return render(request, "wards/admission_form.html", {"form": form})


@role_required(*ADMIT_ROLES)
def discharge(request, pk):
    admission = get_object_or_404(Admission, pk=pk, status=Admission.STATUS_ADMITTED)
    if request.method == "POST":
        with transaction.atomic():
            adm = Admission.objects.select_for_update().get(pk=admission.pk)
            bed = Bed.objects.select_for_update().get(pk=adm.bed.pk)
            adm.status = Admission.STATUS_DISCHARGED
            adm.discharge_date = timezone.localdate()
            adm.save(update_fields=["status", "discharge_date"])
            bed.status = Bed.STATUS_AVAILABLE
            bed.save(update_fields=["status"])
        messages.success(request, f"Patient discharged; bed {bed.bed_no} is now available.")
        return redirect("wards:ward_detail", pk=bed.ward.pk)
    return render(request, "wards/discharge_confirm.html", {"admission": admission})


@role_required("admin")
def bed_status(request, pk):
    bed = get_object_or_404(Bed, pk=pk)
    if request.method == "POST":
        form = BedForm(request.POST, instance=bed)
        if form.is_valid():
            if bed.status == Bed.STATUS_OCCUPIED and form.cleaned_data["status"] != Bed.STATUS_OCCUPIED:
                messages.error(request, "Cannot change status of an occupied bed directly; discharge the patient first.")
            else:
                form.save()
                messages.success(request, f"Bed {bed.bed_no} marked as {bed.get_status_display().lower()}.")
    return redirect("wards:ward_detail", pk=bed.ward.pk)
