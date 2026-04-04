import os
from datetime import timedelta

from celery import Celery
from celery.schedules import crontab
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("checkin")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "dispatch-scheduled-prompts": {
        "task": "apps.scheduled.tasks.dispatch_scheduled_prompts",
        "schedule": timedelta(hours=settings.PROMPT_INTERVAL_HOURS),
    },
    "expire-stale-sessions": {
        "task": "apps.scheduled.tasks.expire_stale_sessions",
        "schedule": crontab(minute=30),
    },
}
