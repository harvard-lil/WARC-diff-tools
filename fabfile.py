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
def run_uwsgi():
    if settings.DEBUG is True:
        # allows terminal debugging
        local("uwsgi config/uwsgi.ini --honour-stdin")
    else:
        local("uwsgi config/uwsgi.ini")



# @task(alias='run')
# def run_django():
#     local("celery -A config worker -E -l info -P gevent")
#     local("python manage.py runserver 0.0.0.0:8082")

