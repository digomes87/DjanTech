import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")


app = Celery("fintech")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@app.task(bind=True, ingnore_result=True)
def debug_tasl(self):
    print(f"Request: {self.request!r}")
