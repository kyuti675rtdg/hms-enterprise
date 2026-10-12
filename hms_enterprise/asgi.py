"""
ASGI config for hms_enterprise project.
"""
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hms_enterprise.settings")

application = get_asgi_application()
