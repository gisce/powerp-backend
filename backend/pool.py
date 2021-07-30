from erppeek_wst import ClientWST as Client

class Pool(object):

    def connect(self, server, db=None, user=None, password=None):
        client = Client(server, db=db, user=user, password=password)
        return client
