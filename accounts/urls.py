from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.HMSLoginView.as_view(), name="login"),
    path("logout/", views.HMSLogoutView.as_view(), name="logout"),
    path("users/", views.user_list, name="user_list"),
    path("users/new/", views.user_create, name="user_create"),
]
