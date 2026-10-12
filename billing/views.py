from decimal import Decimal, InvalidOperation

from django import forms
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.decorators import role_required
from patients.models import Patient

from .models import Invoice, InvoiceItem, Payment

BILLING_ROLES = ("admin", "receptionist", "pharmacist")


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ["amount", "method"]


@role_required(*BILLING_ROLES)
def invoice_list(request):
    invoices = Invoice.objects.select_related("patient")
    status = request.GET.get("status", "")
    if status:
        invoices = invoices.filter(status=status)
    aging = invoices.filter(status__in=[Invoice.STATUS_UNPAID, Invoice.STATUS_PARTIAL]).aggregate(
        total_due=Sum("total"), total_paid=Sum("amount_paid")
    )
    context = {
        "invoices": invoices[:200],
        "f_status": status,
        "statuses": Invoice.STATUS_CHOICES,
        "aging": aging,
    }
    return render(request, "billing/invoice_list.html", context)


@role_required("admin", "receptionist")
def invoice_create(request):
    patients = Patient.objects.all().order_by("first_name")
    if request.method == "POST":
        patient = get_object_or_404(Patient, pk=request.POST.get("patient"))
        descriptions = request.POST.getlist("description[]")
        quantities = request.POST.getlist("quantity[]")
        unit_prices = request.POST.getlist("unit_price[]")
        items = []
        subtotal = Decimal("0")
        for desc, qty, price in zip(descriptions, quantities, unit_prices):
            desc = desc.strip()
            if not desc:
                continue
            try:
                qty_d = Decimal(qty or "1")
                price_d = Decimal(price or "0")
            except InvalidOperation:
                continue
            if qty_d <= 0 or price_d < 0:
                continue
            line_total = qty_d * price_d
            items.append((desc, qty_d, price_d, line_total))
            subtotal += line_total
        if not items:
            messages.error(request, "Add at least one valid line item.")
            return render(request, "billing/invoice_form.html", {"patients": patients})
        try:
            discount = Decimal(request.POST.get("discount") or "0")
            tax = Decimal(request.POST.get("tax") or "0")
        except InvalidOperation:
            discount, tax = Decimal("0"), Decimal("0")
        total = subtotal - discount + tax
        if total < 0:
            messages.error(request, "Total cannot be negative.")
            return render(request, "billing/invoice_form.html", {"patients": patients})
        with transaction.atomic():
            invoice = Invoice.objects.create(
                patient=patient,
                subtotal=subtotal,
                discount=discount,
                tax=tax,
                total=total,
                created_by=request.user,
            )
            for desc, qty_d, price_d, line_total in items:
                InvoiceItem.objects.create(
                    invoice=invoice,
                    description=desc,
                    quantity=qty_d,
                    unit_price=price_d,
                    line_total=line_total,
                )
        messages.success(request, f"Invoice {invoice.invoice_no} created.")
        return redirect("billing:invoice_detail", pk=invoice.pk)
    return render(request, "billing/invoice_form.html", {"patients": patients})


@role_required(*BILLING_ROLES)
def invoice_detail(request, pk):
    invoice = get_object_or_404(
        Invoice.objects.select_related("patient").prefetch_related("items", "payments"),
        pk=pk,
    )
    return render(
        request, "billing/invoice_detail.html", {"invoice": invoice, "pay_form": PaymentForm()}
    )


@role_required("admin", "receptionist")
def record_payment(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    if request.method == "POST":
        form = PaymentForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data["amount"]
            if amount <= 0:
                messages.error(request, "Payment amount must be positive.")
            elif amount > invoice.balance:
                messages.error(
                    request,
                    f"Overpayment blocked: invoice balance is {invoice.balance}.",
                )
            else:
                with transaction.atomic():
                    inv = Invoice.objects.select_for_update().get(pk=invoice.pk)
                    if amount > inv.balance:
                        messages.error(
                            request,
                            f"Overpayment blocked: invoice balance is {inv.balance}.",
                        )
                        return redirect("billing:invoice_detail", pk=invoice.pk)
                    Payment.objects.create(
                        invoice=inv,
                        amount=amount,
                        method=form.cleaned_data["method"],
                        received_by=request.user,
                    )
                    inv.amount_paid += amount
                    inv.refresh_status()
                    inv.save(update_fields=["amount_paid", "status"])
                messages.success(request, f"Payment of {amount} recorded.")
    return redirect("billing:invoice_detail", pk=invoice.pk)


@role_required(*BILLING_ROLES)
def receipt(request, pk):
    invoice = get_object_or_404(
        Invoice.objects.select_related("patient").prefetch_related("items", "payments"),
        pk=pk,
    )
    return render(request, "billing/receipt.html", {"invoice": invoice, "now": timezone.now()})
