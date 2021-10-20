from hashlib import sha1
from time import time
try:
        # Due: https://www.python.org/dev/peps/pep-0476
    import ssl
    try:
                _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:
                # Legacy Python that doesn't verify HTTPS certificates by default
        pass
    else:
                # Handle target environment that doesn't support HTTPS verification
        ssl._create_default_https_context = _create_unverified_https_context
except ImportError:
        pass

from erppeek_wst import ClientWST as Client

class Pool(object):

    def connect(self, server, db=None, user=None, password=None):
        client = Client(server, db=db, user=user, password=password)
        return client
