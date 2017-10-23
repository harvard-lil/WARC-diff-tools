import os

from werkzeug.wsgi import DispatcherMiddleware
from django.core.wsgi import get_wsgi_application

from pywb.apps.frontendapp import FrontEndApp

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# application = DispatcherMiddleware(
#     get_wsgi_application(),
#     {
#         '/archives': FrontEndApp(
#             config_file='config/config.yaml',
#             custom_config={'debug': True}),
#     }
# )


application = FrontEndApp(config_file='config/config.yaml', custom_config={'debug': True})