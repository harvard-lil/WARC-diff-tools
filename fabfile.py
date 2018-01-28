import os
import sys

import subprocess
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
try:
    django.setup()
except Exception as e:
    print("WARNING: Can't configure Django -- tasks depending on Django will fail:\n%s" % e)

from fabric.api import local
from fabric.decorators import task


@task(alias='run')
def run_django():
    celery_command = "celery -A config worker -E -l info -P gevent"
    subprocess.Popen(celery_command, shell=True, stdout=sys.stdout, stderr=sys.stderr)
    local("python manage.py runserver 0.0.0.0:8082")

