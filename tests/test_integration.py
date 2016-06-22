from pylxd_light import lxd


def test_container_state_started_idempotence():
    api = lxd.API()

    def container_started():
        return api.container_apply(
            config=dict(
                name='bloa',
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

    assert container_started().changed == True
    assert container_started().changed == False
