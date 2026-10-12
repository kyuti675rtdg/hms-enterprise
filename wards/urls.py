from django.urls import path

from . import views

app_name = "wards"

urlpatterns = [
    path("", views.ward_list, name="ward_list"),
    path("<int:pk>/", views.ward_detail, name="ward_detail"),
    path("beds/<int:pk>/status/", views.bed_status, name="bed_status"),
    path("admissions/new/", views.admission_create, name="admission_create"),
    path("admissions/<int:pk>/discharge/", views.discharge, name="discharge"),
]
