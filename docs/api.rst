HTTP API transactions
~~~~~~~~~~~~~~~~~~~~~

API
===

.. automodule:: lxdapi.api
.. automethod:: lxdapi.api.API.factory
.. autoclass:: lxdapi.api.API
.. automethod:: lxdapi.api.API.request


If the server responds with HTTP/400 then an APIException will be raised. It
has the APIResult as ``result`` attribute and has the error message from the
server as error. It looks like this::

    APIException: GET http+unix://%2Fvar%2Flib%2Flxd%2Funix.socket/1.0/operations/1c34b923-57c8-4fce-b349-e4a1c61b8803/wait?timeout=30 Error calling 'lxd forkstart pylxd-test-container /var/lib/lxd/containers /var/log/lxd/pylxd-test-container/lxc.conf': err='exit status 1'

.. automethod:: lxdapi.api.API.delete
.. automethod:: lxdapi.api.API.get
.. automethod:: lxdapi.api.API.post
.. automethod:: lxdapi.api.API.put

Debugging
---------

The purpose of this lib is to help the user to have feedback from HTTP
transactions. If anything fails, it should help a lot to re-run the program
with the ``DEBUG`` env var, and such output will be printed out for every
transaction::

	PUT http+unix://%2Fvar%2Flib%2Flxd%2Funix.socket/1.0/containers/pylxd-test-container/state
	{
		"action": "stop",
		"timeout": 30
	} HTTP/202
	{
		"status": "Operation created",
		"status_code": 100,
		"operation": "/1.0/operations/70eb42bf-5e79-42de-8230-2162e9e8b612",
		"type": "async",
		"metadata": {
			"status": "Running",
			"err": "",
			"status_code": 103,
			"created_at": "2016-06-23T15:05:45.435413676+02:00",
			"updated_at": "2016-06-23T15:05:45.435413676+02:00",
			"class": "task",
			"may_cancel": false,
			"id": "70eb42bf-5e79-42de-8230-2162e9e8b612",
			"resources": {
				"containers": [
					"/1.0/containers/pylxd-test-container"
				]
			},
			"metadata": null
		}
	}

APIResult
=========

.. autoclass:: lxdapi.api.APIResult
   :members:

Exceptions
=========

APIException
------------

.. autoclass:: lxdapi.api.APIException
   :members:

APINotFoundException
--------------------

.. autoclass:: lxdapi.api.APINotFoundException
   :members:
