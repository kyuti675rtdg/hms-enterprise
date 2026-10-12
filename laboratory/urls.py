from django.urls import path

from . import views

app_name = "laboratory"

urlpatterns = [
    path("", views.order_list, name="order_list"),
    path("order/", views.order_create, name="order_create"),
    path("orders/<int:pk>/result/", views.result_entry, name="result_entry"),
    path("catalog/", views.catalog, name="catalog"),
    path("catalog/new/", views.test_create, name="test_create"),
    path("catalog/<int:pk>/edit/", views.test_edit, name="test_edit"),
]
