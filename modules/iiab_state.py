#!/usr/bin/python
"""Read and write IIAB state markers.

The state file stays a flat YAML mapping (``awstats_installed: True``), so
``vars_files``, shell greps, and image fixtures keep working.  Writes go
through this module instead of ``lineinfile``: the whole file is read, changed,
and written back.  Unrelated keys, their order, and the leading comment block
are preserved; booleans stay ``True``/``False``.

Use the module for single markers::

    - name: Record AWStats installed
      iiab_state:
        key: awstats_installed
        state: absent          # remove it instead

The companion ``./scripts/iiab-state`` exposes the same operations to shell
code, and ``lookup_plugins/installed.py`` reuses the parsing helpers below, so
all three read the file the same way.
"""

from __future__ import annotations

import fcntl
import os
import stat
import tempfile
from contextlib import contextmanager, nullcontext

import yaml

try:
    from ansible.module_utils.basic import AnsibleModule
except ImportError:    # Allows ./scripts/iiab-state to import the helpers.
    AnsibleModule = None


DEFAULT_PATH = os.environ.get("IIAB_STATE_FILE") or "/etc/iiab/iiab_state.yml"
DEFAULT_HEADER = """\
# DO *NOT* MANUALLY EDIT THIS, THANKS!
# Managed by modules/iiab_state.py and ./scripts/iiab-state.
# iiab-state-format: 1
# IIAB installs apps and services. './runrole --uninstall' works only for roles
# that implement the uninstall operation.
"""

MARKER_SUFFIXES = ("_installed", "_downloaded")


class StateError(Exception):
    """The state file is not a flat YAML mapping."""


class StateDumper(yaml.SafeDumper):
    """Emit Python-style booleans, matching the historical state file."""


def _represent_bool(dumper, value):
    return dumper.represent_scalar(
        "tag:yaml.org,2002:bool", "True" if value else "False"
    )


StateDumper.add_representer(bool, _represent_bool)


def split_header(text):
    """Return (leading comment block, rest of file)."""
    lines = text.splitlines(keepends=True)
    index = 0
    while index < len(lines):
        stripped = lines[index].lstrip()
        if stripped and not stripped.startswith("#"):
            break
        index += 1
    return "".join(lines[:index]), "".join(lines[index:])


def load_state(path=DEFAULT_PATH):
    """Return (state mapping, leading comment block).

    A missing or empty file is a valid empty state.  A file whose top level is
    not a mapping is an error: silently ignoring it would make every role
    reinstall, which is worse than a clear failure.
    """
    try:
        with open(path, encoding="utf-8") as stream:
            text = stream.read()
    except FileNotFoundError:
        return {}, ""
    except OSError as error:
        raise StateError(f"Could not read {path}: {error}") from error

    header, body = split_header(text)
    try:
        data = yaml.safe_load(body) if body.strip() else {}
    except yaml.YAMLError as error:
        raise StateError(f"Could not parse {path}: {error}") from error

    if data is None:
        data = {}
    if not isinstance(data, dict):
        raise StateError(f"{path} must contain a YAML mapping, not {type(data).__name__}")
    for key in data:
        if not isinstance(key, str):
            raise StateError(f"{path} has a non-string key: {key!r}")

    return data, header


def dump_state(data, header="", include_header=True):
    """Serialize a state mapping, preserving the historical boolean spelling."""
    body = ""
    if data:
        body = yaml.dump(
            data,
            Dumper=StateDumper,
            sort_keys=False,
            default_flow_style=False,
            allow_unicode=True,
            width=1000,
        )
        if not body.endswith("\n"):
            body += "\n"

    if not include_header:
        return body
    if not header:
        header = DEFAULT_HEADER
    if header and not header.endswith("\n"):
        header += "\n"
    return header + body


@contextmanager
def state_lock(path=DEFAULT_PATH):
    """Hold an exclusive lock while one caller changes the state file."""
    directory = os.path.dirname(os.path.abspath(path)) or "."
    os.makedirs(directory, exist_ok=True)
    lock_path = os.path.join(directory, "." + os.path.basename(path) + ".lock")
    with open(lock_path, "a+", encoding="utf-8") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def write_state(path, data, header=""):
    """Write *data* to *path*."""
    directory = os.path.dirname(os.path.abspath(path)) or "."
    os.makedirs(directory, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=".iiab_state.", suffix=".tmp", dir=directory, text=True
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(dump_state(data, header))
            stream.flush()
            os.fsync(stream.fileno())

        try:
            existing = os.stat(path)
        except FileNotFoundError:
            existing = None

        if existing is None:
            os.chmod(temporary, 0o644)
        else:
            os.chmod(temporary, stat.S_IMODE(existing.st_mode))
            if os.geteuid() == 0:
                os.chown(temporary, existing.st_uid, existing.st_gid)

        os.replace(temporary, path)
        temporary = None

        try:
            directory_fd = os.open(directory, os.O_RDONLY)
        except OSError:
            return
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if temporary is not None:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass


def marker_keys(state, prefix):
    """Return the marker keys for *prefix*: ``prefix_installed``, etc."""
    return [
        key
        for key in state
        if key.startswith(prefix + "_") and key.endswith(MARKER_SUFFIXES)
    ]


def coerce_value(value):
    """Treat quoted booleans as booleans, leaving other strings alone."""
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in ("true", "yes", "on"):
            return True
        if lowered in ("false", "no", "off"):
            return False
    return value


def change_state(
    path=DEFAULT_PATH,
    state="present",
    key=None,
    keys=None,
    value=True,
    write=True,
):
    """Apply one change and return a result dictionary.

    ``state='present'`` sets *key* (or every key in *keys*) to *value*.
    ``state='absent'`` removes *key* or every key in *keys*.  Marker names
    are exact; prefix matching belongs to callers such as the CLI.
    """
    keys = list(keys or [])
    targets = []
    if key is not None:
        targets.append(key)
    targets.extend(keys)
    if not targets:
        raise StateError("One of key or keys is required.")

    lock = state_lock(path) if write else nullcontext()
    with lock:
        data, header = load_state(path)
        before = dict(data)
        removed = []

        if state == "present":
            for target in targets:
                data[target] = coerce_value(value)
        elif state == "absent":
            removed = [target for target in targets if target in data]
            for target in removed:
                del data[target]
        else:
            raise StateError(f"Unsupported state: {state}")

        changed = data != before
        if changed and write:
            write_state(path, data, header)

        return {
            "changed": changed,
            "path": path,
            "state": state,
            "before": before,
            "after": data,
            "removed": removed,
        }


def run_module():
    module = AnsibleModule(
        argument_spec=dict(
            path=dict(type="path", default=DEFAULT_PATH),
            state=dict(type="str", choices=["present", "absent"], default="present"),
            key=dict(type="str"),
            keys=dict(type="list", elements="str", default=[]),
            value=dict(type="raw", default=True),
        ),
        supports_check_mode=True,
    )

    try:
        result = change_state(
            path=module.params["path"],
            state=module.params["state"],
            key=module.params["key"],
            keys=module.params["keys"],
            value=module.params["value"],
            write=not module.check_mode,
        )
    except (OSError, StateError) as error:
        module.fail_json(msg=str(error))

    answer = {
        "changed": result["changed"],
        "path": result["path"],
        "state": result["state"],
        "removed": result["removed"],
    }
    if result["changed"]:
        answer["diff"] = {
            "before": dump_state(result["before"], include_header=False),
            "after": dump_state(result["after"], include_header=False),
        }
    module.exit_json(**answer)


if __name__ == "__main__":
    run_module()
