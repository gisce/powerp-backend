from datetime import datetime

from cerberus import Validator, errors


class OpenERPValidator(Validator):

    def validate(self, document, schema=None, update=False, context=None):
        if 'id' in document:
            update = True
        else:
            update = False
        return super(OpenERPValidator, self).validate(
            document, schema=schema, update=update, context=context
        )

    def _validate_type_datetime_str(self, field, value):
        try:
            datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            self._error(field, errors.ERROR_BAD_TYPE.format('datetime_str'))

    def _validate_type_date_str(self, field, value):
        try:
            datetime.strptime(value, '%Y-%m-%d')
        except ValueError:
            self._error(field, errors.ERROR_BAD_TYPE.format("date_str"))
