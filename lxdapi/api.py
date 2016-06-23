import json
import logging
import pprint
import os

import requests
import requests_unixsocket


class APIException(Exception):
    def __init__(self, result):
        self.result = result

        message = [
            result.request.method,
            result.request.url,
        ]

        if 'error' in result.data:
            message.append(result['error'])
        elif 'err' in result.get('metadata', {}):
            message.append(result['metadata']['err'])
        else:
            message.append(json.dumps(result.data, indent=4))

        super(APIException, self).__init__(' '.join(message))


class APIResult(object):
    def __init__(self, api, response):
        self.api = api
        self.response = response
        self.request = response.request
        self.data = response.json()

    def __getitem__(self, key):
        return self.data[key]

    def get(self, key, default):
        return self.data.get(key, default)

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

    def wait(self, timeout=None):
        timeout = timeout or self.api.default_timeout

        result = self.api.get('{}/wait?timeout={}', self['operation'], timeout)

        if result['metadata']['status'] != 'Success':
            raise APIException(result)

        return result


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

    def request(self, method, url, *url_format_args, **kwargs):
        try:
            url = url.format(*url_format_args)
        except IndexError:
            raise Exception(
                'Could not format %s with %s' % (url, url_format_args)
            )

        if not url.startswith('/'):
            url = '/{}/{}'.format(self.default_version, url)

        url = self.endpoint + url

        result = APIResult(
            self,
            self.session.request(method, url, **kwargs),
        )

        if result.response.status_code == 400:
            raise APIException(result)

        if self.debug:
            print result.request_summary(), result.response_summary()
            print '=' * 24

        return result

    def delete(self, url, *url_format_args, **kwargs):
        return self.request('DELETE', url, *url_format_args, **kwargs)

    def get(self, url, *url_format_args, **kwargs):
        return self.request('GET', url, *url_format_args, **kwargs)

    def post(self, url, *url_format_args, **kwargs):
        return self.request('POST', url, *url_format_args, **kwargs)

    def put(self, url, *url_format_args, **kwargs):
        return self.request('PUT', url, *url_format_args, **kwargs)
