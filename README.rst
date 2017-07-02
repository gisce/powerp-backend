PowERP REST Backend
===================

REST API Backend for PowERP

You can access to the PowERP API with REST verbs and JSON format.

---------
Endpoints
---------

`GET /api/<model>`
~~~~~~~~~~~~~~~~~~

Get a collection of records.

Optional arguments:

* **filter**: Filter to apply to search resources, is a list of tuples as used in PowERP.
* **schema**: List of fields you want in the JSON, you can use dots to deep browsing. (Default all fields of model)
* **limit**: Number of maxim number of items. (Default 80)
* **offset**: From which number to start. (Default 0)

The result is a json with the following keys:

* **items**: List of JSON documents with the schema defined in the schema parameter.
* **n_items**: Total number of items.
* **offset**: Current offset.
* **limit**: Current limit.

Request e.g.::

  GET /api/account.invoice?schema=['number','partner_id.name','partner_id.vat','total_amount']&filter=[('state','=','open'),('type','in',('out_invoice','out_refund'))]
  
Response e.g.:

.. code:: json

  {
    "items": [
      {
        "id": 435,
        "number": "34432",
        "partner_id": {
          "id": 43,
          "name": "Partner Name, S.L.",
          "vat": "ESB1111113",
        },
        "total_amount": 343.43
      },
      {
        "id": 432,
        "number": "34433",
        "partner_id": {
          "id": 43,
          "name": "Monospace, S.L.",
          "vat": "ESB1123111",
        },
        "total_amount": 143.32
      },
    ],
    "n_items": 2,
    "limit": 80,
    "offset: 0
  }
  
  
`POST /api/<model>`
~~~~~~~~~~~~~~~~~~~

Create a new record of type `model` with JSON body

The backend will validate the the data, if somethin is not valid the following JSON will be returned

.. code:: json

  {
    "status": "ERROR",
    "errors": [
      "field X is required"
    ]
  }

and 422 HTTP Status

If all it's ok the following JSON will be returned

.. code:: json

  {
    "status": "OK",
    "id": 43
  }


`POST /api/<model>/<method>`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Call a model method.

You can pass arguments to the method with the JSON body as the following:

.. code:: json

  {
    "args": ["param1", "param2"]
  }
  
The result is a JSON document as the following:

.. code:: json

  {
    "res": "<method_result>"
  }

`GET /api/<model>/<id>`
~~~~~~~~~~~~~~~~~~~~~~~

Get a record.

Is the same as `GET /api/<model>` but the without `limit`, `offset` and `filter`.
The response is only the JSON of the resource.


`PATCH /api/<model>/<id>`
~~~~~~~~~~~~~~~~~~~~~~~~~

Updates a record.


`DELETE /api/<model>/<id>`
~~~~~~~~~~~~~~~~~~~~~~~~~~

Removes a record.

--------------
Authentication
--------------

`GET /api/token`
~~~~~~~~~~~~~~~~

You must authenticate using Basic Auth a token will be returned as the following:

.. code:: json

  {
    "token": "fkaldsjfñlkajsflñksajdfñlkjsadñlfja9074375984352.09aufoiajsdf"
  }

Then you should use this token for the future requests with the 'Auth header' as:

``"Authoritzation: token fkaldsjfñlkajsflñksajdfñlkjsadñlfja9074375984352.09aufoiajsdf"``
