import hashlib

from .api import APIException, APINotFoundException


def container_absent(api, container):
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

    container_destroy(api, container.metadata['name'])
    return True


def container_apply_config(api, container, config):
    if not container:
        api.post('containers', json=config).wait()
        return True

    return False


def container_apply_status(api, container, status):
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


def container_destroy(api, name):
    return api.delete('containers/%s' % name).wait()


def container_get(api, name):
    try:
        return api.get('containers/%s' % name)
    except APIException as e:
        if e.result.response.status_code == 404:
            return None
        raise


def image_absent(api, fingerprint):
    if not image_is_present(api, fingerprint):
        return False

    api.delete('images/%s' % fingerprint).wait()
    return True


def image_get_fingerprint(path):
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def image_is_present(api, fingerprint):
    try:
        api.get('images/%s' % fingerprint)
    except APINotFoundException:
        return False
    return True


def image_present(api, path, fingerprint=None):
    fingerprint = fingerprint or image_get_fingerprint(path)

    if image_is_present(api, fingerprint):
        return False  # nuthin to do

    with open(path, 'rb') as f:
        headers = {
            'X-LXD-Public': '1',
        }
        api.post('images', data=f.read(), headers=headers).wait()

    return True


def image_alias_present(api, name, target, description=None):
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
