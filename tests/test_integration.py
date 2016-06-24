import os

from lxdapi import lxd

api = lxd.API.factory()
busybox = os.path.join(
    os.path.dirname(__file__),
    'busybox.tar.xz'
)
busybox_fingerprint = lxd.image_get_fingerprint(busybox)
busybox_alias = 'lxdapitestbusybox'


def test_images():
    # Clean up
    lxd.image_absent(api, busybox_fingerprint)

    # Should upload the image
    assert lxd.image_present(api, busybox)

    # Should not do anything, return False
    assert not lxd.image_present(api, busybox)

    # Should tag the image with an alias
    assert lxd.image_alias_present(api, busybox_alias, busybox_fingerprint)

    # Should not do anything
    assert not lxd.image_alias_present(api, busybox_alias, busybox_fingerprint)

    # Should remove the image
    assert lxd.image_absent(api, busybox_fingerprint)

    # Should not do anything, return False
    assert not lxd.image_absent(api, busybox_fingerprint)


def test_container():
    lxd.image_present(api, busybox)
    lxd.image_alias_present(api, busybox_alias, busybox_fingerprint)

    name = 'lxdapi-test-container'
    config = dict(
        name=name,
        source=dict(
            type='image',
            protocol='lxd',
            alias=busybox_alias,
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
    assert lxd.container_apply_status(
        api,
        lxd.container_get(api, name),
        'Running'
    )

    # No change should happen, should return False
    assert not lxd.container_apply_status(
        api,
        lxd.container_get(api, name),
        'Running'
    )

    # Should destroy the container and return True
    assert lxd.container_absent(api, lxd.container_get(api, name))

    # No change should happen, should return False
    assert not lxd.container_absent(api, lxd.container_get(api, name))
