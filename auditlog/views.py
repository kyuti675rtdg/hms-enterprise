from django.shortcuts import render

from accounts.decorators import role_required

from .models import AuditEvent


@role_required("admin")
def event_list(request):
    model_filter = request.GET.get("model", "")
    events = AuditEvent.objects.select_related("actor")
    if model_filter:
        events = events.filter(model_name__icontains=model_filter)
    events = events[:200]
    return render(
        request,
        "auditlog/event_list.html",
        {"events": events, "model_filter": model_filter},
    )
