from django.urls import path

from . import views

app_name = "clinical"

urlpatterns = [
    path("records/", views.record_list, name="record_list"),
    path("records/<int:pk>/", views.record_detail, name="record_detail"),
    path("patients/<int:patient_pk>/records/new/", views.record_create, name="record_create"),
]
