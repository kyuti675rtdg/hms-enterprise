from django.urls import path

from . import views

app_name = "pharmacy"

urlpatterns = [
    path("", views.inventory, name="inventory"),
    path("new/", views.medicine_create, name="medicine_create"),
    path("<int:pk>/edit/", views.medicine_edit, name="medicine_edit"),
    path("dispense/", views.dispense, name="dispense"),
    path("sales/", views.sales_list, name="sales"),
]
