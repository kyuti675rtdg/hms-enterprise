from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy

from .decorators import role_required
from .forms import UserCreateForm

User = get_user_model()


class HMSLoginView(LoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True


class HMSLogoutView(LogoutView):
    next_page = reverse_lazy("accounts:login")


@role_required("admin")
def user_list(request):
    users = User.objects.all().order_by("username")
    return render(request, "accounts/user_list.html", {"users": users})


@role_required("admin")
def user_create(request):
    if request.method == "POST":
        form = UserCreateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "User account created.")
            return redirect("accounts:user_list")
    else:
        form = UserCreateForm()
    return render(request, "accounts/user_form.html", {"form": form})
