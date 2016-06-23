def container_absent(api, name):
    if container_exists(api, name):
        container_destroy(api, name)


def container_get(api, name):
    container_get = api['containers'][name].get()

    if container_get.response.status_code == 404:
        return False

    return container_get


def container_absent(api, name):
    container = container_get(api, name)

    if not container:
        return True

    if container['metadata']['status'] == 'Running':
        container = api['containers'][name]['state'].put(dict(
            action='stop',
            timeout=api.default_timeout,
        )).wait()

    container_destroy(api, name)


def container_apply(api, config, status):
    container = container_get(api, config['name'])

    if not container:
        api['containers'].post(config).wait()
        container = api['containers'][config['name']].get()

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

        container = api['containers'][config['name']]['state'].put(dict(
            action=action,
            timeout=api.default_timeout,
        )).wait()

    return container


def container_destroy(api, name):
    return api['containers'][name].delete().wait()


def container_exists(api, name):
    containers = api['containers'].get()

    for container in containers['metadata']:
        if container.split('/')[-1] == name:
            return True

    return False
