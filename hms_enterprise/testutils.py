"""Shared helpers for the HMS test suite."""
from django.contrib.auth import get_user_model


def make_user(username, role="receptionist", password="Testpass123"):
    User = get_user_model()
    return User.objects.create_user(
        username=username,
        password=password,
        role=role,
        first_name=username.replace("_", " ").title(),
        is_active=True,
    )


def login_as(client, role="receptionist", username=None):
    username = username or f"test_{role}"
    user = make_user(username, role)
    client.force_login(user)
    return user
