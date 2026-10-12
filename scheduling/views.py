from django.contrib import messages
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.decorators import role_required

from .forms import AppointmentForm, DoctorForm
from .models import Appointment, Doctor

APPT_VIEW_ROLES = ("admin", "doctor", "receptionist")
APPT_EDIT_ROLES = ("admin", "receptionist")


# ---------------- Doctors (admin only) ----------------
@role_required("admin")
def doctor_list(request):
    doctors = Doctor.objects.all()
    return render(request, "scheduling/doctor_list.html", {"doctors": doctors})


@role_required("admin")
def doctor_create(request):
    if request.method == "POST":
        form = DoctorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Doctor added.")
            return redirect("scheduling:doctor_list")
    else:
        form = DoctorForm()
    return render(request, "scheduling/doctor_form.html", {"form": form, "title": "Add Doctor"})


@role_required("admin")
def doctor_edit(request, pk):
    doctor = get_object_or_404(Doctor, pk=pk)
    if request.method == "POST":
        form = DoctorForm(request.POST, instance=doctor)
        if form.is_valid():
            form.save()
            messages.success(request, "Doctor updated.")
            return redirect("scheduling:doctor_list")
    else:
        form = DoctorForm(instance=doctor)
    return render(request, "scheduling/doctor_form.html", {"form": form, "title": "Edit Doctor"})


# ---------------- Appointments ----------------
@role_required(*APPT_VIEW_ROLES)
def appointment_list(request):
    appts = Appointment.objects.select_related("patient", "doctor")
    day = request.GET.get("date", "")
    doctor_id = request.GET.get("doctor", "")
    status = request.GET.get("status", "")
    if day:
        appts = appts.filter(appt_date=day)
    if doctor_id:
        appts = appts.filter(doctor_id=doctor_id)
    if status:
        appts = appts.filter(status=status)
    context = {
        "appointments": appts[:200],
        "doctors": Doctor.objects.filter(active=True),
        "statuses": Appointment.STATUS_CHOICES,
        "f_date": day,
        "f_doctor": doctor_id,
        "f_status": status,
        "today": timezone.localdate().isoformat(),
    }
    return render(request, "scheduling/appointment_list.html", context)


@role_required(*APPT_EDIT_ROLES)
def appointment_book(request):
    if request.method == "POST":
        form = AppointmentForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    appt = form.save(commit=False)
                    appt.created_by = request.user
                    appt.save()
            except IntegrityError:
                form.add_error(
                    "appt_time",
                    "This slot was just taken. Please choose another time.",
                )
            else:
                messages.success(request, "Appointment booked.")
                return redirect("scheduling:appointment_list")
    else:
        form = AppointmentForm()
    return render(request, "scheduling/appointment_form.html", {"form": form})


@role_required(*APPT_EDIT_ROLES)
def appointment_status(request, pk, status):
    appt = get_object_or_404(Appointment, pk=pk)
    valid = dict(Appointment.STATUS_CHOICES)
    if status not in valid:
        messages.error(request, "Invalid status.")
        return redirect("scheduling:appointment_list")
    if request.method == "POST":
        try:
            with transaction.atomic():
                appt.status = status
                appt.save(update_fields=["status"])
        except IntegrityError:
            messages.error(
                request,
                "Cannot re-schedule: the doctor already has an appointment at that slot.",
            )
        else:
            messages.success(request, f"Appointment marked as {valid[status].lower()}.")
    return redirect("scheduling:appointment_list")
