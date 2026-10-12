"""Audit signals: record create/update/delete with field diffs as JSON."""
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from .middleware import get_current_request, get_current_user
from .models import AuditEvent

# Models under audit. Imported lazily inside ready() to avoid circulars.
TRACKED = [
    ("patients", "Patient"),
    ("scheduling", "Appointment"),
    ("pharmacy", "Medicine"),
    ("pharmacy", "PharmacySale"),
    ("billing", "Invoice"),
    ("billing", "Payment"),
    ("wards", "Admission"),
]

# (model_label, pk) -> {field: old_value} snapshot taken in pre_save.
_old_values = {}


def _model_label(instance):
    return f"{instance._meta.app_label}.{instance._meta.model_name}"


def _serializable(value):
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _field_dict(instance):
    data = {}
    for field in instance._meta.fields:
        try:
            data[field.name] = _serializable(getattr(instance, field.name))
        except Exception:
            data[field.name] = None
    # Replace raw FK ids with a readable repr where cheap.
    return data


def _get_client_ip(request):
    if request is None:
        return None
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def _register():
    from django.apps import apps

    for app_label, model_name in TRACKED:
        model = apps.get_model(app_label, model_name)

        def make_pre(m):
            @receiver(pre_save, sender=m, weak=False)
            def _pre_save(sender, instance, **kwargs):
                key = (_model_label(instance), instance.pk)
                if instance.pk:
                    try:
                        old = sender.objects.get(pk=instance.pk)
                        _old_values[key] = _field_dict(old)
                    except sender.DoesNotExist:
                        _old_values.pop(key, None)

            return _pre_save

        def make_post(m):
            @receiver(post_save, sender=m, weak=False)
            def _post_save(sender, instance, created, **kwargs):
                key = (_model_label(instance), instance.pk)
                old = _old_values.pop(key, {})
                new = _field_dict(instance)
                if created:
                    action = AuditEvent.ACTION_CREATE
                    diff = new
                else:
                    action = AuditEvent.ACTION_UPDATE
                    diff = {
                        k: {"old": old.get(k), "new": v}
                        for k, v in new.items()
                        if old.get(k) != v
                    }
                if action == AuditEvent.ACTION_UPDATE and not diff:
                    return  # nothing actually changed
                _write_event(instance, action, diff)

            @receiver(post_delete, sender=m, weak=False)
            def _post_delete(sender, instance, **kwargs):
                _write_event(instance, AuditEvent.ACTION_DELETE, {})

            return _post_save

        make_pre(model)
        make_post(model)


def _write_event(instance, action, diff):
    request = get_current_request()
    try:
        AuditEvent.objects.create(
            actor=get_current_user(),
            action=action,
            model_name=_model_label(instance),
            object_id=str(instance.pk),
            object_repr=str(instance)[:255],
            diff=diff,
            ip_address=_get_client_ip(request),
        )
    except Exception:
        # Auditing must never break the primary write.
        pass


_register()
