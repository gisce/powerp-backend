from flask import Flask
from flask_testing import TestCase
from . import Backend
from backend_blueprint import backend
import unittest


class SearchTest(TestCase):
    def create_app(self):
        app = Flask(__name__)
        Backend(app, '')
        app.register_blueprint(backend, url_prefix='')
        app.config['TESTING'] = True
        return app

if __name__ == '__main__':
    unittest.main()
