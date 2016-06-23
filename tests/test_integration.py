from lxdapi import lxd

def test_container():
    api = lxd.API.factory()['1.0']
    name = 'lxdapi-test-container'

    lxd.container_absent(api, name)

    lxd.container_apply(
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
        status='Running',
    )

    assert lxd.container_exists(api, name)
