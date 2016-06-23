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

        result = self.api.for_url(
            '{0}/wait?timeout={1}'.format(self['operation'], timeout)
        ).get()

        if result['metadata']['status'] != 'Success':
            raise APIException(result)

        return result


class API(object):
    @classmethod
    def factory(cls, base_url=None, **kwargs):
        if not base_url:
            base_url = '/var/lib/lxd/unix.socket'

        if base_url.startswith('/'):
            if not os.path.exists(base_url):
                raise RuntimeError('Socket %s does not exist' % base_url)

            base_url = 'http+unix://%s' % requests.compat.quote_plus(base_url)
            session = requests_unixsocket.Session('http+unix://')
        else:
            session = requests.Session()

        return cls(session=session, base_url=base_url, **kwargs)

    def __init__(self, session, base_url, url=None, debug=False):
        self.base_url = base_url[:-1] if base_url.endswith('/') else base_url
        self.default_timeout = 30
        self.session = session
        self.url = url or ''
        self.debug = debug or os.environ.get('DEBUG', False)

    def for_url(self, url):
        return type(self)(
            self.session,
            self.base_url,
            url=url,
            debug=self.debug
        )

    def __getitem__(self, item):
        return type(self)(
            self.session,
            self.base_url,
            '{}/{}'.format(self.url, item)
        )

    def request(self, method, **kwargs):
        url = self.base_url + self.url

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

    def delete(self, **kwargs):
        return self.request('DELETE', **kwargs)

    def get(self, **kwargs):
        return self.request('GET', **kwargs)

    def post(self, json, **kwargs):
        return self.request('POST', json=json, **kwargs)

    def put(self, json, **kwargs):
        return self.request('PUT', json=json, **kwargs)
