from django.apps import AppConfig


class ScheduledConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.scheduled"

    def ready(self):
        import apps.scheduled.handlers  # noqa: F401
