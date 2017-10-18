import os

# from django.core.wsgi import get_wsgi_application
# from gevent.monkey import patch_all; patch_all()
# import gevent.monkey
# gevent.monkey.patch_all(thread=False)
from pywb.apps.frontendapp import FrontEndApp
# from pywb.apps.rewriterapp import RewriterApp

# from pywb.warcserver.warcserver import WarcServer
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# application = get_wsgi_application()
# application = init_app(frontendapp, load_yaml=True, config_file=config_file)

application = FrontEndApp(config_file='config/config.yaml', custom_config={'debug': True})
print("DOES FILE EXIST?!", os.path.exists('config/config.yaml'))
print('application', dir(application))