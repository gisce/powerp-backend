from __future__ import absolute_import
import logging

from flask import Flask
from __init__ import Backend
from osconf import config_from_environment
from raven.contrib.flask import Sentry


application = Flask(__name__)
try:
    sentry = Sentry(application)
    sentry.captureMessage("Modul backend inicat", level=logging.INFO)
except Exception:
    pass
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
