def container_absent(api, name):
    if container_exists(api, name):
        container_destroy(api, name)


def container_get(api, name):
    container_get = api.get('containers/{}', name)

    if container_get.response.status_code == 404:
        return False

    return container_get


def container_absent(api, name):
    container = container_get(api, name)

    if not container:
        return True

    if container['metadata']['status'] == 'Running':
        container = api.put('containers/{}/state', name, json=dict(
            action='stop',
            timeout=api.default_timeout,
        )).wait()

    container_destroy(api, name)


def container_apply(api, config, status):
    container = container_get(api, config['name'])

    if not container:
        api.post('containers', json=config).wait()
        container = api.get('containers/{}', config['name'])

    if status != container['metadata']['status']:
        if status == 'Running':
            action = 'start'
        elif status == 'Stopped':
            action = 'stop'
        elif status == 'Frozen':
            action = 'freeze'
        else:
            raise Exception('Status %s not understood, choices are: %s' % (
                status,
                ['Running', 'Stopped', 'Frozen'],
            ))

        container = api.put('containers/{}/state', config['name'], json=dict(
            action=action,
            timeout=api.default_timeout,
        )).wait()

    return container


def container_destroy(api, name):
    return api.delete('containers/{}', name).wait()


def container_exists(api, name):
    containers = api.get('containers')

    for container in containers['metadata']:
        if container.split('/')[-1] == name:
            return True

    return False
