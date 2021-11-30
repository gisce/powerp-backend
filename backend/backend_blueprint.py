import base64

from flask import Blueprint, session, g, current_app
import flask_restful as restful
import flask_login as login
from itsdangerous import JSONWebSignatureSerializer, BadSignature
from backend.pool import Pool
from backend.models import Model, ModelBunch, ModelMethod, ModelIdMethod, Token
import erppeek


backend = Blueprint('blueprint', __name__)

api = restful.Api()
api.init_app(backend)
api.add_resource(Token, 'token')
api.add_resource(ModelBunch, '<string:model>')
api.add_resource(Model, '<string:model>/<int:obj_id>')
api.add_resource(ModelIdMethod, '<string:model>/<int:obj_id>/<string:method>')
api.add_resource(ModelMethod, '<string:model>/<string:method>')

login_manager = login.LoginManager()

pool = Pool()


class APIUser(login.UserMixin):

    def __init__(self, login, password):
        self.login = login
        self.password = password

    def is_authenticated(self):
        return True

    def get_id(self):
        return self.login


print '------------> backend loads'

@login_manager.header_loader
def load_user_from_header(header_val):
    try:
        header_val = header_val.replace('Basic ', '', 1)
        auth = header_val.split()
        if len(auth) == 1:
            header_val = base64.b64decode(header_val).decode('utf-8')
            user, password = header_val.split(':')
        else:
            user, password = header_val.split()
        if user == "token":
            key = current_app.config['SECRET_KEY']
            token_serializer = JSONWebSignatureSerializer(key)
            try:
                values = token_serializer.loads(password)
                user = values['login']
                password = values['password']
            except BadSignature:
                pass

        database = current_app.config['OPENERP_DATABASE']
        server = current_app.config['OPENERP_SERVER']
        try:
            print '------------> backend new client'
            client = pool.connect(server=server, db=database, user=user,
                                  password=password)
            g.backend_cnx = client

            session['openerp_login'] = user
            session['openerp_password'] = password
            client.close()
            return APIUser(user, password)
        except erppeek.Error as e:
            print '------------> erppeek Error' + str(e)

    except ValueError:
        pass


@login_manager.user_loader
def load_user(user_id):
    login = session.get('openerp_login')
    password = session.get('openerp_password')
    return APIUser(login, password)


@backend.teardown_request
def unload_user(*args, **kwargs):
    session.pop('openerp_login', None)
    session.pop('openerp_password', None)
    login.logout_user()


@backend.record_once
def setup_login(state):
    login_manager.init_app(state.app)
