from django.urls import include, path

from . import views

app_name = "auditlog"

urlpatterns = [
    path("", views.event_list, name="event_list"),
]
