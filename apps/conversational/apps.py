from django.apps import AppConfig


class ConversationalConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.conversational"

    def ready(self):
        import apps.conversational.handlers  # noqa: F401
