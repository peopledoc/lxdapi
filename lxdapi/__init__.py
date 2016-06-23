"""
lxdapi is just a module to help interfacing with the LXD API.

The purpose of this library is to expose wrappers to requests and
requests_unixsocket, encapsulating business logic that would be common to any
use case by facilitating HTTP transactions, with the :mod:`api`:

- url generation with parameters,
- waiting for an async operation to finish,
- lxd error handling,
- lxd HTTP transaction debugging helpers.

The purpose of this library is **not** to be a full blown framework
for interacting with lxd completely abstracting HTTP transactions in an
hermetic way. pylxd already does a good job at that. Instead, this library
helps integrating your own idempotent framework such as Ansible, SaltStack,
ansible-containers, and so on.

In addition, this library provides some basic shortcuts using idempotent logic
in the :mod:`shortcuts`. You'll probably want to use as much shortcuts as
possible so that you can concentrate on what makes the value of your code:
interfacing with another framework with idempotent principles.
"""
