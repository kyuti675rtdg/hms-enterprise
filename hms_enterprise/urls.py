from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("reports.urls")),
    path("accounts/", include("accounts.urls")),
    path("patients/", include("patients.urls")),
    path("", include("scheduling.urls")),
    path("clinical/", include("clinical.urls")),
    path("pharmacy/", include("pharmacy.urls")),
    path("lab/", include("laboratory.urls")),
    path("billing/", include("billing.urls")),
    path("wards/", include("wards.urls")),
    path("audit/", include("auditlog.urls")),
]
