from datetime import datetime

from cerberus import Validator


class OpenERPValidator(Validator):

    def validate(self, document, schema=None, update=False, normalize=True):
        if 'id' in document:
            update = True
        else:
            update = False
        return super(OpenERPValidator, self).validate(
            document, schema=schema, update=update, normalize=normalize
        )

    def _validate_type_datetime_str(self, value):
        try:
            datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
            return True
        except ValueError:
            pass

    def _validate_type_date_str(self, value):
        try:
            datetime.strptime(value, '%Y-%m-%d')
            return True
        except ValueError:
            pass
