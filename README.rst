lxdapi
~~~~~~

This library includes basic helpers encapsulating boring business logic code
for interacting with the lxd daemon. It is an experimental alternative to the
pylxd approach. The purpose of this library is **not** to be a full blown
framework for interacting with lxd completely abstracting HTTP transactions in
an hermetic way, pylxd already does a good job at that.

Example usage
=============

Instanciate an API object as such::

    from lxdapi import lxd

    # Connect to a local socket
    api = lxd.API.factory()

    # Or, connect to a remote server (untested so far)
    api = lxd.API.factory(base_url='http://example.com:12345')

The API object wraps around requests, note that its constructor takes a debug
keyword argument to enable printouts of HTTP transactions, that can also be
enabled with the DEBUG environment variable.

The API object wraps around requests and exposes ``get()``, ``put()``,
``delete()``, and ``post()`` methods, which wrap around the ``request()``
method. The first argument is the url template, then any number of args to
format it can be passed, then any kwarg will be passed to python requests.
Example::

    result = api.get('containers/{}', name)

This works because the API object prepends the url with the ``base_url`` and
``default_version`` attributes, so doing a ``get('containers')`` would actually
result in a request to something like
``http://example.com:1234/1.0/containers``. If the url argument passed to the
``get()`` method here was prefixed with a slash, then it wouldn't prepend the
default version.

This example returns an APIResult containing the request and response and data
objects. The APIResult object also has a wait method, can be used as such::

    container = api.put('containers/{}/state', name, json=dict(
        action='stop',
        timeout=api.default_timeout,
    )).wait()

If the server responds with HTTP/400 then an APIException will be raised. It
has the APIResult as ``result`` attribute and has the error message from the
server as error. It looks like this::

    APIException: GET http+unix://%2Fvar%2Flib%2Flxd%2Funix.socket/1.0/operations/1c34b923-57c8-4fce-b349-e4a1c61b8803/wait?timeout=30 Error calling 'lxd forkstart pylxd-test-container /var/lib/lxd/containers /var/log/lxd/pylxd-test-container/lxc.conf': err='exit status 1'

Additionnaly, some shortcuts have been implementated and demonstrate how easy
it is to use the API object, see ``lxdapi/shortcuts.py`` for details.

Example debug output
--------------------

The purpose of this lib is to help the user to have feedback from HTTP
transactions. If anything fails, it should help a lot to re-run the program
with the DEBUG env var, and such output will be printed out for every
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
