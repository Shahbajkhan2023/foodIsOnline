import os
import celery


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'foodOnline_main.settings')

app = celery.Celery('foodOnline_main')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
