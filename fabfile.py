import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
try:
    django.setup()
except Exception as e:
    print("WARNING: Can't configure Django -- tasks depending on Django will fail:\n%s" % e)

from fabric.api import local
from fabric.decorators import task
from django.conf import settings

@task(alias='run')
def run_django():
    local("python3 manage.py runserver 0.0.0.0:8000")


@task
def test():
    local("pytest --fail-on-template-vars --cov --cov-report= ")

