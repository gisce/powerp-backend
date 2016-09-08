from __future__ import absolute_import
from flask import Flask
from flask_testing import TestCase
from __init__ import Backend
from backend_blueprint import backend
from osconf import config_from_environment
import unittest


class BackendTest(TestCase):
    def create_app(self):
        conf = config_from_environment('TEST', ['secret'])
        app = Flask(__name__)
        Backend(app, '/')
        #app.register_blueprint(backend, url_prefix='')
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = conf['secret']
        return app

    def test_token(self):
        response = self.client.get('/token')


if __name__ == '__main__':
    unittest.main()
