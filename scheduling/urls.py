from django.urls import path

from . import views

app_name = "scheduling"

urlpatterns = [
    path("doctors/", views.doctor_list, name="doctor_list"),
    path("doctors/new/", views.doctor_create, name="doctor_create"),
    path("doctors/<int:pk>/edit/", views.doctor_edit, name="doctor_edit"),
    path("appointments/", views.appointment_list, name="appointment_list"),
    path("appointments/book/", views.appointment_book, name="appointment_book"),
    path(
        "appointments/<int:pk>/status/<str:status>/",
        views.appointment_status,
        name="appointment_status",
    ),
]
