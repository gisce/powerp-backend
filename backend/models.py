from ast import literal_eval
from six.moves.xmlrpc_client import Fault
from flask import jsonify, current_app, g, request
import flask_restful as restful
from flask_restful import reqparse
import flask_login as login
import flask_cors as cors
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

    def options(self):
        return jsonify({})


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

    def get(self, model, obj_id):
        """
            Retrieve data from the element with id = obj_id

            :param model: Model name
            :type model: str
            :param obj_id: Element Id
            :type obj_id: str
            :return: Response with the data of the asked fields
            :rtype: Response
        """
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
        result = normalize(model, model.read(obj_id, schema.keys()), schema)
        return jsonify(result)

    def patch(self, model, obj_id):
        """
            Updates a record with id = obj_id

            :param model: Model name
            :type type: str
            :param obj_id: Element Id
            :type type: str
            :return: Response with the result of the action
            :rtype: Response
        """
        model = get_model(model)
        data = request.json
        data['id'] = obj_id
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

    def delete(self, model, obj_id):
        """
            Delete a record with id = obj_id

            :param model: Model name
            :type type: str
            :param obj_id: Element Id
            :type type: str
            :return: Response with the result of the action
            :rtype: Response
        """
        model = get_model(model)
        found = model.search([('id', '=', obj_id)], context={'active_test': False})
        if not found:
            response = jsonify({'status': 'ERROR'})
            response.status_code = 404
            return response
        else:
            model.unlink(found)
            return jsonify({'status': 'OK'})


class ModelBunch(BaseResource):

    def post(self, model):
        """
            Create a new record in the model

            :param model: Model name
            :type type: str
            :return: Response with the result of the action
            :rtype: Response
        """
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
        """
            Get a collection of record of the model

            :param model: Model name
            :type type: str
            :return: Response with the result of the action
            :rtype: Response
        """
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
            except (ValueError, SyntaxError) as e:
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
        except Fault:
            response = jsonify({'status': 'ERROR'})
            response.status_code = 422
            return response
        if args.schema:
            schema = [x.strip() for x in args.schema.split(',')]
        else:
            schema = list(model.fields_get().keys())
        schema = unflatdot(schema)
        fields = list(schema.keys())
        items = model.read(search_params, fields=fields, limit=limit, offset=offset)
        normalized_items = []
        for values in items:
            normalized_items.append(normalize(model, values, schema))
        return jsonify({
            'items': normalized_items,
            'n_items': count,
            'limit': limit,
            'offset': offset
        })


class ModelMethod(BaseResource):
    def post(self, model, method):
        """
            Call a method of the model

            :param model: Model name
            :type type: str
            :param method: Method name
            :type type: str
            :return: Response with the result of the method execution
            :rtype: Response
        """
        method = getattr(get_model(model), method)
        data = request.json
        if data and 'args' in data:
            res = method(*data['args'])
        else:
            res = method()
        return jsonify({'res': res})


class ModelIdMethod(BaseResource):
    def post(self, model, obj_id, method):
        """
            Call a method of a model and concrete element with id = obj_id

            :param model: Model name
            :type model: str
            :param obj_id: Element Id
            :type obj_id: str
            :param method: Method name
            :type method: str
            :return: Response with the result of the method execution
            :rtype: Response
        """
        model = get_model(model).browse(obj_id)
        method = getattr(model, method)
        data = request.json
        if data and 'args' in data:
            res = method(*data['args'])
        else:
            res = method()
        return jsonify({'res': res})

