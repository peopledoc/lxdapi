"""
HTTP API classes for interfacing with the LXD API.

This module leverages the composition pattern, providing 3 main classes:

- :class:`API`: the entry point for dealing with the HTTP API,
- :class:`APIResult`: returned by requests made with :class:`API`, it
  represents an HTTP transaction.
- :class:`APIException`: raised when the server responded with HTTP 400.

The :class:`API` object wraps around requests, note that its constructor takes
a debug keyword argument to enable printouts of HTTP transactions, that can
also be enabled with the ``DEBUG`` environment variable.
"""

from __future__ import print_function
from __future__ import unicode_literals

import json
import os

import requests

import requests_unixsocket


class APIException(Exception):
    """
    Raised by :class:`API` on HTTP/400 responses.

    It will try to find the error message in the HTTP response and
    use it if it find it, otherwise will use the response data as
    message.

    .. attribute:: result

        The :class:`APIResult` this was raised for.
    """

    def __init__(self, result):
        """
        Construct an APIException with an :class:`APIResult`.
        """
        self.result = result

        message = [
            result.request.method,
            result.request.url,
        ]

        if 'error' in result.data:
            message.append(result.data['error'])
        elif 'err' in result.metadata:
            message.append(result.metadata['err'])
        else:
            message.append(json.dumps(result.data, indent=4))

        super(APIException, self).__init__(' '.join(message))


class APINotFoundException(APIException):
    """Child of APIException for 404."""


class APIResult(object):
    """
    Represent an HTTP transaction, return by API calls using :class:`API`.

    .. attribute:: api

        :class:`API` object which returned this result.

    .. attribute:: data

        JSON data from the response.

    .. attribute:: request

        Request object from the requests library.

    .. attribute:: response

        Response object from the requests library.
    """

    def __init__(self, api, response):
        """Construct a :class:`APIResult` with an :class:`API` and response."""
        self.api = api
        self.data = response.json()
        self.metadata = self.data.get('metadata', None)
        self.response = response
        self.request = response.request

    def request_summary(self):
        """Return a string with the request method, url, and data."""
        summary = ['{} {}'.format(self.request.method, self.request.url)]

        if self.request.body:
            summary.append(
                json.dumps(json.loads(self.request.body), indent=4)
            )

        return '\n'.join(summary)

    def response_summary(self):
        """Return a string with the response status code and data."""
        return '\n'.join([
            'HTTP/{}'.format(self.response.status_code),
            json.dumps(self.data, indent=4),
        ])

    def validate_metadata(self, data):
        """
        Recursive function to check status code for a metadata dict.

        Each metadata may contain more metadata. Each metadata may have a
        status_code, if it's superior or equal to 400 then an
        :class:`APIException` is raised.

        This is used by :meth:`validate()` which should be used in general
        instead of this method.
        """
        if isinstance(data.get('metadata'), dict):
            if data['metadata'].get('status_code', 0) >= 400:
                raise APIException(self)
            self.validate_metadata(data['metadata'])

    def validate(self):
        """
        Recursive status code checker for this result's response.

        If the response's status code is 404 then raise
        :class:`APINotFoundException`.

        If the response's status code is anything superior or equal to 400
        then raise :class:`APIException`

        It'll use :meth:`validate_metadata()` to check metadata.
        """
        if self.response.status_code == 404:
            raise APINotFoundException(self)

        if self.response.status_code >= 400:
            raise APIException(self)

        self.validate_metadata(self.data)

    def wait(self, timeout=None):
        """Execute the wait API call for the operation in this result."""
        timeout = timeout or self.api.default_timeout

        return self.api.get(
            '%s/wait?timeout=%s' % (self.data['operation'], timeout)
        )


class API(object):
    """
    Main entry point to interact with the HTTP API.

    Once you have an instance of :class:`API`, which is easier to make with
    :meth:`factory()` than with the constructor, use the :meth:`get()`,
    :meth:`post()`, :meth:`delete()`, :meth:`put()` or :meth:`request()`
    directly. Since :meth:`request()` is used by the other methods, refer to
    to :meth:`request()` for details.

    Example::

        api = lxd.API.factory()
        api.post('images', json=data_dict).wait()
    """

    @classmethod
    def factory(cls, endpoint=None, default_version=None, **kwargs):
        """
        Instanciate an :class:`API` with the right endpoint and session.

        Example::

            # Connect to a local socket
            api = lxd.API.factory()

            # Or, connect to a remote server (untested so far)
            api = lxd.API.factory(base_url='http://example.com:12345')
        """
        endpoint = endpoint or '/var/lib/lxd/unix.socket'
        default_version = default_version or '1.0'

        if endpoint.startswith('/'):
            if not os.path.exists(endpoint):
                raise RuntimeError('Socket %s does not exist' % endpoint)

            endpoint = 'http+unix://{}'.format(
                requests.compat.quote_plus(endpoint)
            )
            session = requests_unixsocket.Session('http+unix://')
        else:
            session = requests.Session()

        return cls(
            session=session,
            endpoint=endpoint,
            default_version=default_version,
            **kwargs
        )

    def __init__(self, session, endpoint, default_version=None, debug=False):
        self.endpoint = endpoint[:-1] if endpoint.endswith('/') else endpoint
        self.default_timeout = 30
        self.default_version = default_version
        self.session = session
        self.debug = debug or os.environ.get('DEBUG', False)

    def format_url(self, url):
        """
        Return the absolute url for the given url.

        If the url isn't prefixed with a slash, it'll make it absolute by
        prepending the :attr:`default_version`, ie. ``images`` becomes
        ``/1.0/images``.

        Then, it'll prepend the endpoint, ie. ``/1.0/images`` becomes
        ``http+unix://%3Frun%3Flxd.socket/1.0/images``.
        """
        if not url.startswith('/'):
            url = '/{}/{}'.format(self.default_version, url)

        return self.endpoint + url

    def request(self, method, url, *args, **kwargs):
        """
        Execute an HTTP request, return an :class:`APIResult`.

        Note that it calls :meth:`APIResult.validate()`, which may raise
        :class:`APIException` or :class:`APINotFoundException`.

        If :attr:`debug` is True, then this will dump HTTP request and response
        data.

        Extra args and kwargs are passed to ``requests.Session.request()``.
        """
        url = self.format_url(url)

        if self.debug:
            print(method, url)
            if 'json' in kwargs:
                print(json.dumps(kwargs['json'], indent=4))

        result = APIResult(
            self,
            self.session.request(method, url, **kwargs),
        )

        if self.debug:
            print(result.response_summary())
            print('=' * 24)

        result.validate()

        return result

    def delete(self, url, *args, **kwargs):
        """Calls :meth:`request()` with ``method=DELETE``."""
        return self.request('DELETE', url, *args, **kwargs)

    def get(self, url, *args, **kwargs):
        """Calls :meth:`request()` with ``method=GET``."""
        return self.request('GET', url, *args, **kwargs)

    def post(self, url, *args, **kwargs):
        """Calls :meth:`request()` with ``method=POST``."""
        return self.request('POST', url, *args, **kwargs)

    def put(self, url, *args, **kwargs):
        """Calls :meth:`request()` with ``method=PUT``."""
        return self.request('PUT', url, *args, **kwargs)
