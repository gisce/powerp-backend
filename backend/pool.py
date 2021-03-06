from hashlib import sha1
from time import time

from erppeek_wst import ClientWST as Client
from six import text_type


class Pool(object):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Pool, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self, size=10, timeout=900):
        self._clients = {}
        self._max_size = size
        self._timeout = timeout

    def _prune(self):
        if len(self._clients) > self._max_size:
            now = time()
            to_remove = []
            for key, (_, expires) in self._clients.items():
                if expires <= now:
                    to_remove.append(key)
            for key in to_remove:
                self._clients.pop(key, None)

    def connect(self, server, db=None, user=None, password=None):
        key_args = [x for x in [server, db, user, password] if x]
        u_key_args = []
        for element in key_args:
            if isinstance(element, text_type):
                u_key_args.append(element.encode('utf-8'))
            else:
                u_key_args.append(element)
        key = sha1(u'-'.encode('utf-8').join(u_key_args)).hexdigest()
        if key in self._clients:
            client, _ = self._clients[key]
        else:
            client = Client(server, db=db, user=user, password=password)
        self._clients[key] = client, time() + self._timeout
        self._prune()
        return client
