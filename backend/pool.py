from hashlib import sha1
from time import time

from erppeek import Client


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
        print("c1")
        key_args = [x for x in [server, db, user, password] if x]
        print("c2 key_args:{}".format(key_args))
        key = sha1('-'.join(key_args).encode('utf-8')).hexdigest()
        print("c3")
        if key in self._clients:
            client, _ = self._clients[key]
            print("c4:{}".format(self._clients[key]))
        else:
            print("c5")
            client = Client(server, db=db, user=user.encode("utf-8"), password=password.encode("utf-8"))
        print("c6")
        self._clients[key] = client, time() + self._timeout
        print("c7")
        self._prune()
        print("c8")
        return client
