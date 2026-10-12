from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.decorators import role_required

from .forms import LabOrderForm, LabResultForm, LabTestForm
from .models import LabOrder, LabTest

LAB_VIEW_ROLES = ("admin", "doctor", "labtech")
LAB_ADMIN_ROLES = ("admin",)


@role_required(*LAB_VIEW_ROLES)
def order_list(request):
    orders = LabOrder.objects.select_related("patient", "test", "ordered_by")
    status = request.GET.get("status", "")
    if status:
        orders = orders.filter(status=status)
    return render(
        request,
        "laboratory/order_list.html",
        {"orders": orders[:200], "f_status": status, "statuses": LabOrder.STATUS_CHOICES},
    )


@role_required("admin", "labtech", "doctor", "receptionist")
def order_create(request):
    if request.method == "POST":
        form = LabOrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.ordered_by = request.user
            order.save()
            messages.success(request, f"Lab test '{order.test.name}' ordered.")
            return redirect("laboratory:order_list")
    else:
        form = LabOrderForm()
    return render(request, "laboratory/order_form.html", {"form": form})


@role_required("admin", "labtech")
def result_entry(request, pk):
    order = get_object_or_404(LabOrder, pk=pk)
    if request.method == "POST":
        form = LabResultForm(request.POST, instance=order)
        if form.is_valid():
            order = form.save(commit=False)
            order.status = LabOrder.STATUS_COMPLETED
            order.completed_at = timezone.now()
            order.save()
            messages.success(request, "Result recorded; order marked completed.")
            return redirect("laboratory:order_list")
    else:
        form = LabResultForm(instance=order)
    return render(request, "laboratory/result_form.html", {"form": form, "order": order})


@role_required(*LAB_VIEW_ROLES)
def catalog(request):
    tests = LabTest.objects.all()
    return render(request, "laboratory/catalog.html", {"tests": tests})


@role_required(*LAB_ADMIN_ROLES)
def test_create(request):
    if request.method == "POST":
        form = LabTestForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Lab test added.")
            return redirect("laboratory:catalog")
    else:
        form = LabTestForm()
    return render(request, "laboratory/test_form.html", {"form": form, "title": "Add Lab Test"})


@role_required(*LAB_ADMIN_ROLES)
def test_edit(request, pk):
    test = get_object_or_404(LabTest, pk=pk)
    if request.method == "POST":
        form = LabTestForm(request.POST, instance=test)
        if form.is_valid():
            form.save()
            messages.success(request, "Lab test updated.")
            return redirect("laboratory:catalog")
    else:
        form = LabTestForm(instance=test)
    return render(request, "laboratory/test_form.html", {"form": form, "title": f"Edit {test.name}"})
