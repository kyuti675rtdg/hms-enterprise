"""Role-filtered sidebar navigation for the base layout."""


def _item(label, url_name, icon, roles):
    return {"label": label, "url_name": url_name, "icon": icon, "roles": roles}


NAV = [
    _item("Dashboard", "dashboard", "grid", ("admin", "doctor", "receptionist", "pharmacist", "labtech")),
    _item("Patients", "patients:list", "users", ("admin", "doctor", "receptionist", "pharmacist", "labtech")),
    _item("Appointments", "scheduling:appointment_list", "calendar", ("admin", "doctor", "receptionist")),
    _item("Doctors", "scheduling:doctor_list", "stethoscope", ("admin", "receptionist")),
    _item("Medical Records", "clinical:record_list", "clipboard", ("admin", "doctor")),
    _item("Pharmacy", "pharmacy:inventory", "pill", ("admin", "pharmacist")),
    _item("Laboratory", "laboratory:order_list", "flask", ("admin", "doctor", "labtech")),
    _item("Billing", "billing:invoice_list", "receipt", ("admin", "receptionist", "pharmacist")),
    _item("Wards & Beds", "wards:ward_list", "bed", ("admin", "doctor", "receptionist")),
    _item("Reports", "reports:reports", "chart", ("admin", "receptionist")),
    _item("Audit Log", "auditlog:event_list", "shield", ("admin",)),
    _item("Users", "accounts:user_list", "key", ("admin",)),
]


def nav_items(request):
    user = getattr(request, "user", None)
    role = getattr(user, "role", None) if user and user.is_authenticated else None
    items = [i for i in NAV if role in i["roles"]] if role else []
    return {"nav_items": items}
