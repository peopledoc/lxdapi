"""
HTTP API classes for interfacing with the LXD API.

This module leverages the composition pattern, providing 3 main classes:

- :class:`API`: the entry point for dealing with the HTTP API,
- :class:`APIResult`: returned by requests made with :class:`API`, it
  represents an HTTP transaction.
- :class:`APIException`: raised when the server responded with HTTP 400.
"""

from __future__ import print_function
from __future__ import unicode_literals

import json
import os

import requests

import requests_unixsocket


class APIException(Exception):
    """Raised by :class:`API` on HTTP/400 responses."""

    def __init__(self, result):
        """
        Construct an APIException with an :class:`APIResult`.

        It will try to find the error message in the HTTP response and use it
        if it find it, otherwise will use the response data as message.
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
    Represent an HTTP transaction.

    .. py:attr: api

        :class:`API` object which returned this result.

    .. py:attr: data

        JSON data from the response.

    .. py:attr: request

        Request object from the requests library.

    .. py:attr: response

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
        summary = ['{} {}'.format(self.request.method, self.request.url)]

        if self.request.body:
            summary.append(
                json.dumps(json.loads(self.request.body), indent=4)
            )

        return '\n'.join(summary)

    def response_summary(self):
        return '\n'.join([
            'HTTP/{}'.format(self.response.status_code),
            json.dumps(self.data, indent=4),
        ])

    def validate(self):
        if self.response.status_code == 404:
            raise APINotFoundException(self)

        if self.response.status_code >= 400:
            raise APIException(self)

        def validate_metadata(data):
            if isinstance(data.get('metadata'), dict):
                if data['metadata'].get('status_code', 0) >= 400:
                    raise APIException(self)
                validate_metadata(data['metadata'])
        validate_metadata(self.data)

    def wait(self, timeout=None):
        timeout = timeout or self.api.default_timeout

        return self.api.get(
            '%s/wait?timeout=%s' % (self.data['operation'], timeout)
        )


class API(object):
    @classmethod
    def factory(cls, endpoint=None, default_version=None, **kwargs):
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
        if not url.startswith('/'):
            url = '/{}/{}'.format(self.default_version, url)

        return self.endpoint + url

    def request(self, method, url, *args, **kwargs):
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
        return self.request('DELETE', url, *args, **kwargs)

    def get(self, url, *args, **kwargs):
        return self.request('GET', url, *args, **kwargs)

    def post(self, url, *args, **kwargs):
        return self.request('POST', url, *args, **kwargs)

    def put(self, url, *args, **kwargs):
        return self.request('PUT', url, *args, **kwargs)
