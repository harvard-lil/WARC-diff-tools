import os
from config.settings_base import *

SECRET_KEY = "123"

if os.environ.get('HEROKU'):
    print("heroku!")
    from config.settings_heroku import *
    import dj_database_url
    DATABASES['default'] = dj_database_url.config(default=os.environ['DATABASE_URL'])

