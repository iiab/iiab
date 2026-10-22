#!/usr/bin/python
import hashlib
import os
import shutil
import subprocess
import tempfile
import time
from contextlib import suppress

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.text.converters import to_native


def checksum_for_file(path, algorithm):
    digest = hashlib.new(algorithm)
    with open(path, 'rb') as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def find_downloaded_file(temp_path, dest_is_dir, module, dest, url):
    if dest_is_dir:
        try:
            downloaded_file = [entry.path for entry in os.scandir(temp_path)]
        except OSError as e:
            module.fail_json(
                msg=f"Failed to locate downloaded file (temporary directory disappeared??): {to_native(e)}",
                dest=dest,
                url=url,
            )

        if not downloaded_file:
            module.fail_json(msg="No file was downloaded", dest=dest, url=url)
        if len(downloaded_file) > 1:
            module.fail_json(msg="More than one file was downloaded", dest=dest, url=url)
        return downloaded_file[0]

    if not os.path.exists(temp_path):
        module.fail_json(msg="No file was downloaded", dest=dest, url=url)
    return temp_path


def clear_temp_path(temp_path, dest_is_dir):
    if dest_is_dir:
        for entry in os.scandir(temp_path):
            if entry.is_dir(follow_symlinks=False):
                shutil.rmtree(entry.path)
            else:
                os.unlink(entry.path)
    else:
        with suppress(FileNotFoundError):
            os.remove(temp_path)


def run_module():
    argument_spec = dict(
        url=dict(type='str', required=True),
        dest=dict(type='path', required=True),
        tmp_dest=dict(type='path'),
        headers=dict(type='dict'),
        timeout=dict(type='int', default=60),
        retries=dict(type='int', default=10),
        force=dict(type='bool', default=False),
        checksum=dict(type='str'),
    )

    module = AnsibleModule(argument_spec=argument_spec, add_file_common_args=True, supports_check_mode=True)

    url = module.params['url']
    dest = module.params['dest']
    tmp_dest = module.params['tmp_dest']
    headers = module.params['headers']
    timeout = module.params['timeout']
    retries = module.params['retries']
    force = module.params['force']
    checksum = module.params['checksum']

    checksum_algorithm = None
    expected_checksum = None
    if checksum:
        try:
            checksum_algorithm, expected_checksum = checksum.split(':', 1)
        except ValueError:
            module.fail_json(
                msg="checksum must use the '<algorithm>:<checksum>' format",
                checksum=checksum,
                dest=dest,
                url=url,
            )

        checksum_algorithm = checksum_algorithm.lower()
        expected_checksum = expected_checksum.lower()
        try:
            digest_size = hashlib.new(checksum_algorithm).digest_size
        except ValueError:
            module.fail_json(
                msg=f"Unsupported checksum algorithm: {checksum_algorithm}",
                checksum=checksum,
                dest=dest,
                url=url,
            )
        if (
            len(expected_checksum) != digest_size * 2
            or any(character not in '0123456789abcdef' for character in expected_checksum)
        ):
            module.fail_json(
                msg=f"Invalid checksum for {checksum_algorithm}",
                checksum=checksum,
                dest=dest,
                url=url,
            )

    if dest.endswith('/'):
        try:
            os.makedirs(dest, exist_ok=True)
        except OSError as e:
            module.fail_json(msg=f"Failed to create final destination directory: {e}", dest=dest, url=url)

        dest_is_dir = True
    else:
        dest_is_dir = os.path.isdir(dest)

    if not dest_is_dir and os.path.exists(dest) and not force:
        checksum_matches = not checksum or checksum_for_file(dest, checksum_algorithm).lower() == expected_checksum
        if checksum_matches:
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

                if process.returncode != 0:
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
                    continue

                if checksum:
                    downloaded_file = find_downloaded_file(temp_path, dest_is_dir, module, dest, url)
                    actual_checksum = checksum_for_file(downloaded_file, checksum_algorithm).lower()
                    if actual_checksum != expected_checksum:
                        if attempt == retries:
                            module.fail_json(
                                msg="Checksum mismatch",
                                checksum=checksum,
                                actual_checksum=f"{checksum_algorithm}:{actual_checksum}",
                                dest=dest,
                                url=url,
                            )
                        clear_temp_path(temp_path, dest_is_dir)
                        elapsed = time.monotonic() - start_time
                        if elapsed >= retry_max_time:
                            module.fail_json(
                                msg="Checksum retry time exceeded",
                                checksum=checksum,
                                actual_checksum=f"{checksum_algorithm}:{actual_checksum}",
                                dest=dest,
                                url=url,
                            )
                        retry_delay = min(600, 2 ** min(attempt, 10), retry_max_time - elapsed)
                        time.sleep(retry_delay)
                        continue

                break
        except Exception as e:
            module.fail_json(msg=f"Failed to execute curl: {to_native(e)}", dest=dest, url=url)

        downloaded_file = find_downloaded_file(temp_path, dest_is_dir, module, dest, url)

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
