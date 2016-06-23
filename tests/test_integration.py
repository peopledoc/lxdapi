from lxdapi import lxd

def test_container():
    api = lxd.API.factory()
    name = 'lxdapi-test-container'

    container = lxd.container_get(api, name)
    lxd.container_absent(api, container)

    config = dict(
        name=name,
        source=dict(
            type='image',
            mode='pull',
            server='https://images.linuxcontainers.org',
            protocol='lxd',
            alias='ubuntu/xenial/amd64',
        ),
        profiles=['default'],
    )

    # Clean potential leftover from other test run
    lxd.container_absent(api, lxd.container_get(api, name))
    assert not lxd.container_get(api, name)

    # This should create the container and return True
    assert lxd.container_apply_config(
        api,
        lxd.container_get(api, name),
        config
    )

    # No change should happen, should return False
    assert not lxd.container_apply_config(
        api,
        lxd.container_get(api, name),
        config
    )

    # Should start the container and return True
    assert lxd.container_apply_status(api, name, 'Running')

    # No change should happen, should return False
    assert not lxd.container_apply_status(api, name, 'Running')

    # Should destroy the container and return True
    assert lxd.container_absent(api, lxd.container_get(api, name))

    # No change should happen, should return False
    assert not lxd.container_absent(api, lxd.container_get(api, name))
