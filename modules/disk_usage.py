#!/usr/bin/python
"""Return the used bytes of the filesystems holding one or more paths.

This replaces the shell idiom ``df -B1 --output=used / | tail -1``.  Passing
both ``/`` and ``content_base`` means content on a separate /library disk is
counted, and a path that does not exist yet is resolved to its nearest existing
ancestor so first-install measurements do not fail.
"""
import os

from ansible.module_utils.basic import AnsibleModule


def used_bytes(path):
    stat = os.statvfs(path)
    block_size = stat.f_frsize or stat.f_bsize
    return (stat.f_blocks - stat.f_bfree) * block_size


def resolve(path):
    path = os.path.abspath(os.path.expanduser(path))
    while not os.path.exists(path):
        parent = os.path.dirname(path)
        if parent == path:
            return None
        path = parent
    return path


def run_module():
    module = AnsibleModule(
        argument_spec=dict(
            path=dict(type='path', default='/'),
            paths=dict(type='list', elements='path', default=[]),
        ),
        supports_check_mode=True,
    )

    requested = module.params['paths'] or [module.params['path']]
    mounts = {}
    details = []

    for requested_path in requested:
        resolved = resolve(requested_path)
        if resolved is None:
            module.fail_json(
                msg=f"Could not find an existing ancestor of {requested_path}"
            )
        stat = os.stat(resolved)
        used = used_bytes(resolved)
        mounts[stat.st_dev] = used
        details.append(
            dict(path=requested_path, resolved=resolved, used=used)
        )

    module.exit_json(
        changed=False,
        used=sum(mounts.values()),
        mounts=details,
    )


if __name__ == '__main__':
    run_module()
