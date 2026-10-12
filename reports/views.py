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
    from scheduling.models import Doctor

    from .charts import area_chart, bars, donut, sparkline

    today = timezone.localdate()
    month_start = today.replace(day=1)

    # ---- KPI cards ------------------------------------------------------
    appt_total = Appointment.objects.count()
    new_patients_month = Patient.objects.filter(created_at__date__gte=month_start).count()
    beds_occupied = Bed.objects.filter(status=Bed.STATUS_OCCUPIED).count()
    beds_total = Bed.objects.count() or 1
    revenue_month = (
        Payment.objects.filter(paid_at__date__gte=month_start).aggregate(total=Sum("amount"))[
            "total"
        ]
        or Decimal("0")
    )

    # 14-day sparkline series
    days = [today - timedelta(days=i) for i in range(13, -1, -1)]
    appt_by_day = {
        r["day"]: r["n"]
        for r in Appointment.objects.filter(appt_date__gte=days[0])
        .annotate(day=TruncDate("appt_date"))
        .values("day")
        .annotate(n=Count("id"))
    }
    newpat_by_day = {
        r["day"]: r["n"]
        for r in Patient.objects.filter(created_at__date__gte=days[0])
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(n=Count("id"))
    }
    revenue_by_day = {
        r["day"]: float(r["total"] or 0)
        for r in Payment.objects.filter(paid_at__date__gte=days[0])
        .annotate(day=TruncDate("paid_at"))
        .values("day")
        .annotate(total=Sum("amount"))
    }
    spark_appt = [appt_by_day.get(d, 0) for d in days]
    spark_newpat = [newpat_by_day.get(d, 0) for d in days]
    spark_revenue = [revenue_by_day.get(d, 0) for d in days]

    kpis = [
        {
            "label": "Appointments",
            "value": f"{appt_total:,}",
            "icon": "calendar",
            "color": "#7c3aed",
            "spark": sparkline(spark_appt, "#7c3aed"),
            "link": "scheduling:appointment_list",
            "link_text": "View schedule",
        },
        {
            "label": "Beds occupied",
            "value": f"{beds_occupied}",
            "sub": f"of {beds_total}",
            "icon": "bed",
            "color": "#f59e0b",
            "donut": donut(beds_occupied / beds_total * 100, "#f59e0b", label="occupied"),
            "link": "wards:ward_list",
            "link_text": "Bed board",
        },
        {
            "label": "New patients",
            "value": f"{new_patients_month:,}",
            "sub": "this month",
            "icon": "users",
            "color": "#10b981",
            "spark": sparkline(spark_newpat, "#10b981"),
            "link": "patients:list",
            "link_text": "View patients",
        },
        {
            "label": "Revenue",
            "value": f"{float(revenue_month):,.0f}",
            "sub": "this month",
            "icon": "wallet",
            "color": "#3b82f6",
            "spark": sparkline(spark_revenue, "#3b82f6"),
            "link": "billing:invoice_list",
            "link_text": "View billing",
        },
    ]

    # ---- Hospital survey: last 6 months, new patients vs appointments ----
    months, m_newpat, m_appt = [], [], []
    for i in range(5, -1, -1):
        # step back i months from month_start
        y, mo = month_start.year, month_start.month - i
        while mo <= 0:
            mo += 12
            y -= 1
        m_start = month_start.replace(year=y, month=mo, day=1)
        m_end = (m_start + timedelta(days=32)).replace(day=1)
        months.append(m_start.strftime("%b"))
        m_newpat.append(
            Patient.objects.filter(
                created_at__date__gte=m_start, created_at__date__lt=m_end
            ).count()
        )
        m_appt.append(
            Appointment.objects.filter(appt_date__gte=m_start, appt_date__lt=m_end).count()
        )
    survey_svg = area_chart(
        months,
        [("New patients", "#3b82f6", m_newpat), ("Appointments", "#f59e0b", m_appt)],
    )

    # ---- Appointment summary + revenue bars ------------------------------
    appt_completed = Appointment.objects.filter(status=Appointment.STATUS_COMPLETED).count()
    appt_scheduled = Appointment.objects.filter(status=Appointment.STATUS_SCHEDULED).count()
    rev_labels = [d.strftime("%d %b") for d in days]
    revenue_svg = bars(spark_revenue, rev_labels, "#3b82f6")
    revenue_delta = ""
    if len(spark_revenue) >= 14:
        prev = sum(spark_revenue[:7]) or 1
        cur = sum(spark_revenue[7:])
        pct = (cur - prev) / prev * 100
        revenue_delta = f"{'+' if pct >= 0 else ''}{pct:.1f}%"

    # ---- Upcoming appointments table -------------------------------------
    upcoming = (
        Appointment.objects.select_related("patient", "doctor")
        .filter(appt_date__gte=today)
        .order_by("appt_date", "appt_time")[:8]
    )

    # ---- Doctor status ----------------------------------------------------
    doctors = Doctor.objects.filter(active=True).order_by("first_name", "last_name")[:6]

    context = {
        "kpis": kpis,
        "survey_svg": survey_svg,
        "appt_total": appt_total,
        "appt_completed": appt_completed,
        "appt_scheduled": appt_scheduled,
        "revenue_month": revenue_month,
        "revenue_delta": revenue_delta,
        "revenue_svg": revenue_svg,
        "upcoming": upcoming,
        "doctors": doctors,
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
