#!/usr/bin/python

from ansible.module_utils.basic import AnsibleModule
import os
import subprocess


def run_module():
    argument_spec = dict(
        url=dict(type='str', required=True),
        dest=dict(type='str', required=True),
        force=dict(type='bool', default=True),
        timeout=dict(type='int', default=60),
        retries=dict(type='int', default=10),
    )

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)
    args = module.params

    # Handle directory-to-filename logic similar to get_url
    # We rely on curl -J -O to determine the filename in the dest dir case
    is_dir = os.path.isdir(args['dest']) or args['dest'].endswith('/')
    if is_dir and not os.path.exists(args['dest']):
        os.makedirs(args['dest'])

    # Check if file exists for idempotency (creates-like behavior)
    if not args['force'] and os.path.exists(args['dest']):
        module.exit_json(changed=False, msg="File already exists", dest=args['dest'])

    cmd = [
        "curl",
        "-fL",
        "-C",
        "-",
        "--connect-timeout",
        str(args['timeout']),
        "--retry",
        str(args['retries']),
        "--retry-all-errors",
        "--retry-max-time",
        "1200",
    ]

    if is_dir:
        cmd.extend(["--output-dir", args['dest'], "-J", "-O"])
    else:
        cmd.extend(["-o", args['dest']])

    cmd.append(args['url'])

    if module.check_mode:
        module.exit_json(changed=True, msg="Download would be attempted (check mode)")

    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            module.fail_json(msg="curl failed", rc=process.returncode, stdout=stdout, stderr=stderr)

        module.exit_json(changed=True, dest=args['dest'], rc=0)
    except Exception as e:
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    run_module()
