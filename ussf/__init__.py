from __future__ import absolute_import, unicode_literals

# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
from .celery import app as celery_app
import os
from django.conf import settings

__all__ = ['celery_app']

if not os.path.exists(settings.LOG_DIR):
    os.mkdir(settings.LOG_DIR)
