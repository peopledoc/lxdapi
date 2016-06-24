"""
Idempotent functions and shortcuts.

Functions here have the following similarities:

- take a :class:`~lxdapi.api.API` as first argument,
- return True if something has changed, False otherwise,
- except ``_get()`` functions such as ``container_get()`` which return
  :class:`~lxdapi.api.APIResult` for an :meth:`lxdapi.api.API.get` or False.
"""

import hashlib

from .api import APINotFoundException


def container_absent(api, container):
    """
    Ensure a container is absent.

    Container is an :class:`~lxdapi.api.APIResult` for the container, to be
    able to compare the configuration with.

    It is expected that the user manages the HTTP transactions, here's an
    example usage::

        container_absent(api, container_get('yourcontainer'))
    """
    if not container:
        return False

    if container.metadata['status'] == 'Running':
        api.put(
            'containers/%s/state' % container.metadata['name'],
            json=dict(
                action='stop',
                timeout=api.default_timeout,
            )
        ).wait()

    api.delete('containers/%s' % container.metadata['name']).wait()
    return True


def container_apply_config(api, container, config):
    """
    Apply a configuration on a container.

    Container is an:class:`lxdapi.api.APIResult`for the container, to be able
    to compare the configuration with.

    Config is the dict to pass as JSON to the HTTP API.

    Example usage::

        container_apply_config(api, container_get('yourcontainer'))
    """
    if not container:
        api.post('containers', json=config).wait()
        return True

    return False


def container_apply_status(api, container, status):
    """Apply an LXD status to a container.

    Container is an:class:`lxdapi.api.APIResult`for the container, to be able
    to compare the status with.

    Status is a string, choices are: Running, Stopped, Frozen.

    Example usage::

        container_apply_status(api, container_get('yourcontainer'), 'Running')
    """

    if status == container.metadata['status']:
        return False

    if status == 'Running':
        action = 'start'
    elif status == 'Stopped':
        action = 'stop'
    elif status == 'Frozen':
        action = 'freeze'
    else:
        raise Exception('Invalid status %s, choices are: %s' % (
            status,
            ['Running', 'Stopped', 'Frozen'],
        ))

    api.put(
        'containers/%s/state' % container.metadata['name'],
        json=dict(
            action=action,
            timeout=api.default_timeout,
        )
    ).wait()

    return True


def container_get(api, name):
    """Return the:class:`lxdapi.api.APIResult`for a container or False."""
    try:
        return api.get('containers/%s' % name)
    except APINotFoundException:
        return False


def image_absent(api, fingerprint):
    """
    Return False if the image is absent, otherwise delete it and return True.
    """
    if not image_get(api, fingerprint):
        return False

    api.delete('images/%s' % fingerprint).wait()
    return True


def image_get_fingerprint(path):
    """Return the fingerprint for an image."""
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def image_get(api, fingerprint):
    """Return the :class:`APIResult` for a fingerprint or False."""
    try:
        return api.get('images/%s' % fingerprint)
    except APINotFoundException:
        return False


def image_present(api, path, fingerprint=None):
    """Ensure an image is present."""
    fingerprint = fingerprint or image_get_fingerprint(path)

    if image_get(api, fingerprint):
        return False  # nuthin to do

    with open(path, 'rb') as f:
        headers = {
            'X-LXD-Public': '1',
        }
        api.post('images', data=f.read(), headers=headers).wait()

    return True


def image_alias_present(api, name, target, description=None):
    """Ensure an image has an alias."""
    try:
        result = api.get('images/aliases/%s' % name)
    except APINotFoundException:
        pass
    else:
        if result.metadata['target'] == target:
            return False
        api.delete('images/aliases/%s' % name)

    api.post('images/aliases', json=dict(
        name=name,
        target=target,
        description=description or '',
    ))

    return True
