import os
import dj_database_url

SECRET_KEY = os.environ.get('SECRET_KEY')

DATABASES = {
    'default': dj_database_url.config(default=os.environ['DATABASE_URL']),
}

BASE_URL = os.environ.get('BASE_URL')
DEBUG = os.environ.get('DEBUG')
PROTOCOL = os.environ.get('PROTOCOL')