# coding: utf-8
# Author: Chery Huo
from __future__ import absolute_import
import os
import json
from celery import Celery, platforms
from django.conf import settings
from celery.schedules import crontab

# from itmsp.utils.base import set_log, LOG_LEVEL
# from
# from itmsp import settings as i_settings
# settings.configure()
# from djcelery import models as celery_models

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'itmsp.settings')

# settings.configure()
# os.environ.update("DJANGO_SETTINGS_MODULE", "itmsp.settings")
# logger = set_log(LOG_LEVEL, filename='celery.log', logger_name='celery')
app = Celery("itmsp", broker=settings.CACHE_LOCATION + '/1')
# app = Celery("itmsp", broker="redis://localhost:6379/1") # 源代码
platforms.C_FORCE_ROOT = True  # 允许root用户执行

app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

CELERYBEAT_SCHEDULE = {
    'sync-network-one-day': {
        'task': 'ivmware.tasks.sync_network',
        'schedule': crontab(minute=0, hour=0),  # 每天执行一次
    }
}
CELERYBEAT_TIMEZONE = 'UTC'
app.conf.update(
    CELERY_RESULT_BACKEND=settings.CACHE_LOCATION + '/1',
    # CELERY_RESULT_BACKEND="localhost:6379/1", # 源代码
    CELERY_ACCEPT_CONTENT=['application/json'],
    CELERY_TASK_SERIALIZER='json',
    CELERY_RESULT_SERIALIZER='json',
    CELERYBEAT_SCHEDULER='djcelery.schedulers.DatabaseScheduler',
    CELERYBEAT_SCHEDULE=CELERYBEAT_SCHEDULE,
    CELERYBEAT_TIMEZONE=CELERYBEAT_TIMEZONE
)
