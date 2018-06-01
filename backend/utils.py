import collections
from numbers import Integral
from hashlib import sha1

from werkzeug.contrib.cache import SimpleCache


class DataCache(SimpleCache):

    TIMEOUT = 10

    @staticmethod
    def calculate_key(model, ids, fields):
        if not isinstance(ids, (list, tuple)):
            ids = [ids]
        ids = sorted(ids)
        fields = sorted(fields)
        key_args = '{}-{}-{}'.format(model, ids, fields).encode('utf-8')
        key = sha1(key_args).hexdigest()
        return key

    def get_data(self, model, ids, fields):
        key = self.calculate_key(model, ids, fields)
        return self.get(key)

    def set_data(self, model, ids, fields, values):
        key = self.calculate_key(model, ids, fields)
        self.set(key, values, self.TIMEOUT)

    def get_fields(self, model):
        key = '{}_fields'.format(model)
        return self.get(key)

    def set_fields(self, model, fields):
        key = '{}_fields'.format(model)
        self.set(key, fields, self.TIMEOUT)


cache = DataCache()


def recursive_crud(model, values):
    schema = model.fields_get()
    vals = {}
    for k, v in values.items():
        if k == 'id':
            vals[k] = v
            continue
        field_type = schema.get(k, {}).get('type')
        if field_type is None:
            continue
        if field_type == 'boolean':
            vals[k] = int(v)
        if v is None:
            vals[k] = False
        if 'relation' in schema[k]:
            relation = model.client.model(schema[k]['relation'])
            if field_type == 'many2one':
                if isinstance(v, Integral):
                    vals[k] = v
                elif v.keys() == ['id']:
                    vals[k] = v['id']
                else:
                    vals[k] = recursive_crud(relation, v)
            else:
                if not v:
                    vals[k] = [(5, )]
                else:
                    xmany = []
                    for value in v:
                        if value.keys() == ['id']:
                            xmany.append((4, value['id']))
                        else:
                            xmany.append((4, recursive_crud(relation, value)))
                    vals[k] = xmany
        else:
            vals[k] = v

    if 'id' not in vals:
        item_id = model.create(vals).id
    else:
        item_id = vals.pop('id', None)
        if vals:
            stored = model.read([item_id], list(vals.keys()))[0]
            stored.pop('id', None)
            for key, stored_value in stored.items():
                if vals[key] == stored_value:
                    vals.pop(key)
        if vals:
            model.write([item_id], vals)
    return item_id


def normalize(model, values, dump_schema=None):
    if dump_schema is None:
        dump_schema = {}
    schema = cache.get_fields(model._name)
    if schema is None:
        schema = model.fields_get()
        cache.set_fields(model._name, schema)
    _values = values.copy()
    for k, v in _values.items():
        field_type = schema.get(k, {}).get('type')
        if field_type is None:
            continue
        elif field_type.endswith('2many') and not v:
            _values[k] = []
        elif field_type != 'boolean' and not v:
            _values[k] = None
        elif 'relation' in schema[k]:
            relation = model.client.model(schema[k]['relation'])
            fields_to_read = []
            if k in dump_schema and isinstance(dump_schema[k], dict):
                fields_to_read = dump_schema[k]
            if field_type == 'many2one':
                if fields_to_read:
                    data = cache.get_data(
                        relation._name,
                        _values[k][0],
                        fields_to_read
                    )
                    if data is None:
                        data = relation.read(_values[k][0], fields_to_read)
                        cache.set_data(
                            relation._name,
                            _values[k][0],
                            fields_to_read,
                            data
                        )
                    _values[k] = normalize(
                        relation, data, dump_schema.get(k)
                    )
                else:
                    _values[k] = {'id': values[k][0]}
            else:
                rel_ids = _values[k]
                _values[k] = []
                if fields_to_read:
                    for data in relation.read(rel_ids, fields_to_read):
                        _values[k].append(normalize(
                            relation, data, dump_schema.get(k)
                        ))
                else:
                    for rel_id in rel_ids:
                        _values[k].append(dict(id=rel_id))
    return _values


def recursive_update(d, u):
    for k, v in u.items():
        if isinstance(v, collections.Mapping):
            r = recursive_update(d.get(k, {}), v)
            d[k] = r
        else:
            d[k] = u[k]
    return d


def unflatdot(fields):
    schema = {}
    for field in sorted(fields):
        tree = field.split('.')
        if len(tree) > 1:
            k = tree[0]
            v = ['.'.join(tree[1:])]
            schema.setdefault(k, {})
            recursive_update(schema[k], unflatdot(v))
        else:
            schema[field] = True
    return schema


def flatdot(schema):
    fields = []
    if schema is True:
        return ['id']
    for k, v in schema.items():
        if isinstance(v, dict):
            for f in flatdot(schema[k]):
                f = '%s.%s' % (k, f)
                fields.append(f)
        elif isinstance(v, list):
            for x in schema[k]:
                for f in flatdot(x):
                    f = '%s.%s' % (k, f)
                    if f not in fields:
                        fields.append(f)
        else:
            fields.append(k)
    return fields


def make_schema(model, fields, data=None):
    if data is None:
        data = {}
    fields = unflatdot(fields)
    fields_def = model.fields_get()
    defaults_fields = model.default_get(list(fields_def.keys()))
    schema = {}
    if 'id' not in fields_def:
        fields_def['id'] = {'type': 'integer'}
    for field, attrs in fields_def.items():
        if 'id' not in fields:
            required = (
                attrs.get('required', False) and field not in defaults_fields
            )
        else:
            required = False
        schema[field] = {
            'required': required,
            'readonly': bool(attrs.get('readonly', False))
        }
        states = attrs.get('states', {})
        if states:
            if 'state' in data:
                schema[field].update(dict(states[data['state']]))
            elif 'state' in defaults_fields:
                schema[field].update(dict(states[defaults_fields['state']]))

        type_ = attrs['type']
        if type_ in ('text', 'char', 'selection', 'binary'):
            type_ = 'string'
        if attrs['type'] == 'char' and attrs.get('size'):
            schema[field]['maxlength'] = attrs['size']
        if 'selection' in attrs:
            schema[field]['allowed'] = [x[0] for x in attrs['selection']]
        if 'relation' in attrs:
            relation = model.client.model(attrs['relation'])
            if field not in fields:
                rel_schema = {'id': {'type': 'integer'}}
            else:
                rel_fields = flatdot(fields[field])
                rel_schema = make_schema(relation, rel_fields)
            if attrs['type'] == 'many2one':
                if isinstance(data.get(field), dict):
                    type_ = 'dict'
                    schema[field]['schema'] = rel_schema
                else:
                    type_ = 'integer'
            elif attrs['type'] in ('many2many', 'one2many'):
                type_ = 'list'
                schema[field]['schema'] = {
                    'type': 'dict',
                    'schema': rel_schema
                }
        if attrs['type'] in ('date', 'datetime'):
            type_ = '%s_str' % attrs['type']
        if attrs['type'] == 'reference':
            type_ = 'string'
            schema[field]['regex'] = '^({}),\d'.format('|'.join(
                    x[0].replace('.', '\.') for x in attrs['selection']
                )
            )
            schema[field].pop('allowd', None)
        schema[field]['type'] = type_
    return schema
