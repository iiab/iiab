#!/usr/bin/env python3
"""Run role lifecycle scenarios against a virtual Ansible environment.

Besides the scenarios, task files are scanned for lifecycle warnings: network
work in a phase that must stay offline, offline phases that include a phase
which may use the network, unsafe state checks, and state writes in the wrong
phase. The scenarios also seed a role's declared user data and check that every
runrole operation keeps it. Warnings are reported but do not fail the run
unless --strict is used; a reference to the removed clean_install variable
always fails.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import NamedTuple

import jinja2
import yaml
from jinja2 import meta as jinja_meta

ROOT_DIR = Path(__file__).resolve().parents[1]
ACTIVE_STATES = {"started", "restarted", "reloaded"}
BASELINE_SERVICES = {"nginx", "dnsmasq"}

# scripts/role_lifecycle.py is the single source of truth for role names,
# variable prefixes, and capabilities; ./runrole and ./runroles call the same
# code through its CLI.
_SPEC = importlib.util.spec_from_file_location(
    "iiab_role_lifecycle", ROOT_DIR / "scripts" / "role_lifecycle.py"
)
if _SPEC is None or _SPEC.loader is None:
    raise SystemExit("could not load scripts/role_lifecycle.py")
role_lifecycle = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(role_lifecycle)


def role_var(role: str) -> str:
    return role_lifecycle.role_var(role)


def role_supports(role: str, feature: str) -> bool:
    return role_lifecycle.supports(role, feature)


def available_roles() -> list[str]:
    return role_lifecycle.available_roles()


# Services supplied by a package but referenced through a loop or a computed
# variable that role_service_names() cannot resolve statically.
ROLE_EXTRA_SERVICES = {
    "cups": {"cups", "cups-browsed"},
    "luanti": {"luanti-server", "minetest-server"},
    "samba": {"smbd", "nmbd"},
}

# Task files executed by the lifecycle runner. Only these need phase-aware
# checks; helper files are reached through them. enable-or-disable is a legacy
# convention outside the formal contract, but the runner still executes it, so
# it is checked too.
LIFECYCLE_FILES = {
    "main",
    "uninstall",
    "install",
    "configure",
    "state",
    "enable-or-disable",
}

# install.yml and configure.yml may use the network. Everything else must work
# offline: --uninstall has to be retryable on a disconnected host, and main.yml
# only dispatches to the phase that owns the work.
OFFLINE_PHASES = {
    "main",
    "uninstall",
    "state",
    "enable-or-disable",
}

# Phases that may use the network, and must therefore only run when the role
# dispatches to them deliberately.
NETWORK_PHASES = {"install"}


PACKAGE_MODULES = {"apt", "apk", "dnf", "package", "pacman", "yum", "zypper"}
INSTALLER_MODULES = {"composer", "gem", "npm", "pnpm", "pip", "pip3", "snap", "yarn"}
SHELL_MODULES = {"command", "raw", "shell"}
INCLUDE_MODULES = {"include", "include_tasks", "import_tasks"}

LIFECYCLE_DIRECTIVE = re.compile(
    r"#\s*lifecycle:\s*(?P<rule>allow-network)\b", re.IGNORECASE
)

NETWORK_COMMAND = re.compile(
    r"(?:^|[\s;&|(`])(?:"
    r"curl|wget|"
    r"git\s+(?:clone|fetch|ls-remote|pull|submodule\s+update)|"
    r"(?:python[0-9.]*\s+-m\s+)?pip[0-9.]*\s+(?:download|install|wheel)|"
    r"(?:apt|apt-get|aptitude)\s+(?:build-dep|dist-upgrade|install|reinstall|update|upgrade)|"
    r"(?:dnf|yum)\s+(?:install|makecache|update|upgrade)|"
    r"zypper\s+(?:install|refresh|update|up)|"
    r"pacman\s+-S|"
    r"(?:npm|pnpm|yarn)\s+(?:add|ci|install|update)|"
    r"(?:gem|snap)\s+(?:install|refresh|update)"
    r")\b",
    re.IGNORECASE,
)

LIFECYCLE_HINTS = {
    "main": "tasks/main.yml should only validate and dispatch; move the work to install.yml or configure.yml",
    "uninstall": "uninstall.yml must work offline; move the fetch to install.yml",
    "install": "install.yml should not run configure.yml; main.yml owns the phase order",
    "configure": "configure.yml should not install the program; move that work to install.yml",
    "state": "state.yml only records settings",
    "enable-or-disable": "enable-or-disable.yml only toggles services",
}

# Phases that main.yml must only include conditionally.
GATED_PHASES = {
    "uninstall": "uninstall.yml must only run when uninstall is set; add a when: guard",
}

TASK_KEYWORDS = {
    "__line__",
    "action",
    "always",
    "any_errors_fatal",
    "args",
    "async",
    "become",
    "become_exe",
    "become_flags",
    "become_method",
    "become_user",
    "block",
    "changed_when",
    "check_mode",
    "collections",
    "connection",
    "debugger",
    "delay",
    "delegate_facts",
    "delegate_to",
    "diff",
    "environment",
    "failed_when",
    "ignore_errors",
    "ignore_unreachable",
    "listen",
    "local_action",
    "loop",
    "loop_control",
    "module_defaults",
    "name",
    "no_log",
    "notify",
    "poll",
    "port",
    "register",
    "remote_user",
    "rescue",
    "retries",
    "run_once",
    "tags",
    "throttle",
    "timeout",
    "until",
    "vars",
    "when",
    "with_dict",
    "with_fileglob",
    "with_first_found",
    "with_flattened",
    "with_items",
    "with_nested",
    "with_sequence",
    "with_subelements",
    "with_together",
}
MOCK_MODULE_SOURCE = r'''#!/usr/bin/python3
import ast
import copy
import json
import os
import posixpath
import re
import shlex
import sys


def module_name():
    name = os.path.basename(sys.argv[0])
    return name[len("AnsiballZ_") :] if name.startswith("AnsiballZ_") else name


def decode(value):
    try:
        return ast.literal_eval(value)
    except (SyntaxError, ValueError):
        return value


def module_args():
    if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
        with open(sys.argv[1], encoding="utf-8") as args_file:
            text = args_file.read()
        if text.startswith("{"):
            return json.loads(text).get("ANSIBLE_MODULE_ARGS", {})
        # Ansible writes some argument files as shell-like key=value text
        # (e.g. command with cmd/creates), where values may be quoted and
        # contain spaces. Shlex keeps those values intact; the previous regex
        # stopped at the first space and truncated commands such as pip install.
        try:
            tokens = shlex.split(text)
        except ValueError:
            tokens = text.split()
        args = {}
        for token in tokens:
            key, separator, value = token.partition("=")
            if separator and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key):
                args[key] = decode(value)
        return args
    return {}


def load_state():
    state_file = os.environ["IIAB_MOCK_STATE"]
    if os.path.isfile(state_file):
        with open(state_file, encoding="utf-8") as stream:
            return json.load(stream)
    return {"paths": {}, "services": {}}


def save_state(state):
    with open(os.environ["IIAB_MOCK_STATE"], "w", encoding="utf-8") as stream:
        json.dump(state, stream)


def finish(state, **result):
    save_state(state)
    print(json.dumps(result))
    raise SystemExit(0)


def fail(state, message):
    finish(state, failed=True, changed=False, msg=message)


def exists(state, path):
    prefix = path.rstrip("/") + "/"
    return path in state["paths"] or any(
        item.startswith(prefix) for item in state["paths"]
    )


def unit_path(service):
    suffixes = (
        ".service",
        ".socket",
        ".timer",
        ".path",
        ".target",
        ".mount",
        ".automount",
        ".swap",
        ".device",
        ".slice",
        ".scope",
    )
    suffix = "" if service.endswith(suffixes) else ".service"
    return f"/etc/systemd/system/{service}{suffix}"


def create(state, path, kind="file"):
    changed = not exists(state, path)
    state["paths"][path] = kind
    return changed


# Packages that ship systemd units the roles look for. Installing one of these
# packages materializes its units, just like the package manager would.
PACKAGE_UNITS = {
    "uwsgi": (
        "/lib/systemd/system/uwsgi-app@.service",
        "/lib/systemd/system/uwsgi-app@.socket",
    ),
}


def install_packages(state, args):
    names = args.get("name") or args.get("pkg") or args.get("package") or []
    if isinstance(names, str):
        names = [names]
    requested = str(args.get("state") or "present").lower()
    changed = False
    packages = state.setdefault("packages", {})
    for package in names:
        package = str(package).split("=", 1)[0]
        if requested in {"absent", "removed", "purged"}:
            if packages.pop(package, None) is not None:
                changed = True
            continue
        if packages.get(package) != "present":
            packages[package] = "present"
            changed = True
        for path in PACKAGE_UNITS.get(package, ()):
            changed = create(state, path) or changed
    return changed


def seed_user_data(state, args):
    paths = args.get("paths") or []
    databases = args.get("databases") or []
    if isinstance(paths, str):
        paths = [paths]
    if isinstance(databases, str):
        databases = [databases]
    paths = [str(path) for path in paths if path]
    databases = [str(database) for database in databases if database]
    for path in paths:
        create(state, path, "directory" if path.endswith("/") else "file")
    for database in databases:
        state.setdefault("databases", {})[database] = "present"
    state["user_data"] = {"paths": paths, "databases": databases}


def remove(state, path):
    prefix = path.rstrip("/") + "/"
    paths = [
        item
        for item in state["paths"]
        if item == path or item.startswith(prefix)
    ]
    for item in paths:
        del state["paths"][item]
    return bool(paths)


def record_service(state, name, enabled=None, service_state=None):
    service = state["services"].setdefault(
        name, {"enabled": False, "state": "stopped"}
    )
    if enabled is not None:
        service["enabled"] = enabled
    if service_state:
        service["state"] = service_state
    state.setdefault("events", []).append(
        {
            "phase": os.environ.get("IIAB_MOCK_PHASE"),
            "name": name,
            "enabled": enabled,
            "state": service_state,
        }
    )


def command_result(state, args):
    command = args.get("_raw_params") or args.get("cmd") or ""
    creates = args.get("creates")
    if creates and exists(state, creates):
        finish(state, changed=False, skipped=True, rc=0, stdout="", stderr="")
    if creates:
        create(state, creates)

    try:
        words = shlex.split(command)
    except ValueError:
        words = command.split()

    # Simulate the download destinations of the common command-line fetchers.
    if words and words[0] in {"wget", "curl"}:
        for flag in ("-O", "--output-document", "-o", "--output"):
            if flag in words:
                index = words.index(flag)
                if index + 1 < len(words):
                    create(state, words[index + 1])

    if "systemctl" in command or re.search(r"(^|\s)service\s", command):
        actions = {
            "start": "started",
            "restart": "restarted",
            "reload": "reloaded",
            "stop": "stopped",
        }
        for index, word in enumerate(words):
            if word in actions and index + 1 < len(words):
                record_service(
                    state,
                    words[index + 1],
                    service_state=actions[word],
                )
            elif word == "enable" and index + 1 < len(words):
                record_service(state, words[index + 1], enabled=True)
            elif word == "disable" and index + 1 < len(words):
                record_service(state, words[index + 1], enabled=False)
        finish(state, changed=False, rc=0, stdout="", stderr="")

    if "dpkg-query" in command:
        stdout = "installed"
    elif "rev-parse" in command:
        stdout = "mock-commit"
    elif "describe --tags" in command:
        stdout = "v0.1.5"
    elif "remote get-url" in command:
        stdout = "https://example.invalid/iiab-test-repo.git"
    elif "--version" in command:
        stdout = "Python 3.14.0"
    elif "df " in command:
        stdout = "1000"
    elif "ls /sys/class/net |" in command:
        stdout = "1"
    elif "is-active" in command:
        stdout = "active"
    elif "pip install" in command:
        stdout = "Successfully installed iiab-test-package"
    else:
        stdout = ""
    finish(state, changed=False, rc=0, stdout=stdout, stderr="")


def main():
    name = module_name()
    args = module_args()
    state = load_state()

    if name == "stat":
        path = args.get("path", "")
        installed = os.environ.get("IIAB_MOCK_INSTALLED") == "true"
        finish(
            state,
            changed=False,
            stat={
                "exists": exists(state, path) or installed,
                "isdir": state["paths"].get(path) == "directory",
                "size": 0,
                "islnk": False,
            },
        )

    if name in {
        "file",
        "template",
        "copy",
        "get_curl",
        "lineinfile",
        "blockinfile",
        "replace",
        "ini_file",
    }:
        path = args.get("path") or args.get("dest") or args.get("name")
        if not path:
            fail(state, f"{name} mock needs a path or destination")
        if name in {"template", "copy"} and path.endswith("/"):
            path = posixpath.join(path, posixpath.basename(args.get("src", "")))
        if name == "get_curl" and args.get("url"):
            url_name = posixpath.basename(str(args["url"]).split("?")[0])
            dest_is_dir = path.endswith("/") or state["paths"].get(path) == "directory"
            if (
                not dest_is_dir
                and url_name
                and not posixpath.splitext(path.rstrip("/"))[1]
            ):
                dest_is_dir = True
            if dest_is_dir:
                dest_dir = path.rstrip("/")
                if dest_dir:
                    create(state, dest_dir, "directory")
                path = posixpath.join(path, url_name)
        if args.get("state") == "absent":
            changed = remove(state, path)
        else:
            kind = "directory" if args.get("state") == "directory" else "file"
            changed = create(state, path, kind)
            if name == "template" and path.startswith("/etc/systemd/system/"):
                for service in state.get("expected_services", []):
                    changed = create(state, unit_path(service)) or changed
        finish(state, changed=changed, path=path, dest=path)

    if name in {"group", "user"}:
        finish(state, changed=False)

    if name == "disk_usage":
        finish(state, changed=False, used=1000, mounts=[])

    if name == "git":
        destination = args.get("dest")
        create(state, destination, "directory")
        create(state, posixpath.join(destination, ".git"), "directory")
        finish(state, changed=True, after="mock-commit")

    if name == "get_url":
        dest = args.get("dest") or args.get("path")
        url = str(args.get("url", ""))
        url_name = posixpath.basename(url.split("?")[0])
        dest_is_dir = bool(dest) and (
            dest.endswith("/") or state["paths"].get(dest) == "directory"
        )
        if (
            dest
            and not dest_is_dir
            and url_name
            and not posixpath.splitext(dest.rstrip("/"))[1]
        ):
            dest_is_dir = True
        if dest and dest_is_dir:
            dest_dir = dest.rstrip("/")
            if dest_dir:
                create(state, dest_dir, "directory")
            if url_name:
                dest = posixpath.join(dest, url_name)
        if dest:
            create(state, dest)
        finish(state, changed=False, dest=dest)

    if name in {
        "apt",
        "apk",
        "dnf",
        "package",
        "pacman",
        "yum",
        "zypper",
    }:
        finish(state, changed=install_packages(state, args))

    if name in {
        "unarchive",
        "mount",
        "sysctl",
        "mariadb_user",
        "postgresql_user",
    }:
        finish(state, changed=False)

    if name in {"mariadb_db", "postgresql_db"}:
        database = args.get("name")
        if database:
            state.setdefault("databases", {})[str(database)] = str(
                args.get("state", "present")
            ).lower()
        finish(state, changed=False)

    if name == "mock_user_data":
        seed_user_data(state, args)
        finish(state, changed=False)

    if name in {"command", "shell"}:
        command_result(state, args)

    if name == "uri":
        status = 302 if str(args.get("method", "GET")).upper() == "POST" else 200
        finish(
            state,
            changed=False,
            status=status,
            url=args.get("url", ""),
            attempts=1,
            cookies={"MATOMO_SESSID": "mock"},
            content='{"tag_name": "v0.1.5"}',
        )

    if name in {"systemd", "systemd_service", "service"}:
        if not args.get("name"):
            finish(state, changed=False)
        service = args["name"]
        installed = os.environ.get("IIAB_MOCK_INSTALLED") == "true"
        unit = unit_path(service)
        available = service in state.get("available_services", [])
        if not installed and service not in state["services"] and not exists(state, unit):
            if not available:
                fail(state, f"service {service} is not installed")
        record_service(
            state,
            service,
            enabled=args.get("enabled"),
            service_state=args.get("state"),
        )
        finish(state, changed=False)

    if name == "mock_checkpoint":
        snapshot = args.get("snapshot")
        state.setdefault("snapshots", {})[snapshot] = {
            "paths": copy.deepcopy(state["paths"]),
            "services": copy.deepcopy(state["services"]),
        }
        finish(state, changed=False)

    if name in {"raw", "script"}:
        fail(state, f"{name} execution is disabled in lifecycle tests")

    finish(state, changed=False)


if __name__ == "__main__":
    main()
'''

MOCK_MODULE_ACTION_SOURCE = r'''from __future__ import annotations

import importlib.util
import io
import json
import os
import sys
from contextlib import redirect_stdout
from pathlib import Path

from ansible.plugins.action import ActionBase

# The same mock implementation is used both as a module (fallback, and for
# collection-qualified modules) and through action plugins.  Action plugins
# run in the ansible-playbook process, so they avoid spawning a new Python
# interpreter for every mocked task.  That is the difference between a CI run
# that fits in a few minutes and one that oversubscribes a single-vCPU runner.
MOCK_MODULE = "_iiab_lifecycle_mock_module"


def load_mock_module():
    module = sys.modules.get(MOCK_MODULE)
    if module is not None:
        return module
    library = Path(os.environ["ANSIBLE_LIBRARY"])
    path = library.parent / "mock-module.py"
    spec = importlib.util.spec_from_file_location(MOCK_MODULE, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[MOCK_MODULE] = module
    spec.loader.exec_module(module)
    return module


class ActionModule(ActionBase):
    def run(self, tmp=None, task_vars=None):
        # A few roles put async on service writes; the mock is instant.
        self._supports_async = True
        self._supports_check_mode = True
        result = super().run(tmp, task_vars)
        task_vars = task_vars or {}
        name = self._task.action.rsplit(".", 1)[-1]
        module = load_mock_module()
        args = dict(self._task.args)
        module.module_name = lambda: name
        module.module_args = lambda: args

        # Play-level environment reaches modules, but action plugins run in
        # the controller.  Pass the mock settings through play vars instead so
        # each play can use its own state file.
        overrides = {}
        for env_name, var_name in (
            ("IIAB_MOCK_STATE", "iiab_mock_state"),
            ("IIAB_MOCK_INSTALLED", "iiab_mock_installed"),
            ("IIAB_MOCK_PHASE", "iiab_mock_phase"),
        ):
            if var_name in task_vars:
                overrides[env_name] = os.environ.get(env_name)
                os.environ[env_name] = str(task_vars[var_name])

        output = io.StringIO()
        code = 0
        try:
            with redirect_stdout(output):
                module.main()
        except SystemExit as error:
            code = error.code if isinstance(error.code, int) else 0
        finally:
            for env_name, value in overrides.items():
                if value is None:
                    os.environ.pop(env_name, None)
                else:
                    os.environ[env_name] = value

        text = output.getvalue().strip()
        if text:
            try:
                result.update(json.loads(text))
            except json.JSONDecodeError:
                result.update(failed=True, msg=text)
        # Ansible's built-in command/shell action plugins add these lines.
        # Roles read stdout_lines, so keep the same shape.
        if "stdout" in result and "stdout_lines" not in result:
            result["stdout_lines"] = str(result["stdout"]).splitlines()
        if "stderr" in result and "stderr_lines" not in result:
            result["stderr_lines"] = str(result["stderr"]).splitlines()
        if code:
            result["failed"] = True
        return result
'''

MOCK_ACTION_SOURCE = r'''from __future__ import annotations

import json
import os
import posixpath

from ansible.plugins.action import ActionBase


def state_path(task_vars):
    return (task_vars or {}).get("iiab_mock_state") or os.environ["IIAB_MOCK_STATE"]


def unit_path(service):
    suffixes = (
        ".service",
        ".socket",
        ".timer",
        ".path",
        ".target",
        ".mount",
        ".automount",
        ".swap",
        ".device",
        ".slice",
        ".scope",
    )
    suffix = "" if service.endswith(suffixes) else ".service"
    return f"/etc/systemd/system/{service}{suffix}"


class ActionModule(ActionBase):
    def run(self, tmp=None, task_vars=None):
        result = super().run(tmp, task_vars)
        args = self._task.args
        path = args.get("dest") or args.get("path")
        if not path:
            result.update(failed=True, msg="mock action needs a destination")
            return result

        state_file = state_path(task_vars)
        with open(state_file, encoding="utf-8") as stream:
            state = json.load(stream)
        if path.endswith("/"):
            path = posixpath.join(path, posixpath.basename(args.get("src", "")))
        changed = path not in state["paths"]
        state["paths"][path] = "file"
        if path.startswith("/etc/systemd/system/"):
            for service in state.get("expected_services", []):
                unit = unit_path(service)
                if unit not in state["paths"]:
                    state["paths"][unit] = "file"
                    changed = True
        with open(state_file, "w", encoding="utf-8") as stream:
            json.dump(state, stream)
        result.update(changed=changed, path=path)
        return result
'''

MOCK_INCLUDE_VARS_ACTION_SOURCE = r'''from __future__ import annotations

import json
import os
from pathlib import Path

import yaml

from ansible.plugins.action import ActionBase


def load_data(path: Path):
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".json":
        return json.loads(text)
    return yaml.safe_load(text)


class ActionModule(ActionBase):
    def run(self, tmp=None, task_vars=None):
        result = super().run(tmp, task_vars)
        args = self._task.args
        filename = args.get("file")
        name = args.get("name")
        data = {}
        if filename:
            path = Path(filename)
            if path.is_file():
                data = load_data(path)
            else:
                # Mock downloads live in IIAB_MOCK_STATE, not on disk. Fall
                # back to a real data file shipped alongside the role.
                role = getattr(self._task, "_role", None)
                role_path = Path(getattr(role, "_role_path", "."))
                candidates = []
                if role_path.is_dir():
                    candidates.extend(sorted(role_path.glob("*.json")))
                    candidates.extend(sorted((role_path / "files").glob("*.json")))
                lifecycle_root = os.environ.get("IIAB_LIFECYCLE_ROOT")
                if name == "maps_catalog" and lifecycle_root:
                    candidates.append(
                        Path(lifecycle_root) / "roles" / "maps" / "maps-catalog.json"
                    )
                for candidate in candidates:
                    if candidate.is_file():
                        data = load_data(candidate)
                        break
        if name:
            result["ansible_facts"] = {name: data}
        elif isinstance(data, dict):
            result["ansible_facts"] = data
        result["changed"] = False
        result["ansible_included_var_files"] = []
        return result
'''

MOCK_NORMAL_ACTION_SOURCE = r'''from __future__ import annotations

import importlib.util
from pathlib import Path

import ansible


def _load_builtin_normal():
    path = Path(ansible.__file__).parent / "plugins" / "action" / "normal.py"
    spec = importlib.util.spec_from_file_location("_iiab_builtin_normal", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.ActionModule


class ActionModule(_load_builtin_normal()):
    """Resolve ansible.builtin.* modules through the mock library.

    Ansible's builtin collection is synthetic, so a local ansible.builtin
    collection cannot override it. Stripping the prefix lets the normal
    action find the legacy module name, which ANSIBLE_LIBRARY points at the
    lifecycle mock.
    """

    def run(self, tmp=None, task_vars=None):
        if self._task.action.startswith("ansible.builtin."):
            self._task.action = self._task.action.rsplit(".", 1)[-1]
        return super().run(tmp=tmp, task_vars=task_vars)
'''

MOCK_PAUSE_ACTION_SOURCE = r'''from __future__ import annotations

from ansible.plugins.action import ActionBase


class ActionModule(ActionBase):
    """Return immediately instead of sleeping (roles pause for emphasis)."""

    def run(self, tmp=None, task_vars=None):
        result = super().run(tmp, task_vars)
        result.update(
            changed=False,
            delta=0,
            echo=True,
            rc=0,
            start="",
            stop="",
            stdout="Paused for 0.0 minutes",
            user_input="",
        )
        return result
'''


def user_data_defaults_file(role: str) -> Path | None:
    defaults = ROOT_DIR / "roles" / role / "defaults"
    for name in ("main.yml", "main.yaml"):
        path = defaults / name
        if path.is_file():
            return path
    return None


def declares_user_data(role: str) -> bool:
    path = user_data_defaults_file(role)
    if path is None:
        return False
    return bool(
        re.search(
            rf"^{re.escape(role_var(role))}_user_data\b",
            path.read_text(encoding="utf-8"),
            re.MULTILINE,
        )
    )


def load_vars_file(path: Path) -> dict:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError):
        return {}
    return data if isinstance(data, dict) else {}


def resolved_user_data(role: str, vars_file: str) -> dict:
    """Resolve a role's declared user data without including its defaults.

    The lifecycle playbook must not load role defaults as host facts: that
    would shadow the role's own templated defaults with raw Jinja strings. So
    resolve just the declared paths and databases here, using the same vars the
    test passes to the playbook.
    """
    defaults = user_data_defaults_file(role)
    if defaults is None or not declares_user_data(role):
        return {"paths": [], "databases": []}

    prefix = role_var(role)
    raw: dict = load_vars_file(defaults)
    base = Path(vars_file) if vars_file else ROOT_DIR / "vars" / "default_vars.yml"
    raw.update(load_vars_file(base))
    raw.update(load_vars_file(ROOT_DIR / "roles" / role / "vars" / "main.yml"))

    environment = jinja2.Environment()
    resolved: dict[str, object] = {}

    def resolve(name: str, stack: set[str]):
        if name in resolved:
            return resolved[name]
        if name not in raw or name in stack:
            return None
        result = render(raw[name], stack | {name})
        resolved[name] = result
        return result

    def render(value, stack: set[str]):
        if isinstance(value, str):
            try:
                names = jinja_meta.find_undeclared_variables(
                    environment.parse(value)
                )
            except jinja2.TemplateSyntaxError:
                return value
            if not names:
                return value
            context = {name: resolve(name, stack) for name in names}
            try:
                return environment.from_string(value).render(context)
            except jinja2.TemplateError:
                return value
        if isinstance(value, list):
            return [render(item, stack) for item in value]
        if isinstance(value, dict):
            return {key: render(item, stack) for key, item in value.items()}
        return value

    paths = render(raw.get(f"{prefix}_user_data", []), set())
    databases = render(raw.get(f"{prefix}_user_data_databases", []), set())
    if not isinstance(paths, list):
        paths = []
    if not isinstance(databases, list):
        databases = []
    return {
        "paths": [str(path) for path in paths if path],
        "databases": [str(database) for database in databases if database],
    }


def enabled_var(role: str) -> str:
    """Return the role's <prefix>_enabled variable.

    Use the same install prefix as runrole; don't guess from task prose (that
    used to pick dependency names such as mongodb_enabled for sugarizer).
    """
    prefix = role_lifecycle.install_prefix(role) or role_var(role)
    return f"{prefix}_enabled"


def role_service_names(role: str) -> set[str]:
    services = set()
    tasks_dir = ROOT_DIR / "roles" / role / "tasks"
    for path in sorted(tasks_dir.rglob("*")):
        if not path.is_file():
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        for index, line in enumerate(lines):
            module = re.match(r"^\s+(?:systemd_service|systemd|service):\s*$", line)
            if not module:
                continue
            module_indent = len(line) - len(line.lstrip())
            for following in lines[index + 1 : index + 8]:
                if following.strip() and len(following) - len(following.lstrip()) <= module_indent:
                    break
                match = re.match(
                    r'^\s+name:\s*["\']?([A-Za-z0-9@_.-]+)["\']?\s*$',
                    following,
                )
                if match:
                    services.add(match.group(1))
                    break
    return services


UNIT_SUFFIXES = (
    ".service",
    ".socket",
    ".timer",
    ".path",
    ".target",
    ".mount",
    ".automount",
    ".swap",
    ".device",
    ".slice",
    ".scope",
)


def unit_path(service: str) -> str:
    suffix = "" if service.endswith(UNIT_SUFFIXES) else ".service"
    return f"/etc/systemd/system/{service}{suffix}"


def initial_state(role: str, installed: bool = False) -> dict:
    role_services = sorted(
        role_service_names(role) | ROLE_EXTRA_SERVICES.get(role, set())
    )
    available_services = [
        "nginx",
        "dnsmasq",
        "apache2",
        "avahi-daemon",
        "hostapd",
        "hostapd.service",
        "iiab-clone-wifi.service",
        "mariadb",
        "php8.2-fpm",
        "postgresql",
        "postgresql-iiab",
        "ssh",
        "systemd-resolved",
        "networking",
        "wpa_supplicant",
    ]
    # A fresh install gets its units from the package that the mocked package
    # task installs, so treat every service the role refers to as available.
    available_services.extend(
        service for service in role_services if service not in available_services
    )
    state = {
        "paths": {},
        "services": {"nginx": {"enabled": True, "state": "started"}},
        "expected_services": role_services,
        "available_services": available_services,
        "packages": {},
    }
    # Packages such as uwsgi materialize their unit templates when a role
    # installs them; instance units are added by the role's own systemd tasks.
    if installed:
        for service in role_services:
            if service in state["services"]:
                continue
            state["paths"][unit_path(service)] = "file"
            state["services"][service] = {"enabled": True, "state": "started"}
    return state


def role_manages_service_toggle(role: str) -> bool:
    tasks_dir = ROOT_DIR / "roles" / role / "tasks"
    return any(
        path.is_file() and "enable-or-disable" in path.stem
        for path in tasks_dir.rglob("*")
    )


def role_toggle_service_names(role: str) -> set[str]:
    services = set()
    tasks_dir = ROOT_DIR / "roles" / role / "tasks"
    for path in tasks_dir.rglob("*"):
        if not path.is_file() or "enable-or-disable" not in path.stem:
            continue
        services.update(role_service_names_from_files((path,)))
    services.update(ROLE_EXTRA_SERVICES.get(role, set()))
    return services


def role_service_names_from_files(paths) -> set[str]:
    services = set()
    for path in paths:
        lines = path.read_text(encoding="utf-8").splitlines()
        for index, line in enumerate(lines):
            module = re.match(r"^\s+(?:systemd_service|systemd|service):\s*$", line)
            if not module:
                continue
            module_indent = len(line) - len(line.lstrip())
            for following in lines[index + 1 : index + 8]:
                if following.strip() and len(following) - len(following.lstrip()) <= module_indent:
                    break
                match = re.match(
                    r'^\s+name:\s*["\']?([A-Za-z0-9@_.-]+)["\']?\s*$',
                    following,
                )
                if match:
                    services.add(match.group(1))
                    break
    return services


class _LifecycleLoader(yaml.SafeLoader):
    pass


def _construct_mapping(loader, node):
    # Keep the source line so warnings can point at the exact task.
    data = yaml.SafeLoader.construct_mapping(loader, node)
    data["__line__"] = node.start_mark.line + 1
    return data


_LifecycleLoader.add_constructor(
    _LifecycleLoader.DEFAULT_MAPPING_TAG, _construct_mapping
)


def load_task_file(path: Path, text: str | None = None):
    if text is None:
        text = path.read_text(encoding="utf-8")
    return yaml.load(text, Loader=_LifecycleLoader)


def lifecycle_directives(lines: list[str], line: int | None) -> set[str]:
    """Collect ``# lifecycle: ...`` directives for a task.

    A directive may be on the task's first line or in the comment block
    directly above it. Blank lines end the block.
    """
    if line is None or not 1 <= line <= len(lines):
        return set()
    candidates = [lines[line - 1]]
    index = line - 2
    while index >= 0 and lines[index].lstrip().startswith("#"):
        candidates.append(lines[index])
        index -= 1
    return {
        match.group("rule").lower()
        for candidate in candidates
        for match in LIFECYCLE_DIRECTIVE.finditer(candidate)
    }


def task_arg(args, name: str, default=None):
    if isinstance(args, dict):
        return args.get(name, default)
    if isinstance(args, str):
        match = re.search(
            rf"(?:^|\s){re.escape(name)}=(\"[^\"]*\"|'[^']*'|\S+)", args
        )
        if match:
            return match.group(1).strip("\"'")
    return default


def is_true(value) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "on", "true", "yes"}


def task_command(task: dict, args) -> str:
    if isinstance(args, str):
        return args
    command = task_arg(args, "cmd") or task_arg(args, "_raw_params")
    task_args = task.get("args")
    if not command and isinstance(task_args, dict):
        command = task_args.get("cmd", "")
    return str(command or "")


def network_action(module: str, args, task: dict) -> tuple[str, str] | None:
    """Return (kind, description) for a task that uses the network.

    ``kind`` lets configure.yml accept fetching an immutable asset while still
    rejecting program checkouts and dependency installs.
    """
    module = module.rsplit(".", 1)[-1]

    if module in {"get_url", "get_curl"}:
        return "asset", "downloads a file"
    if module == "git":
        return "checkout", "fetches a git checkout"
    if module == "unarchive":
        src = str(task_arg(args, "src", ""))
        if is_true(task_arg(args, "remote_src")) or re.match(
            r"^(?:ftp|https?)://", src
        ):
            return "asset", "downloads and extracts an archive"
        return None
    if module == "uri":
        url = task_arg(args, "url", "a remote host")
        if task_arg(args, "dest"):
            return "asset", f"downloads {url}"
        return "asset", f"makes an HTTP request to {url}"
    if module in {"apt_key", "apt_repository"}:
        if str(task_arg(args, "state", "present")).lower() != "absent":
            return "metadata", f"fetches {module} metadata"
        return None
    if module in PACKAGE_MODULES:
        state = str(task_arg(args, "state", "present")).lower()
        if state in {"absent", "removed", "purged"}:
            return None
        name = task_arg(args, "name") or task_arg(args, "pkg")
        if module == "apt" and is_true(task_arg(args, "update_cache")) and not name:
            return "install", "refreshes the apt cache"
        if module == "apt" and task_arg(args, "upgrade"):
            return "install", "upgrades apt packages"
        if module == "package":
            return "install", "installs system packages"
        if state == "latest":
            return "install", f"installs or upgrades {module} packages"
        return "install", f"installs {module} packages"
    if module in INSTALLER_MODULES:
        state = str(task_arg(args, "state", "present")).lower()
        if state not in {"absent", "removed", "purged"}:
            return "install", f"installs {module} packages"
        return None
    if module in SHELL_MODULES:
        command = task_command(task, args)
        match = NETWORK_COMMAND.search(command)
        if match:
            word = match.group(0).strip().split()[0].lower()
            if word in {"curl", "wget"}:
                kind = "asset"
            elif word == "git":
                kind = "checkout"
            else:
                kind = "install"
            return kind, f"runs `{match.group(0).strip()}` (network)"
        return None
    return None


def included_phase(module: str, args) -> str | None:
    if module.rsplit(".", 1)[-1] not in INCLUDE_MODULES:
        return None
    value = task_arg(args, "file") or task_arg(args, "_raw_params")
    if not value and isinstance(args, str):
        value = args
    if not value:
        return None
    stem = Path(str(value)).stem
    return stem if stem in LIFECYCLE_FILES else None


def walk_tasks(items, guarded: bool = False):
    if not isinstance(items, list):
        return
    for task in items:
        if not isinstance(task, dict):
            continue
        task_guarded = guarded or "when" in task
        yield task, task_guarded
        for block_key in ("block", "rescue", "always"):
            yield from walk_tasks(task.get(block_key), task_guarded)


def task_modules(task: dict) -> list[tuple[str, object]]:
    return [
        (key, value)
        for key, value in task.items()
        if key not in TASK_KEYWORDS and not str(key).startswith("with_")
    ]


class Warning(NamedTuple):
    """A lifecycle finding that can be printed or surfaced as a CI annotation."""

    path: str
    line: int | None
    message: str
    label: str = ""

    def text(self) -> str:
        location = self.path
        if self.line is not None:
            location += f":{self.line}"
        label = f" [{self.label}]" if self.label else ""
        message = self.message
        if len(message) > 160:
            message = message[:157] + "..."
        return f"  WARN {location}{label}: {message}\n"

    def annotation(self) -> str:
        properties = f"file={self.path}"
        if self.line is not None:
            properties += f",line={self.line}"
        label = f"{self.label}: " if self.label else ""
        message = self.message.replace("\n", " ")
        return f"::warning {properties}::{label}{message}"


def warnings_enabled() -> bool:
    """True when GitHub should render each finding as a PR annotation."""
    return os.environ.get("GITHUB_ACTIONS") == "true"


def print_warnings(
    warnings: list[Warning],
    header: str | None = None,
    stream=sys.stdout,
) -> None:
    if not warnings:
        return
    if header:
        print(f"  {header}: {len(warnings)}", file=stream)
    for item in warnings:
        if warnings_enabled():
            print(item.annotation(), file=stream)
        else:
            print(item.text(), end="", file=stream)


def format_lifecycle_warning(
    path: Path, line: int | None, task: dict, message: str
) -> Warning:
    name = re.sub(r"\s+", " ", str(task.get("name", ""))).strip()
    if len(name) > 90:
        name = name[:87] + "..."
    return Warning(str(path.relative_to(ROOT_DIR)), line, message, name)


def lifecycle_warnings(role: str) -> list[Warning]:
    """Warn when a task file does work that belongs in another phase."""
    tasks_dir = ROOT_DIR / "roles" / role / "tasks"
    warnings: list[Warning] = []
    paths = sorted(
        set(tasks_dir.glob("*.yml")) | set(tasks_dir.glob("*.yaml"))
    )
    for path in paths:
        phase = path.stem
        if phase not in LIFECYCLE_FILES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
            tasks = load_task_file(path, text)
        except (OSError, UnicodeDecodeError, yaml.YAMLError) as error:
            warnings.append(
                Warning(
                    str(path.relative_to(ROOT_DIR)),
                    None,
                    f"could not read or parse task file for lifecycle checks "
                    f"({error.__class__.__name__})",
                )
            )
            continue
        lines = text.splitlines()
        for task, guarded in walk_tasks(tasks):
            line = task.get("__line__")
            if "allow-network" in lifecycle_directives(lines, line):
                # Deliberate exception, explained next to the task.
                continue
            for module, args in task_modules(task):
                network = network_action(module, args, task)
                if network and phase in OFFLINE_PHASES:
                    _, action = network
                    warnings.append(
                        format_lifecycle_warning(
                            path,
                            line,
                            task,
                            f"{module} {action}; {LIFECYCLE_HINTS[phase]}",
                        )
                    )

                included = included_phase(module, args)
                if not included or included == phase:
                    continue
                # main.yml is supposed to dispatch to these phases; every
                # other offline phase including them can pull in the network.
                if phase == "main":
                    if included in GATED_PHASES and not guarded:
                        warnings.append(
                            format_lifecycle_warning(
                                path,
                                line,
                                task,
                                f"includes {included}.yml unconditionally; "
                                f"{GATED_PHASES[included]}",
                            )
                        )
                    continue
                if included in NETWORK_PHASES or (
                    included == "configure" and phase != "configure"
                ):
                    warnings.append(
                        format_lifecycle_warning(
                            path,
                            line,
                            task,
                            f"includes {included}.yml, which may use the "
                            f"network; {LIFECYCLE_HINTS[phase]}",
                        )
                    )
    return warnings


STATE_MARKER = re.compile(
    r"(?<![A-Za-z0-9_.'\"])([A-Za-z0-9_]+_(?:installed|downloaded))"
    r"(?![A-Za-z0-9_.\[])"
)
SAFE_STATE_MARKER = re.compile(
    r"^\s*(?:\|\s*default|default\s*\()"
)
SAFE_MARKERS = {"network_packages_installed"}


def condition_texts(value) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        texts: list[str] = []
        for item in value:
            texts.extend(condition_texts(item))
        return texts
    return []


def unsafe_state_warnings(role: str) -> list[Warning]:
    """Warn when an optional state marker is tested without a guard.

    ``*_installed`` and ``*_downloaded`` are observed state.  Use
    ``lookup('installed', 'mysql')`` (or ``not lookup(...)``) rather than
    reading the marker variable directly.  Entry playbooks still load the state
    file through vars_files while roles are converted one at a time, but a bare
    reference breaks as soon as a role stops being loaded that way.
    """
    tasks_dir = ROOT_DIR / "roles" / role / "tasks"
    warnings: list[Warning] = []
    paths = list(tasks_dir.rglob("*.yml"))
    handlers_dir = ROOT_DIR / "roles" / role / "handlers"
    if handlers_dir.is_dir():
        paths.extend(handlers_dir.rglob("*.yml"))
    for path in sorted(paths):
        try:
            text = path.read_text(encoding="utf-8")
            tasks = load_task_file(path, text)
        except (OSError, UnicodeDecodeError, yaml.YAMLError):
            continue
        for task, _ in walk_tasks(tasks):
            line = task.get("__line__")
            conditions: list[str] = []
            for key in ("when", "failed_when", "changed_when", "until"):
                conditions.extend(condition_texts(task.get(key)))
            for module, args in task_modules(task):
                if module.rsplit(".", 1)[-1] == "assert" and isinstance(args, dict):
                    conditions.extend(condition_texts(args.get("that")))
            for condition in conditions:
                for match in STATE_MARKER.finditer(condition):
                    marker = match.group(1)
                    if marker in SAFE_MARKERS:
                        continue
                    if SAFE_STATE_MARKER.match(condition[match.end() :]):
                        continue
                    if condition[: match.start()].rstrip().endswith("default("):
                        continue
                    warnings.append(
                        format_lifecycle_warning(
                            path,
                            line,
                            task,
                            f"uses bare '{marker}'; use "
                            f"lookup('installed', '{marker}')",
                        )
                    )
    return warnings


def state_write_warnings(role: str) -> list[Warning]:
    """Warn when an installed marker is written before the role is finished."""
    tasks_dir = ROOT_DIR / "roles" / role / "tasks"
    warnings: list[Warning] = []
    paths = sorted(set(tasks_dir.glob("install*.yml")) | set(tasks_dir.glob("configure*.yml")))
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8")
            tasks = load_task_file(path, text)
        except (OSError, UnicodeDecodeError, yaml.YAMLError):
            continue
        for task, _ in walk_tasks(tasks):
            for module, args in task_modules(task):
                if module.rsplit(".", 1)[-1] != "iiab_state":
                    continue
                if not isinstance(args, dict):
                    continue
                keys = []
                if args.get("key"):
                    keys.append(str(args["key"]))
                for key in args.get("keys") or []:
                    keys.append(str(key))
                if not any(
                    key.endswith(("_installed", "_downloaded")) for key in keys
                ):
                    continue
                warnings.append(
                    format_lifecycle_warning(
                        path,
                        task.get("__line__"),
                        task,
                        "writes an installed marker before the role has "
                        "finished configuring; move it to state.yml or the end "
                        "of main.yml",
                    )
                )

    if role_supports(role, "uninstall"):
        path = tasks_dir / "uninstall.yml"
        if path.is_file():
            try:
                text = path.read_text(encoding="utf-8")
                tasks = load_task_file(path, text)
            except (OSError, UnicodeDecodeError, yaml.YAMLError):
                tasks = []
            if tasks:
                last = tasks[-1]
                removal = False
                for module, args in task_modules(last):
                    if module.rsplit(".", 1)[-1] != "iiab_state":
                        continue
                    if isinstance(args, dict) and args.get("state") == "absent":
                        removal = True
                if not removal:
                    warnings.append(
                        format_lifecycle_warning(
                            path,
                            last.get("__line__"),
                            last,
                            "uninstall.yml should remove its state markers as "
                            "its final task, after cleanup succeeds",
                        )
                    )
    return warnings


def clean_install_references() -> list[Warning]:
    """Find the removed clean_install variable in any Ansible file.

    --clean-install is implemented by ./runrole as --uninstall followed by a
    normal apply. No role may branch on the removed variable, so this is a
    hard failure rather than a warning. The CLI flag itself (with a hyphen) is
    fine in prose; only the Ansible variable matters.
    """
    findings: list[Warning] = []
    paths = set(ROOT_DIR.glob("*.yml")) | set(ROOT_DIR.glob("*.yaml"))
    for directory in ("roles", "vars", "modules/tests"):
        base = ROOT_DIR / directory
        if base.is_dir():
            paths.update(base.rglob("*.yml"))
            paths.update(base.rglob("*.yaml"))
    for path in sorted(paths):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        for number, line in enumerate(lines, 1):
            if re.search(r"\bclean_install\b", line):
                findings.append(
                    Warning(
                        str(path.relative_to(ROOT_DIR)),
                        number,
                        "'clean_install' is no longer a runtime flag; "
                        "--clean-install is --uninstall followed by a normal "
                        "apply. Remove this variable.",
                    )
                )
    return findings


def prepare_controller_files(scenario: Path) -> None:
    template_roles = scenario / "templates" / "roles"
    template_roles.parent.mkdir(parents=True, exist_ok=True)
    template_roles.symlink_to(ROOT_DIR / "roles", target_is_directory=True)
    (scenario / "roles").symlink_to(ROOT_DIR / "roles", target_is_directory=True)


def playbook_header(
    role: str,
    vars_file: str,
    install_name: str,
    enabled_name: str,
    enabled: bool,
    installed: bool,
    scenario: Path,
    phase: str | None = None,
    lifecycle: dict | None = None,
) -> str:
    lifecycle = lifecycle or {}
    vars_path = vars_file or str(ROOT_DIR / "vars" / "default_vars.yml")
    lines = [
        "- hosts: localhost",
        "  connection: local",
        "  gather_facts: false",
        "  vars_files:",
        f'    - "{vars_path}"',
        "  module_defaults:",
        "    iiab_state:",
        '      path: "{{ iiab_state_file }}"',
        "  vars:",
        f'    ansible_python_interpreter: "{sys.executable}"',
        "    ansible_facts:",
        "      machine: x86_64",
        "      distribution: Debian",
        '      distribution_major_version: "13"',
        '      distribution_version: "13.0"',
        "      pkg_mgr: apt",
        "      default_ipv4:",
        "        alias: eth0",
        "        gateway: 192.0.2.1",
        "      ansible_local:",
        "        local_facts:",
        '          systemd_networkd: "disabled"',
        '          network_manager: "disabled"',
        '          dhcpcd: "disabled"',
        "    is_proot: false",
        "    iiab_stage: 8",
        "    no_net_restart: false",
        '    iiab_wireless_lan_iface: "wlan0"',
        '    iiab_lan_iface: "eth0"',
        '    iiab_wan_iface: "eth0"',
        '    rpi_model: "none"',
        '    os_ver: "debian-13"',
        "    is_debian: true",
        "    is_raspbian: false",
        "    is_ubuntu: false",
        "    is_linuxmint: false",
        '    dpkg_arch: {"stdout": "amd64"}',
        '    php_version: "8.2"',
        '    python_version: "3.14"',
        "    skip_role_on_error: false",
        f'    uninstall: {str(lifecycle.get("uninstall", False)).lower()}',
        f'    reinstall: {str(lifecycle.get("reinstall", False)).lower()}',
        f"    {install_name}: true",
        f"    {enabled_name}: {str(enabled).lower()}",
        f'    iiab_mock_state: "{scenario}/state.json"',
        f'    iiab_mock_installed: "{str(installed).lower()}"',
    ]
    if phase:
        lines.append(f'    iiab_mock_phase: "{phase}"')
    lines.extend(
        [
            "  environment:",
            f'    IIAB_MOCK_STATE: "{scenario}/state.json"',
            f'    IIAB_MOCK_INSTALLED: "{str(installed).lower()}"',
        ]
    )
    if phase:
        lines.append(f'    IIAB_MOCK_PHASE: "{phase}"')
    lines.append("  tasks:")
    return "\n".join(lines) + "\n"


def make_playbook(
    role: str,
    vars_file: str,
    install_name: str,
    enabled_name: str,
    scenario: Path,
    *,
    enabled: bool,
    installed: bool,
    lifecycle: dict | None = None,
    phase: str | None = None,
    checkpoint: str | None = None,
    seed_installed: bool = False,
) -> str:
    content = playbook_header(
        role,
        vars_file,
        install_name,
        enabled_name,
        enabled,
        installed,
        scenario,
        phase,
        lifecycle,
    )
    if phase:
        lifecycle = lifecycle or {}
        content += textwrap.indent(
            textwrap.dedent(
                f"""\
                    - set_fact:
                        {install_name}: true
                        {enabled_name}: {str(enabled).lower()}
                        uninstall: {str(lifecycle.get("uninstall", False)).lower()}
                        reinstall: {str(lifecycle.get("reinstall", False)).lower()}
                """
            ),
            "    ",
        )
    if seed_installed:
        content += textwrap.indent(
            textwrap.dedent(
                f"""\
                    - set_fact:
                        {role_var(role)}_installed: true
                """
            ),
            "    ",
        )
    user_data = resolved_user_data(role, vars_file)
    if user_data["paths"] or user_data["databases"]:
        content += textwrap.indent(
            textwrap.dedent(
                f"""\
                    - name: Seed declared user data for the lifecycle test
                      mock_user_data:
                        paths: {json.dumps(user_data["paths"])}
                        databases: {json.dumps(user_data["databases"])}
                """
            ),
            "    ",
        )
    content += textwrap.indent(
        textwrap.dedent(
            """\
                # Roles notify the shared NGINX handlers in 0-init.  Load them
                # without running 0-init's tasks, so each role can still be
                # tested on its own.
                - name: Load the shared handlers from 0-init
                  include_role:
                    name: 0-init
                    tasks_from: noop
            """
        ),
        "    ",
    )
    content += textwrap.indent(
        textwrap.dedent(
            f"""\
                - include_role:
                    name: {role}
            """
        ),
        "    ",
    )
    if checkpoint:
        content += textwrap.indent(
            textwrap.dedent(
                f"""\
                    - name: Record {checkpoint} virtual state
                      mock_checkpoint:
                        snapshot: {checkpoint}
                """
            ),
            "    ",
        )
    return content


def create_mock_library(directory: Path) -> Path:
    library = directory / "library"
    library.mkdir()
    (library / "iiab_state").symlink_to(ROOT_DIR / "modules" / "iiab_state.py")
    module = directory / "mock-module.py"
    module.write_text(MOCK_MODULE_SOURCE, encoding="utf-8")
    module.chmod(0o755)
    actions = directory / "actions"
    actions.mkdir()
    for name in ("copy", "template", "unarchive"):
        action = actions / f"{name}.py"
        action.write_text(MOCK_ACTION_SOURCE, encoding="utf-8")
    (actions / "pause.py").write_text(MOCK_PAUSE_ACTION_SOURCE, encoding="utf-8")
    (actions / "normal.py").write_text(MOCK_NORMAL_ACTION_SOURCE, encoding="utf-8")
    (actions / "include_vars.py").write_text(
        MOCK_INCLUDE_VARS_ACTION_SOURCE, encoding="utf-8"
    )
    # The remaining mocked modules become action plugins, so their Python code
    # runs inside ansible-playbook instead of a fresh interpreter per task.
    module_action = actions / "_mock_module_action.py"
    module_action.write_text(MOCK_MODULE_ACTION_SOURCE, encoding="utf-8")
    names = {
        "stat",
        "file",
        "template",
        "copy",
        "get_curl",
        "lineinfile",
        "blockinfile",
        "replace",
        "ini_file",
        "disk_usage",
        "group",
        "user",
        "git",
        "apt",
        "package",
        "dnf",
        "yum",
        "unarchive",
        "get_url",
        "uri",
        "cron",
        "pip",
        "mount",
        "sysctl",
        "command",
        "shell",
        "systemd",
        "systemd_service",
        "service",
        "raw",
        "script",
        "setup",
        "mock_checkpoint",
        "mock_user_data",
    }
    for name in names:
        (library / name).symlink_to(module)
        if name not in {"copy", "template", "unarchive"}:
            (actions / f"{name}.py").symlink_to(module_action)
    collection_modules = {
        ("ansible", "mariadb"): {"mariadb_db", "mariadb_user"},
        ("ansible", "posix"): {"patch"},
        ("community", "general"): {"apache2_module", "htpasswd", "npm", "timezone"},
        ("community", "mysql"): {"mysql_db", "mysql_user"},
        ("community", "postgresql"): {"postgresql_db", "postgresql_user"},
    }
    for (namespace, collection), module_names in collection_modules.items():
        for name in module_names:
            (actions / f"{name}.py").symlink_to(module_action)
        module_dir = (
            directory
            / "collections"
            / "ansible_collections"
            / namespace
            / collection
            / "plugins"
            / "modules"
        )
        module_dir.mkdir(parents=True)
        for name in module_names:
            (module_dir / name).symlink_to(module)
    return library


def run_ansible(
    playbook: Path,
    library: Path,
    state_file: Path,
    installed: bool | None = None,
    phase: str | None = None,
    extra_vars: dict | None = None,
) -> subprocess.CompletedProcess[str]:
    # Some roles run command tasks with become_user (postgres, www-data). The
    # mock module writes IIAB_MOCK_STATE, so let those users traverse to and
    # update the scenario state file.
    state_file.parent.parent.chmod(0o777)
    state_file.parent.chmod(0o777)
    if state_file.exists():
        state_file.chmod(0o666)
    environment = os.environ.copy()
    environment.update(
        {
            "ANSIBLE_CONFIG": str(ROOT_DIR / "ansible.cfg"),
            "ANSIBLE_ROLES_PATH": str(ROOT_DIR / "roles"),
            "ANSIBLE_LIBRARY": str(library),
            "ANSIBLE_COLLECTIONS_PATH": str(library.parent / "collections"),
            "ANSIBLE_ACTION_PLUGINS": str(library.parent / "actions"),
            "ANSIBLE_LOOKUP_PLUGINS": str(ROOT_DIR / "lookup_plugins"),
            "ANSIBLE_NOCOLOR": "1",
            "IIAB_MOCK_STATE": str(state_file),
            "IIAB_LIFECYCLE_ROOT": str(ROOT_DIR),
        }
    )
    if installed is not None:
        environment["IIAB_MOCK_INSTALLED"] = str(installed).lower()
    if phase:
        environment["IIAB_MOCK_PHASE"] = phase
    command = [
        shutil.which("ansible-playbook") or "ansible-playbook",
        "--forks=1",
        "-i",
        "localhost,",
        str(playbook),
    ]
    # default_vars.yml sets skip_role_on_error: True, and vars_files beat the
    # play-level value in make_playbook(). Force it as an extra var so a real
    # role failure makes the lifecycle test fail instead of silently passing.
    scenario_vars = {
        "skip_role_on_error": False,
        "iiab_state_file": str(state_file.parent / "iiab_state.yml"),
    }
    if extra_vars:
        scenario_vars.update(extra_vars)
    command.extend(["--extra-vars", json.dumps(scenario_vars)])

    return subprocess.run(
        command,
        cwd=ROOT_DIR,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )


def state_has_path(state: dict, path: str) -> bool:
    paths = state.get("paths", {})
    if path in paths:
        return True
    prefix = path.rstrip("/") + "/"
    return any(item.startswith(prefix) for item in paths)


def user_data_problem(state: dict, operation: str) -> str | None:
    """Report declared user data that an operation removed or left behind."""
    declared = state.get("user_data") or {}
    paths = [str(path) for path in declared.get("paths", [])]
    databases = [str(name) for name in declared.get("databases", [])]
    databases_state = state.get("databases", {})

    missing = [path for path in paths if not state_has_path(state, path)]
    missing.extend(
        name for name in databases if databases_state.get(name) != "present"
    )
    if missing:
        return f"{operation} removed declared user data: " + ", ".join(missing)
    return None


def operation_result(
    name: str,
    role: str,
    vars_file: str,
    library: Path,
    temp_dir: Path,
    enabled_name: str,
    install_name: str,
    values: dict,
) -> str:
    scenario = temp_dir / name
    scenario.mkdir()
    prepare_controller_files(scenario)
    state_yaml = scenario / "iiab_state.yml"
    if name == "reinstall":
        # ./runrole leaves the role's markers in place during --reinstall, so
        # start the scenario the same way and prove the role does not remove
        # them while rebuilding.
        state_yaml.write_text(f"{role_var(role)}_installed: True\n", encoding="utf-8")
    else:
        state_yaml.touch()
    state_file = scenario / "state.json"
    state_file.write_text(
        json.dumps(initial_state(role, values["installed"])), encoding="utf-8"
    )
    playbook = scenario / "playbook.yml"
    playbook.write_text(
        make_playbook(
            role,
            vars_file,
            install_name,
            enabled_name,
            scenario,
            enabled=values["enabled"],
            installed=values["installed"],
            lifecycle=values,
        ),
        encoding="utf-8",
    )
    extra_vars = {
        install_name: True,
        enabled_name: values["enabled"],
        **{key: values[key] for key in ("uninstall", "reinstall")},
    }
    result = run_ansible(
        playbook,
        library,
        state_file,
        installed=values["installed"],
        phase=name,
        extra_vars=extra_vars,
    )
    output = [f"  {name:<19}"]
    if result.returncode:
        output.append("FAIL\n")
        output.append("".join(result.stdout.splitlines(True)[-40:]))
        output.append("".join(result.stderr.splitlines(True)[-40:]))
        return "".join(output)
    state = json.loads(state_file.read_text(encoding="utf-8"))
    problem = user_data_problem(state, name)
    if problem:
        output.append(f"FAIL\n{problem}\n")
        output.append(state_file.read_text(encoding="utf-8"))
        return "".join(output)

    if name == "uninstall":
        prefix = role_var(role)
        if re.search(
            rf"^{re.escape(prefix)}_(?:installed|downloaded): True$",
            state_yaml.read_text(encoding="utf-8"),
            re.MULTILINE,
        ):
            output.append("FAIL\nuninstall did not remove the role's markers\n")
            output.append(state_yaml.read_text(encoding="utf-8"))
            return "".join(output)

    if name == "reinstall":
        prefix = role_var(role)
        if not re.search(
            rf"^{re.escape(prefix)}_(?:installed|downloaded): True$",
            state_yaml.read_text(encoding="utf-8"),
            re.MULTILINE,
        ):
            output.append("FAIL\nreinstall did not keep the role's installed marker\n")
            output.append(state_yaml.read_text(encoding="utf-8"))
            return "".join(output)

    output.append("PASS\n")
    return "".join(output)


def clean_install_result(
    role: str,
    vars_file: str,
    library: Path,
    temp_dir: Path,
    enabled_name: str,
    install_name: str,
) -> str:
    """Run --uninstall and then a normal apply, sharing one virtual host.

    --clean-install is not a flag the role sees: ./runrole runs the uninstall
    phase and then the ordinary apply. Mirror that here so the scenario proves
    the second run really reinstalls from the post-uninstall state.
    """
    scenario = temp_dir / "clean-install"
    scenario.mkdir()
    prepare_controller_files(scenario)
    state_yaml = scenario / "iiab_state.yml"
    state_yaml.touch()
    state_file = scenario / "state.json"
    state_file.write_text(json.dumps(initial_state(role, True)), encoding="utf-8")

    output = [f"  {'clean-install':<19}"]
    phases = (
        ("clean-install-uninstall", True, True),
        ("clean-install-install", False, False),
    )
    for phase, installed, uninstall in phases:
        playbook = scenario / f"{phase}.yml"
        playbook.write_text(
            make_playbook(
                role,
                vars_file,
                install_name,
                enabled_name,
                scenario,
                enabled=True,
                installed=installed,
                lifecycle={"uninstall": uninstall, "reinstall": False},
            ),
            encoding="utf-8",
        )
        result = run_ansible(
            playbook,
            library,
            state_file,
            installed=installed,
            phase=phase,
            extra_vars={
                install_name: True,
                enabled_name: True,
                "uninstall": uninstall,
                "reinstall": False,
            },
        )
        if result.returncode:
            output.append("FAIL\n")
            output.append("".join(result.stdout.splitlines(True)[-40:]))
            output.append("".join(result.stderr.splitlines(True)[-40:]))
            return "".join(output)
        if uninstall:
            prefix = role_var(role)
            if re.search(
                rf"^{re.escape(prefix)}_(?:installed|downloaded): True$",
                state_yaml.read_text(encoding="utf-8"),
                re.MULTILINE,
            ):
                output.append("FAIL\nclean-install uninstall left the role's markers behind\n")
                output.append(state_yaml.read_text(encoding="utf-8"))
                return "".join(output)

    state = json.loads(state_file.read_text(encoding="utf-8"))
    problem = user_data_problem(state, "clean-install")
    if problem:
        output.append(f"FAIL\n{problem}\n")
        output.append(state_file.read_text(encoding="utf-8"))
        return "".join(output)

    prefix = role_var(role)
    if not re.search(
        rf"^{re.escape(prefix)}_(?:installed|downloaded): True$",
        state_yaml.read_text(encoding="utf-8"),
        re.MULTILINE,
    ):
        output.append("FAIL\nclean-install did not record an installed marker\n")
        output.append(state_yaml.read_text(encoding="utf-8"))
        return "".join(output)

    output.append("PASS\n")
    return "".join(output)


def toggle_result(
    role: str,
    vars_file: str,
    library: Path,
    temp_dir: Path,
    enabled_name: str,
    install_name: str,
    uninstall_supported: bool,
    toggle_supported: bool,
    toggle_services: set[str],
) -> str:
    scenario = temp_dir / "toggle"
    if not toggle_supported:
        return f"  {'toggle':<19}SKIP (role has no service toggle tasks)\n"
    scenario.mkdir()
    prepare_controller_files(scenario)
    (scenario / "iiab_state.yml").touch()
    state_file = scenario / "state.json"
    state_file.write_text(json.dumps(initial_state(role)), encoding="utf-8")
    playbook = scenario / "playbook.yml"
    plays = []
    phases = [
        ("enabled", True, False),
        ("disabled", False, True),
        ("enabled-again", True, True),
    ]
    if uninstall_supported:
        phases.append(("uninstall", True, True))
    for phase, enabled, installed in phases:
        plays.append(
            make_playbook(
                role,
                vars_file,
                install_name,
                enabled_name,
                scenario,
                enabled=enabled,
                installed=installed,
                lifecycle={"uninstall": phase == "uninstall"},
                phase=phase,
                checkpoint=phase,
                seed_installed=installed,
            )
        )
    playbook.write_text("---\n" + "".join(plays), encoding="utf-8")
    result = run_ansible(playbook, library, state_file)
    output = [f"  {'toggle':<19}"]
    if result.returncode:
        output.append("FAIL\n")
        output.append("".join(result.stdout.splitlines(True)[-40:]))
        output.append("".join(result.stderr.splitlines(True)[-40:]))
        return "".join(output)

    state = json.loads(state_file.read_text(encoding="utf-8"))
    snapshots = state.get("snapshots", {})
    required = {"enabled", "disabled", "enabled-again"}
    if uninstall_supported:
        required.add("uninstall")
    if not required <= snapshots.keys():
        output.append("FAIL\nvirtual state did not record all toggle phases\n")
        output.append(f"recorded snapshots: {sorted(snapshots)}\n")
        return "".join(output)

    events = state.get("events", [])
    active = {
        event["name"]
        for event in events
        if event["phase"] == "enabled" and event["state"] in ACTIVE_STATES
    }
    stopped = {
        event["name"]
        for event in events
        if event["phase"] == "disabled" and event["state"] == "stopped"
    }
    active_again = {
        event["name"]
        for event in events
        if event["phase"] == "enabled-again" and event["state"] in ACTIVE_STATES
    }
    managed = active & toggle_services - BASELINE_SERVICES
    if not managed:
        # A role can toggle a config file instead of owning a daemon (e.g.,
        # AWStats' NGINX shortcut). Both phases are already installed, so any
        # path difference between them comes from the enabled state.
        disabled_paths = set(snapshots["disabled"].get("paths", {}))
        enabled_paths = set(snapshots["enabled-again"].get("paths", {}))
        added = enabled_paths - disabled_paths
        removed = disabled_paths - enabled_paths
        if added or removed:
            output.append(
                f"PASS (config-only toggle: {len(added)} added, "
                f"{len(removed)} removed)\n"
            )
            return "".join(output)
        output.append("SKIP (role created no systemd service or config change)\n")
        return "".join(output)
    if missing := managed - stopped:
        output.append(f"FAIL\nservices not stopped when disabled: {sorted(missing)}\n")
        return "".join(output)
    if missing := managed - active_again:
        output.append(f"FAIL\nservices not started when re-enabled: {sorted(missing)}\n")
        return "".join(output)

    for name in managed:
        enabled_service = snapshots["enabled"]["services"][name]
        disabled_service = snapshots["disabled"]["services"][name]
        enabled_again_service = snapshots["enabled-again"]["services"][name]
        if enabled_service["state"] not in ACTIVE_STATES:
            output.append(f"FAIL\n{name} was not active after enabling\n")
            return "".join(output)
        if disabled_service["state"] != "stopped":
            output.append(f"FAIL\n{name} was not stopped after disabling\n")
            return "".join(output)
        if enabled_again_service["state"] not in ACTIVE_STATES:
            output.append(f"FAIL\n{name} was not active after re-enabling\n")
            return "".join(output)
        if uninstall_supported:
            uninstall_service = snapshots["uninstall"]["services"].get(name)
            if not uninstall_service or uninstall_service["state"] != "stopped":
                output.append(f"FAIL\n{name} was not stopped during uninstall\n")
                return "".join(output)
    output.append("PASS\n")
    return "".join(output)


def default_jobs() -> int:
    """Return a conservative number of roles to test in parallel.

    GitHub's ubuntu-slim runner has one vCPU, but os.cpu_count() can report the
    host's cores.  The cgroup CPU quota is the reliable value; cap the fallback
    so a single-vCPU runner never starts dozens of ansible-playbook processes.
    """
    try:
        quota, period = Path("/sys/fs/cgroup/cpu.max").read_text().split()
        if quota != "max":
            return max(1, -(-int(quota) // int(period)))
    except (OSError, ValueError):
        pass
    return max(1, min(4, os.cpu_count() or 1))


def run_role(role: str, vars_file: str, quiet: bool = False, strict: bool = False) -> int:
    role_dir = ROOT_DIR / "roles" / role
    if not re.fullmatch(r"[A-Za-z0-9_-]+", role):
        print(f"ERROR: invalid role name: {role}", file=sys.stderr)
        return 1
    if not any((role_dir / "tasks" / name).is_file() for name in ("main.yml", "main.yaml")):
        print(f"ERROR: role not found or has no tasks/main.yml: {role}", file=sys.stderr)
        return 1
    if vars_file and not Path(vars_file).is_file():
        print(f"ERROR: vars file not found: {vars_file}", file=sys.stderr)
        return 1

    enabled_name = enabled_var(role)
    install_name = f"{role_lifecycle.install_prefix(role) or role_var(role)}_install"
    operations: list[tuple[str, dict]] = [
        ("apply", {"installed": False, "enabled": True}),
        ("disabled-apply", {"installed": False, "enabled": False}),
        ("toggle", {}),
    ]
    skipped: list[str] = []
    if role_supports(role, "reinstall"):
        operations.append(("reinstall", {"installed": True, "enabled": True, "reinstall": True}))
    else:
        skipped.append("reinstall")
    uninstall_supported = role_supports(role, "uninstall")
    toggle_supported = role_manages_service_toggle(role)
    toggle_services = role_toggle_service_names(role)
    # An already-installed role that is disabled is covered by the 'disabled'
    # phase of the toggle scenario below, so it is not run separately.
    if uninstall_supported:
        operations.extend(
            [
                ("clean-install", {"installed": True, "enabled": True}),
                ("uninstall", {"installed": True, "enabled": False, "uninstall": True}),
            ]
        )
    else:
        skipped.extend(["clean-install", "uninstall"])

    if not quiet:
        print(f"Testing {role} lifecycle with mocked filesystem, services, and processes...")
    warnings = lifecycle_warnings(role)
    print_warnings(warnings)
    unsafe_state = unsafe_state_warnings(role)
    print_warnings(unsafe_state, "unsafe state checks")
    state_writes = state_write_warnings(role)
    print_warnings(state_writes, "state writes in the wrong phase")
    if not quiet:
        for name in skipped:
            print(f"  {name:<19} SKIP (unsupported)")

    with tempfile.TemporaryDirectory(prefix="iiab-role-lifecycle.") as directory:
        temp_dir = Path(directory)
        library = create_mock_library(temp_dir)
        futures = {}
        # Keep one ansible-playbook per role at a time. --all parallelizes
        # across roles; nesting another pool here used to launch dozens of
        # ansible processes on a single-vCPU CI runner.
        with ThreadPoolExecutor(max_workers=1) as executor:
            for name, values in operations:
                if name == "toggle":
                    future = executor.submit(
                        toggle_result,
                        role,
                        vars_file,
                        library,
                        temp_dir,
                        enabled_name,
                        install_name,
                        uninstall_supported,
                        toggle_supported,
                        toggle_services,
                    )
                elif name == "clean-install":
                    future = executor.submit(
                        clean_install_result,
                        role,
                        vars_file,
                        library,
                        temp_dir,
                        enabled_name,
                        install_name,
                    )
                else:
                    for lifecycle_flag in ("uninstall", "reinstall"):
                        values.setdefault(lifecycle_flag, False)
                    future = executor.submit(
                        operation_result,
                        name,
                        role,
                        vars_file,
                        library,
                        temp_dir,
                        enabled_name,
                        install_name,
                        values,
                    )
                futures[name] = future
            failures = 0
            for name, _ in operations:
                output = futures[name].result()
                if not quiet or "FAIL" in output:
                    print(output, end="")
                if " FAIL\n" in output or output.endswith("FAIL\n"):
                    failures = 1
    if strict and (warnings or unsafe_state or state_writes):
        failures = 1
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("role", nargs="?")
    parser.add_argument("vars_file", nargs="?")
    parser.add_argument(
        "--all",
        action="store_true",
        dest="all_roles",
        help="test every active role and print lifecycle warnings and failures",
    )
    parser.add_argument("--quiet", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="treat lifecycle warnings as failures",
    )
    parser.add_argument(
        "--jobs",
        type=int,
        default=None,
        metavar="N",
        help="with --all, number of roles to test in parallel (default: CPU quota)",
    )
    args = parser.parse_args()

    if shutil.which("ansible-playbook") is None:
        parser.error("ansible-playbook is required")
    if args.jobs is not None and args.jobs < 1:
        parser.error("--jobs must be at least 1")
    if args.jobs is not None and not args.all_roles:
        parser.error("--jobs requires --all")

    # --clean-install is uninstall followed by install; no Ansible file may
    # still branch on the removed variable. This is a hard failure.
    offenders = clean_install_references()
    if offenders:
        print_warnings(offenders, "clean_install is no longer a runtime flag")
        return 1

    if args.all_roles:
        if args.role or args.vars_file:
            parser.error("--all does not accept a role or vars file")
        all_roles = available_roles()
        roles = all_roles
        if not roles:
            return 0
        failures = 0
        workers = min(args.jobs or default_jobs(), len(roles))
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                role: executor.submit(
                    subprocess.run,
                    [
                        sys.executable,
                        str(Path(__file__).resolve()),
                        role,
                        "--quiet",
                        *(["--strict"] if args.strict else []),
                    ],
                    cwd=ROOT_DIR,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                for role in roles
            }
            for role in roles:
                result = futures[role].result()
                if result.returncode:
                    failures = 1
                    print(f"ERROR: {role}", file=sys.stderr)
                    if result.stdout:
                        print(result.stdout, end="", file=sys.stderr)
                    if result.stderr:
                        print(result.stderr, end="", file=sys.stderr)
                elif result.stdout:
                    # Quiet mode only prints lifecycle warnings for a passing role.
                    print(result.stdout, end="")
        return failures
    if not args.role:
        parser.error("a role is required unless --all is used")
    return run_role(args.role, args.vars_file or "", args.quiet, args.strict)


if __name__ == "__main__":
    sys.exit(main())
