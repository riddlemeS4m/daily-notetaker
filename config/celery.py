import os

from celery import Celery
from celery.schedules import crontab
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery(settings.PROJECT_NAME)
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@app.on_after_finalize.connect
def setup_beat_schedule(sender, **kwargs):
    sender.conf.beat_schedule = {
        "dispatch-due-jobs": {
            "task": "apps.scheduled.tasks.dispatch_due_jobs_task",
            "schedule": crontab(),  # every minute
        },
        "close-end-of-day-sessions": {
            "task": "apps.core.tasks.close_end_of_day_sessions_task",
            "schedule": crontab(hour=8, minute=0),
        },
    }
