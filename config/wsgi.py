import os
from werkzeug.wsgi import DispatcherMiddleware

from django.core.wsgi import get_wsgi_application
from django.conf import settings

from pywb.apps.frontendapp import FrontEndApp
from dashboard.handler import WSHandler
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")


application = DispatcherMiddleware(
    get_wsgi_application(),
    {
        '/websocket': WSHandler,
        settings.ARCHIVES_ROUTE: FrontEndApp(
            config_file='config/config.yaml',
            custom_config={'debug': True}),
    }
)