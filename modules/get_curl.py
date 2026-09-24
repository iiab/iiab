#!/usr/bin/python
import os
import shutil
import subprocess
import tempfile
import time
from contextlib import suppress

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.text.converters import to_native


def run_module():
    argument_spec = dict(
        url=dict(type='str', required=True),
        dest=dict(type='path', required=True),
        tmp_dest=dict(type='path'),
        headers=dict(type='dict'),
        timeout=dict(type='int', default=60),
        retries=dict(type='int', default=10),
        force=dict(type='bool', default=False),
    )

    module = AnsibleModule(argument_spec=argument_spec, add_file_common_args=True, supports_check_mode=True)

    url = module.params['url']
    dest = module.params['dest']
    tmp_dest = module.params['tmp_dest']
    headers = module.params['headers']
    timeout = module.params['timeout']
    retries = module.params['retries']
    force = module.params['force']

    if dest.endswith('/'):
        try:
            os.makedirs(dest, exist_ok=True)
        except OSError as e:
            module.fail_json(msg=f"Failed to create final destination directory: {e}", dest=dest, url=url)

        dest_is_dir = True
    else:
        dest_is_dir = os.path.isdir(dest)

    if not dest_is_dir and os.path.exists(dest) and not force:
        # File exists and not forcing, just update attributes
        file_args = module.load_file_common_arguments(module.params, path=dest)
        changed = module.set_fs_attributes_if_different(file_args, changed=False)
        msg = "File already exists"
        if changed:
            msg += ", updated attributes"
        module.exit_json(msg=msg, dest=dest, url=url, changed=changed)

    if module.check_mode:
        module.exit_json(changed=True, msg="Download would be attempted (check mode)", dest=dest, url=url)

    if tmp_dest:
        if not os.path.isdir(tmp_dest):
            module.fail_json(msg=f"tmp_dest must be a directory: {tmp_dest}", dest=dest, url=url)
        temp_dir = tmp_dest
    else:
        temp_dir = module.tmpdir

    # Create temporary file/directory for download
    try:
        temp_path = tempfile.mkdtemp(dir=temp_dir)
        if not dest_is_dir:
            temp_path = os.path.join(temp_path, os.path.basename(dest))
    except Exception as e:
        module.fail_json(msg=f"Failed to create temporary location: {to_native(e)}", dest=dest, url=url)

    try:
        cmd = [
            "curl",
            "--fail",
            "--location",
            "--connect-timeout",
            str(timeout),
        ]
        if headers:
            for key, value in headers.items():
                cmd.extend(["-H", f"{key}: {value}"])
        if dest_is_dir:
            cmd.extend(["--output-dir", temp_path, "--remote-name", "--remote-header-name"])
        else:
            cmd.extend(["--output", temp_path])
        cmd.extend(["--write-out", "%{http_code}"])
        cmd.append(url)

        try:
            retry_max_time = 1200
            start_time = time.monotonic()
            for attempt in range(retries + 1):
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                stdout, stderr = process.communicate()

                if process.returncode == 0:
                    break

                if stdout.strip() == "404" or attempt == retries:
                    module.fail_json(
                        msg="curl failed", rc=process.returncode, stdout=stdout, stderr=stderr, dest=dest, url=url
                    )

                elapsed = time.monotonic() - start_time
                if elapsed >= retry_max_time:
                    module.fail_json(
                        msg="curl retry time exceeded",
                        rc=process.returncode,
                        stdout=stdout,
                        stderr=stderr,
                        dest=dest,
                        url=url,
                    )

                retry_delay = min(600, 2 ** min(attempt, 10), retry_max_time - elapsed)
                time.sleep(retry_delay)
        except Exception as e:
            module.fail_json(msg=f"Failed to execute curl: {to_native(e)}", dest=dest, url=url)

        if dest_is_dir:
            # Find the downloaded file(s) in temp directory
            try:
                downloaded_file = [entry.path for entry in os.scandir(temp_path)]
            except Exception as e:
                module.fail_json(
                    msg=f"Failed to locate downloaded file (temporary directory disappeared??): {to_native(e)}",
                    dest=dest,
                    url=url,
                )

            if not downloaded_file:
                module.fail_json(msg="No file was downloaded", dest=dest, url=url)
            if len(downloaded_file) > 1:
                module.fail_json(msg="More than one file was downloaded", dest=dest, url=url)
            downloaded_file = downloaded_file[0]
        else:
            if not os.path.exists(temp_path):
                module.fail_json(msg="No file was downloaded", dest=dest, url=url)
            downloaded_file = temp_path

        try:
            if dest_is_dir:
                dest = os.path.join(dest, os.path.basename(downloaded_file))

            module.atomic_move(downloaded_file, dest)

            # Set file attributes (mode, owner, group, etc.)
            file_args = module.load_file_common_arguments(module.params, path=dest)
            module.set_fs_attributes_if_different(file_args, changed=True)
        except Exception as e:
            module.fail_json(msg=f"Failed to move file to destination: {to_native(e)}", dest=dest, url=url)

        module.exit_json(msg="File downloaded successfully", dest=dest, url=url, changed=True)
    finally:
        with suppress(Exception):
            if dest_is_dir:
                shutil.rmtree(temp_path, ignore_errors=True)
            else:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                os.rmdir(os.path.dirname(temp_path))


if __name__ == '__main__':
    run_module()
