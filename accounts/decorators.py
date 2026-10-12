"""Role-based access control helpers."""
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


def role_required(*roles):
    """Require the logged-in user to have one of the given roles.

    Anonymous users are redirected to the login page; authenticated users
    with the wrong role get a 403.
    """

    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped(request, *args, **kwargs):
            if request.user.role not in roles:
                raise PermissionDenied
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator


ALL_ROLES = ("admin", "doctor", "receptionist", "pharmacist", "labtech")
