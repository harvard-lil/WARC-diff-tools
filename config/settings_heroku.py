import os
import dj_database_url

DATABASES = {}

DATABASES['default'] = dj_database_url.config(default=os.environ['DATABASE_URL'])
