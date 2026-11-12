#!/usr/bin/python
import os
import shutil
import subprocess
import tempfile
import time
from contextlib import suppress

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.text.converters import to_native


HTTP2_ERROR_CODES = (16, 92)    # CURLE_HTTP2, CURLE_HTTP2_STREAM


def curl_command(url, temp_path, dest_is_dir, timeout, headers, http_version=None):
    cmd = [
        "curl",
        "--fail",
        "--globoff",
        "--location",
        "--silent",
        "--show-error",
        "--connect-timeout",
        str(timeout),
    ]
    if http_version:
        cmd.append(f"--http{http_version}")
    if headers:
        for key, value in headers.items():
            cmd.extend(["-H", f"{key}: {value}"])
    if dest_is_dir:
        cmd.extend(["--output-dir", temp_path, "--remote-name", "--remote-header-name"])
    else:
        cmd.extend(["--output", temp_path])
    cmd.extend(["--write-out", "%{http_code}"])
    cmd.extend(["--url", url])
    return cmd


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

    if not dest:
        module.fail_json(msg="dest must not be empty", dest=dest, url=url)
    if retries < 0:
        module.fail_json(msg="retries must be >= 0", dest=dest, url=url)

    if dest.endswith('/'):
        try:
            if not module.check_mode:
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
        retry_max_time = 1200
        retry_start_time = None    # starts with the first retry, not the first attempt
        http_version = None    # internal only: fall back to HTTP/1.1 after an HTTP/2 error

        try:
            # The extra iteration is reserved for the HTTP/1.1 fallback attempt.
            for attempt in range(retries + 2):
                cmd = curl_command(url, temp_path, dest_is_dir, timeout, headers, http_version)
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                stdout, stderr = process.communicate()

                if process.returncode == 0:
                    break

                status = int(stdout) if stdout.strip().isdigit() else 0
                failure = {
                    "rc": process.returncode,
                    "stdout": stdout,
                    "stderr": stderr,
                    "attempts": attempt + 1,
                    "dest": dest,
                    "url": url,
                }
                if 400 <= status < 500 and status not in (408, 429):
                    # Permanent client errors must not be retried.
                    module.fail_json(msg="curl failed", **failure)

                if process.returncode in HTTP2_ERROR_CODES and not http_version:
                    # HTTP/2 stream failures are often caused by a proxy or
                    # server bug.  Retry immediately over HTTP/1.1, even if
                    # the retry budget is already exhausted.
                    http_version = "1.1"
                    continue

                # Always allow at least one retry, even if the first (possibly
                # very slow) attempt used up the retry time budget.
                now = time.monotonic()
                if retry_start_time is None:
                    retry_start_time = now
                elapsed = now - retry_start_time

                if attempt >= retries:
                    module.fail_json(msg="curl failed", **failure)
                if elapsed >= retry_max_time:
                    module.fail_json(msg="curl retry time exceeded", **failure)

                retry_delay = min(600, 2 ** min(attempt, 10), retry_max_time - elapsed)
                time.sleep(max(0, retry_delay))
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
