from __future__ import absolute_import

from backend_blueprint import backend


class Backend(object):
    def __init__(self, app=None, url_prefix='/backend'):
        self.url_prefix = url_prefix
        if app is not None:
            self.app = app
            self.init_app(app)
        else:
            self.app = None

    def init_app(self, app):
        app.register_blueprint(backend, url_prefix=self.url_prefix)
        app.extensions['backend'] = self
