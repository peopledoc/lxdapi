import logging
import os

import requests
import requests_unixsocket


class API(object):
    def __init__(self, socket=None, url=None, debug=False):
        self.default_timeout = 30

        if socket is None and url is None:
            socket = '/var/lib/lxd/unix.socket'

        if socket:
            if not os.path.exists(socket):
                raise RuntimeError('Socket %s does not exist' % socket)
            self.session = requests_unixsocket.Session('http+unix://')
            self.base_url = 'http+unix://%s' % requests.compat.quote_plus(
                socket
            )
        else:
            self.session = requests.Session()
            self.base_url = url

        if debug or os.environ.get('DEBUG', False):
            self.enable_debug()

    @staticmethod
    def enable_debug():
        # Enabling debugging at http.client level
        # (requests->urllib3->http.client) you will see the REQUEST,
        # including HEADERS and DATA, and RESPONSE with HEADERS but
        # without DATA.  the only thing missing will be the
        # response.body which is not logged.

        try: # for Python 3
            from http.client import HTTPConnection
        except ImportError:
            from httplib import HTTPConnection

        HTTPConnection.debuglevel = 1

        # you need to initialize logging, otherwise you will not see
        # anything from requests
        logging.basicConfig()
        logging.getLogger().setLevel(logging.DEBUG)
        requests_log = logging.getLogger("requests.packages.urllib3")
        requests_log.setLevel(logging.DEBUG)
        requests_log.propagate = True

    def request(self, method, url, **kwargs):
        absolute_url = self.base_url + url
        return self.session.request(method, absolute_url, **kwargs)

    def wait_success(self, operation, timeout=None):
        timeout = timeout or self.default_timeout

        response = self.request(
            'GET',
            '{0}/wait?timeout={1}'.format(operation, timeout)
        )

        if response.json()['metadata']['status'] != 'Success':
            raise RuntimeError(response)

        return response

    def container_create(self, config):
        return self.request(
            'POST',
            '/1.0/containers',
            json=config
        )

    def container_get(self, name):
        response = self.request(
            'GET',
            '/1.0/containers/{0}'.format(name),
        )
        if response.status_code == 404:
            return False
        return response.json()

    def container_state_get(self, name):
        return self.request(
            'GET',
            '/1.0/containers/{0}'.format(name),
        )

    def container_apply(self, config, status):
        container = self.container_get(config['name'])

        if not container:
            result = self.container_create(config)
            result = self.wait_success(result.json()['operation'])
            container = self.container_get(config['name'])

        if status != container['metadata']['status']:
            import ipdb; ipdb.set_trace()

        return result
