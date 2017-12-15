import os

if os.environ.get('HEROKU'):
    from config.settings_heroku import *
    import dj_database_url
    DATABASES['default'] = dj_database_url.config(default=os.environ['DATABASE_URL'])
else:
    from config.settings_base import *

