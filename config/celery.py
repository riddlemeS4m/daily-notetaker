import os
from datetime import timedelta

from celery import Celery
from celery.schedules import crontab
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery(settings.PROJECT_NAME)
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@app.on_after_finalize.connect
def setup_beat_schedule(sender, **kwargs):
    from apps.scheduled.handlers.schedule_handler import ScheduleHandler

    sender.conf.beat_schedule = {
        "dispatch-scheduled-prompts": {
            "task": "apps.scheduled.tasks.dispatch_scheduled_prompts",
            "schedule": timedelta(hours=ScheduleHandler.PROMPT_INTERVAL_HOURS),
        },
        "expire-stale-sessions": {
            "task": "apps.scheduled.tasks.expire_stale_sessions",
            "schedule": crontab(minute=30),
        },
        "close-end-of-day-sessions": {
            "task": "apps.core.tasks.close_end_of_day_sessions",
            "schedule": crontab(hour=8, minute=0),
        },
    }
