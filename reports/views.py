import csv
from datetime import timedelta
from decimal import Decimal

from django.contrib import messages
from django.db.models import Count, Sum
from django.db.models.functions import TruncDate
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone

from accounts.decorators import role_required
from billing.models import Invoice, Payment
from patients.models import Patient
from pharmacy.models import Medicine, PharmacySale
from scheduling.models import Appointment
from wards.models import Bed

DASHBOARD_ROLES = ("admin", "doctor", "receptionist", "pharmacist", "labtech")
REPORT_ROLES = ("admin", "receptionist")


@role_required(*DASHBOARD_ROLES)
def dashboard(request):
    today = timezone.localdate()
    month_start = today.replace(day=1)

    kpis = {
        "patients": Patient.objects.count(),
        "appointments_today": Appointment.objects.filter(
            appt_date=today, status=Appointment.STATUS_SCHEDULED
        ).count(),
        "beds_occupied": Bed.objects.filter(status=Bed.STATUS_OCCUPIED).count(),
        "beds_total": Bed.objects.count(),
        "revenue_month": Payment.objects.filter(paid_at__date__gte=month_start).aggregate(
            total=Sum("amount")
        )["total"]
        or Decimal("0"),
    }
    todays_appointments = (
        Appointment.objects.select_related("patient", "doctor")
        .filter(appt_date=today)
        .order_by("appt_time")[:10]
    )
    low_stock = [m for m in Medicine.objects.all() if m.is_low_stock][:8]
    recent_invoices = Invoice.objects.select_related("patient").order_by("-created_at")[:8]

    # 14-day revenue for the SVG bar chart
    days = [today - timedelta(days=i) for i in range(13, -1, -1)]
    revenue_by_day = {
        row["day"]: row["total"]
        for row in (
            Payment.objects.filter(paid_at__date__gte=days[0])
            .annotate(day=TruncDate("paid_at"))
            .values("day")
            .annotate(total=Sum("amount"))
        )
    }
    chart = [
        {"label": d.strftime("%d %b"), "total": float(revenue_by_day.get(d, 0) or 0)}
        for d in days
    ]
    chart_max = max([c["total"] for c in chart] + [1])

    context = {
        "kpis": kpis,
        "todays_appointments": todays_appointments,
        "low_stock": low_stock,
        "recent_invoices": recent_invoices,
        "chart": chart,
        "chart_max": chart_max,
        "today": today,
    }
    return render(request, "reports/dashboard.html", context)


@role_required(*REPORT_ROLES)
def reports(request):
    today = timezone.localdate()
    month_start = today.replace(day=1)

    revenue_by_status = list(
        Invoice.objects.values("status").annotate(total=Sum("total"), count=Count("id"))
    )
    appts_per_doctor = list(
        Appointment.objects.filter(appt_date__gte=month_start)
        .values("doctor__first_name", "doctor__last_name", "doctor__specialization")
        .annotate(count=Count("id"))
        .order_by("-count")
    )
    top_medicines = list(
        PharmacySale.objects.values("medicine__name", "medicine__unit")
        .annotate(qty=Sum("quantity"), revenue=Sum("total"))
        .order_by("-qty")[:10]
    )
    outstanding = Invoice.objects.filter(
        status__in=[Invoice.STATUS_UNPAID, Invoice.STATUS_PARTIAL]
    ).aggregate(due=Sum("total"), paid=Sum("amount_paid"))

    context = {
        "revenue_by_status": revenue_by_status,
        "appts_per_doctor": appts_per_doctor,
        "top_medicines": top_medicines,
        "outstanding": outstanding,
        "month": month_start.strftime("%B %Y"),
    }
    return render(request, "reports/reports.html", context)


@role_required(*REPORT_ROLES)
def export_csv(request, kind):
    if kind == "revenue":
        rows = Invoice.objects.select_related("patient").order_by("-issue_date")
        header = ["invoice_no", "patient", "issue_date", "subtotal", "discount", "tax", "total", "amount_paid", "status"]
        data = [
            [i.invoice_no, i.patient.full_name, i.issue_date, i.subtotal, i.discount, i.tax, i.total, i.amount_paid, i.status]
            for i in rows
        ]
    elif kind == "appointments":
        rows = Appointment.objects.select_related("patient", "doctor").order_by("-appt_date")
        header = ["date", "time", "patient", "doctor", "status", "reason"]
        data = [
            [a.appt_date, a.appt_time, a.patient.full_name, str(a.doctor), a.status, a.reason]
            for a in rows
        ]
    elif kind == "medicines":
        rows = PharmacySale.objects.select_related("patient", "medicine").order_by("-sold_at")
        header = ["sold_at", "patient", "medicine", "quantity", "unit_price", "total"]
        data = [
            [s.sold_at, s.patient.full_name, s.medicine.name, s.quantity, s.unit_price, s.total]
            for s in rows
        ]
    else:
        messages.error(request, "Unknown export.")
        return redirect("reports:reports")

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="hms_{kind}.csv"'
    writer = csv.writer(response)
    writer.writerow(header)
    writer.writerows(data)
    return response
