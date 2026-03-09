"""
Celery configuration for BookVerse project.
"""

import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

app = Celery("bookverse")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()

# Periodic tasks
app.conf.beat_schedule = {
    "update-bestseller-list": {
        "task": "apps.catalog.tasks.update_bestseller_list",
        "schedule": crontab(hour=0, minute=0),  # Daily at midnight
    },
    "generate-recommendations": {
        "task": "apps.recommendations.tasks.generate_all_recommendations",
        "schedule": crontab(hour=2, minute=0),  # Daily at 2 AM
    },
    "send-reading-reminders": {
        "task": "apps.reading.tasks.send_reading_reminders",
        "schedule": crontab(hour=9, minute=0),  # Daily at 9 AM
    },
    "cleanup-abandoned-carts": {
        "task": "apps.orders.tasks.cleanup_abandoned_orders",
        "schedule": crontab(hour=3, minute=0),  # Daily at 3 AM
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task to verify Celery is working."""
    print(f"Request: {self.request!r}")
