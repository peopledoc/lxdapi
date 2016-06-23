from lxdapi import lxd

def test_container():
    api = lxd.API.factory()
    name = 'lxdapi-test-container'

    lxd.container_absent(api, name)

    container, changed = lxd.container_apply_config(
        api,
        config=dict(
            name=name,
            source=dict(
                type='image',
                mode='pull',
                server='https://images.linuxcontainers.org',
                protocol='lxd',
                alias='ubuntu/xenial/amd64',
            ),
            profiles=['default'],
        ),
    )
    assert changed

    container, changed = lxd.container_apply_status(api, name, 'Running')
    assert changed

    container, changed = lxd.container_apply_status(api, name, 'Running')
    assert not changed

    assert lxd.container_exists(api, name)
