from decimal import Decimal

from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from accounts.decorators import role_required
from billing.models import Invoice, InvoiceItem

from .forms import DispenseForm, MedicineForm
from .models import Medicine, PharmacySale

PHARM_ROLES = ("admin", "pharmacist")


@role_required(*PHARM_ROLES)
def inventory(request):
    q = request.GET.get("q", "").strip()
    medicines = Medicine.objects.all()
    if q:
        medicines = medicines.filter(name__icontains=q)
    low_only = request.GET.get("low") == "1"
    if low_only:
        medicines = [m for m in medicines if m.is_low_stock]
    return render(
        request,
        "pharmacy/inventory.html",
        {"medicines": medicines, "q": q, "low_only": low_only},
    )


@role_required(*PHARM_ROLES)
def medicine_create(request):
    if request.method == "POST":
        form = MedicineForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Medicine added to inventory.")
            return redirect("pharmacy:inventory")
    else:
        form = MedicineForm()
    return render(request, "pharmacy/medicine_form.html", {"form": form, "title": "Add Medicine"})


@role_required(*PHARM_ROLES)
def medicine_edit(request, pk):
    medicine = get_object_or_404(Medicine, pk=pk)
    if request.method == "POST":
        form = MedicineForm(request.POST, instance=medicine)
        if form.is_valid():
            form.save()
            messages.success(request, "Medicine updated.")
            return redirect("pharmacy:inventory")
    else:
        form = MedicineForm(instance=medicine)
    return render(
        request, "pharmacy/medicine_form.html", {"form": form, "title": f"Edit {medicine.name}"}
    )


@role_required(*PHARM_ROLES)
def dispense(request):
    """Dispense medicine: atomic stock decrement + auto-created unpaid invoice."""
    if request.method == "POST":
        form = DispenseForm(request.POST)
        if form.is_valid():
            patient = form.cleaned_data["patient"]
            quantity = form.cleaned_data["quantity"]
            try:
                with transaction.atomic():
                    medicine = Medicine.objects.select_for_update().get(
                        pk=form.cleaned_data["medicine"].pk
                    )
                    if quantity > medicine.quantity_in_stock:
                        raise ValueError(
                            f"Only {medicine.quantity_in_stock} {medicine.unit} available."
                        )
                    medicine.quantity_in_stock -= quantity
                    medicine.save(update_fields=["quantity_in_stock"])
                    total = medicine.unit_price * Decimal(quantity)
                    PharmacySale.objects.create(
                        patient=patient,
                        medicine=medicine,
                        quantity=quantity,
                        unit_price=medicine.unit_price,
                        total=total,
                        sold_by=request.user,
                    )
                    invoice = Invoice.objects.create(
                        patient=patient,
                        subtotal=total,
                        total=total,
                        created_by=request.user,
                    )
                    InvoiceItem.objects.create(
                        invoice=invoice,
                        description=f"{medicine.name} × {quantity} {medicine.unit}",
                        quantity=Decimal(quantity),
                        unit_price=medicine.unit_price,
                        line_total=total,
                    )
            except ValueError as exc:
                messages.error(request, str(exc))
            except Medicine.DoesNotExist:
                messages.error(request, "Selected medicine no longer exists.")
            else:
                messages.success(
                    request,
                    f"Dispensed {quantity}× {medicine.name}. Invoice {invoice.invoice_no} created.",
                )
                return redirect("pharmacy:sales")
    else:
        form = DispenseForm()
    return render(request, "pharmacy/dispense.html", {"form": form})


@role_required(*PHARM_ROLES)
def sales_list(request):
    sales = PharmacySale.objects.select_related("patient", "medicine", "sold_by")[:200]
    return render(request, "pharmacy/sales.html", {"sales": sales})
