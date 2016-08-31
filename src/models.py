from ast import literal_eval
from xmlrpclib import Fault

from flask import jsonify, current_app, g, request
from flask.ext import restful
from flask.ext.restful import reqparse
from flask.ext import login
from flask.ext import cors
from itsdangerous import JSONWebSignatureSerializer

from backend.utils import (
    recursive_crud, flatdot, unflatdot, normalize, make_schema
)
from backend.validators import OpenERPValidator


def get_model(model):
    client = g.backend_cnx
    if '.' in model:
        model = client.model(model)
    else:
        model = getattr(client, model)
    return model


class BaseResource(restful.Resource):
    method_decorators = [login.login_required, cors.cross_origin()]


class Token(BaseResource):
    def get(self):
        user = login.current_user
        key = current_app.config['SECRET_KEY']
        serializer = JSONWebSignatureSerializer(key)
        token = serializer.dumps({
            'login': user.login, 'password': user.password
        })
        return jsonify({'token': token})


class Model(BaseResource):

    def get(self, model, id):
        model = get_model(model)
        parser = reqparse.RequestParser()
        parser.add_argument(
            'schema', dest='schema',
            type=str, help='Schema for dumping the JSON'
        )
        args = parser.parse_args()
        schema = args.schema
        if schema:
            schema = [x.strip() for x in schema.split(',')]
        else:
            schema = model.fields_get().keys()
        schema = unflatdot(schema)
        result = normalize(model, model.read(id, schema.keys()), schema)
        return jsonify(result)

    def patch(self, model, id):
        model = get_model(model)
        data = request.json
        data['id'] = id
        fields = flatdot(data)
        schema = make_schema(model, fields)
        validator = OpenERPValidator(schema)
        if not validator.validate(data, update=True):
            response = {
                'status': 'ERROR',
                'errors': validator.errors
            }
            resp = jsonify(response)
            resp.status_code = 422
        else:
            recursive_crud(model, data)
            resp = jsonify({'status': 'OK'})
        return resp

    def delete(self, model, id):
        model = get_model(model)
        found = model.search([('id', '=', id)], context={'active_test': False})
        if not found:
            response = jsonify({'status': 'ERROR'})
            response.status_code = 404
            return response
        else:
            model.unlink(found)
            return jsonify({'status': 'OK'})


class ModelBunch(BaseResource):
    def post(self, model):
        model = get_model(model)
        data = request.json
        fields = flatdot(data)
        schema = make_schema(model, fields)
        validator = OpenERPValidator(schema)
        if not validator.validate(data, update=True):
            response = {
                'status': 'ERROR',
                'errors': validator.errors
            }
            resp = jsonify(response)
            resp.status_code = 422
        else:
            res_id = recursive_crud(model, data)
            resp = jsonify({'status': 'OK', 'id': res_id})
        return resp

    def get(self, model):
        model = get_model(model)
        parser = reqparse.RequestParser()
        parser.add_argument(
            'filter', dest='filter',
            type=str, help='Filter for searching items'
        )
        parser.add_argument(
            'schema', dest='schema',
            type=str, help='Schema for dumping the JSON'
        )
        parser.add_argument(
            'limit', dest='limit', default=80,
            type=int, help='Limit results'
        )
        parser.add_argument(
            'offset', dest='offset', default=0,
            type=int, help='Offset of results'
        )
        args = parser.parse_args()
        limit = args.limit
        offset = args.offset
        if args.filter:
            try:
                search_params = literal_eval(args.filter)
            except (ValueError, SyntaxError), e:
                response = jsonify({
                    'status': 'ERROR',
                    'errors': {'filter': e.message}
                })
                response.status_code = 422
                return response
        else:
            search_params = []
        try:
            count = model.search_count(search_params)
            res_ids = model.search(search_params, limit=limit, offset=offset)
        except Fault:
            response = jsonify({'status': 'ERROR'})
            response.status_code = 422
            return response
        if args.schema:
            schema = [x.strip() for x in args.schema.split(',')]
        else:
            schema = model.fields_get().keys()
        schema = unflatdot(schema)
        items = []
        for item_id in res_ids:
            values = model.read(item_id, schema.keys())
            items.append(normalize(model, values, schema))
        return jsonify({
            'items': items, 'n_items': count, 'limit': limit, 'offset': offset
        })


class ModelMethod(BaseResource):
    def post(self, model, id, method):
        model = get_model(model).browse(id)
        method = getattr(model, method)
        data = request.json
        if data and 'args' in data:
            res = method(*data['args'])
        else:
            res = method()
        return jsonify({'res': res})
