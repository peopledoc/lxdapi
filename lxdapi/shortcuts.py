from .api import APIException


def container_absent(api, container):
    if not container:
        return True

    if container.metadata['status'] == 'Running':
        api.put(
            'containers/%s/state' % container.metadata['name'],
            json=dict(
                action='stop',
                timeout=api.default_timeout,
            )
        ).wait()

    container_destroy(api, container.metadata['name'])


def container_apply_config(api, container, config):
    if not container:
        api.post('containers', json=config).wait()
        return True

    return False


def container_apply_status(api, container, status):
    if status == container['metadata']['status']:
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
        'containers/%s/state' % container.data['name'],
        json=dict(
            action=action,
            timeout=api.default_timeout,
        )
    ).wait()

    return container, True


def container_destroy(api, name):
    return api.delete('containers/%s' % name).wait()


def container_get(api, name):
    try:
        return api.get('containers/%s' % name)
    except APIException as e:
        if e.result.response.status_code == 404:
            return None
        raise
