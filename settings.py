import os
from config.settings import *
DECOMPRESS = True

try:
    if os.environ['HEROKU']:
        from config.settings_heroku import *
except KeyError:
    pass
