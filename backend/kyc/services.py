from .models import AuditLog


def log_action(application, actor, action, detail=""):
    AuditLog.objects.create(
        application=application, actor=actor, action=action, detail=detail
    )
