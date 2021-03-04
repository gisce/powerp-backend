from __future__ import absolute_import
import logging

from flask import Flask
from __init__ import Backend
from osconf import config_from_environment
from raven.contrib.flask import Sentry

try:
    # Due: https://www.python.org/dev/peps/pep-0476
    import ssl
    try:
        _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:
        # Legacy Python that doesn't verify HTTPS certificates by default
        pass
    else:
        # Handle target environment that doesn't support HTTPS verification
        ssl._create_default_https_context = _create_unverified_https_context
except ImportError:
    pass

application = Flask(__name__)
sentry = Sentry(application)
sentry.captureMessage("Modul backend inicat", level=logging.INFO)
Backend(application, url_prefix='/')

required = [
    'openerp_server',
    'openerp_database',
]
config = config_from_environment('BACKEND', required, session_cookie_name=None)
for k, v in config.items():
    k = k.upper()
    print('CONFIG: {0}: {1}'.format(k, v))
    if v is not None:
        application.config[k] = v
if __name__ == "__main__":
    application.run(host='0.0.0.0', debug=True)
