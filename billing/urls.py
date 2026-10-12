from django.urls import path

from . import views

app_name = "billing"

urlpatterns = [
    path("", views.invoice_list, name="invoice_list"),
    path("new/", views.invoice_create, name="invoice_create"),
    path("<int:pk>/", views.invoice_detail, name="invoice_detail"),
    path("<int:pk>/pay/", views.record_payment, name="record_payment"),
    path("<int:pk>/receipt/", views.receipt, name="receipt"),
]
