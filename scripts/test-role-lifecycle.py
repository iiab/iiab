#!/usr/bin/env python3
"""Run role lifecycle scenarios against a virtual Ansible environment.

Besides the scenarios, task files are scanned for lifecycle warnings: network
work in a phase that must stay offline, offline phases that include a phase
which may use the network, an unguarded uninstall include, unsafe state
checks, and state writes in the wrong phase. Warnings are reported but do not
fail the run unless --strict is used; a reference to the removed
clean_install variable and an ownership path declared in more than one class
always fail. Declared user settings are seeded and must survive a normal
apply; declared user data must survive every operation.
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
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import NamedTuple

import jinja2
import yaml
from jinja2 import meta as jinja_meta

ROOT_DIR = Path(__file__).resolve().parents[1]

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
import json
import os
import posixpath
import re
import shlex
import sys

FILE_MODULES = {
    "file",
    "template",
    "copy",
    "get_curl",
    "lineinfile",
    "blockinfile",
    "replace",
    "ini_file",
}
PACKAGE_MODULES = {"apt", "apk", "dnf", "package", "pacman", "yum", "zypper"}

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
UNIT_DIRS = (
    "/etc/systemd/system",
    "/lib/systemd/system",
    "/usr/lib/systemd/system",
)

# Services that exist on the mocked base host or are supplied by an earlier
# IIAB stage.  Each role is tested on its own, so these do not have to be
# installed by the role under test.
BASE_SERVICES = {
    "NetworkManager",
    "apache2",
    "avahi-daemon",
    "dhcpcd",
    "dnsmasq",
    "hostapd",
    "iiab-clone-wifi",
    "mariadb",
    "networking",
    "networkd-dispatcher",
    "nginx",
    "php8.2-fpm",
    "postgresql",
    "postgresql-iiab",
    "ssh",
    "sshd",
    "systemd-networkd",
    "systemd-networkd-wait-online",
    "systemd-resolved",
    "systemd-udevd",
    "uwsgi-app",
    "wpa_supplicant",
}

# Packages whose units are not named after the package.
PACKAGE_UNIT_ALIASES = {
    "openssh-server": {"ssh", "sshd"},
    "samba": {"smbd", "nmbd"},
}


def module_name():
    name = os.path.basename(sys.argv[0])
    return name[len("AnsiballZ_") :] if name.startswith("AnsiballZ_") else name


def decode(value):
    try:
        return ast.literal_eval(value)
    except (SyntaxError, ValueError):
        return value


def is_false(value):
    if isinstance(value, bool):
        return not value
    return str(value).strip().lower() in {"0", "false", "no", "off", ""}


def module_args():
    if len(sys.argv) <= 1 or not os.path.isfile(sys.argv[1]):
        return {}
    with open(sys.argv[1], encoding="utf-8") as args_file:
        text = args_file.read()
    if text.startswith("{"):
        return json.loads(text).get("ANSIBLE_MODULE_ARGS", {})
    # Ansible sometimes writes shell-like key=value text, where values may be
    # quoted and contain spaces.  Shlex keeps those values intact.
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


def load_state():
    path = os.environ["IIAB_MOCK_STATE"]
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as stream:
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


def create(state, path, kind="file", content=None):
    changed = not exists(state, path)
    state["paths"][path] = kind
    if kind == "file" and content is not None:
        state.setdefault("contents", {})[path] = content
    return changed


def unit_name(service):
    service = str(service)
    return service if service.endswith(UNIT_SUFFIXES) else service + ".service"


def unit_base(unit):
    unit = unit_name(unit)
    for suffix in UNIT_SUFFIXES:
        if unit.endswith(suffix):
            unit = unit[: -len(suffix)]
            break
    return unit.split("@", 1)[0]


def package_provides_unit(package, unit):
    package = str(package).split(":", 1)[0].lower().replace("_", "-")
    base = unit_base(unit).lower()
    if not package or not base:
        return False
    if base in PACKAGE_UNIT_ALIASES.get(package, ()):
        return True
    return (
        base == package
        or base.startswith(package + "-")
        or package.startswith(base + "-")
    )


def unit_available(state, service):
    service = str(service)
    if service in BASE_SERVICES or unit_base(service) in BASE_SERVICES:
        return True
    unit = unit_name(service)
    if any(exists(state, posixpath.join(directory, unit)) for directory in UNIT_DIRS):
        return True
    return any(
        package_provides_unit(package, unit)
        for package in state.get("packages", {})
    )


def stat_exists(state, path):
    if exists(state, path) or os.environ.get("IIAB_MOCK_INSTALLED") == "true":
        return True
    unit = posixpath.basename(path)
    if not any(path == posixpath.join(directory, unit) for directory in UNIT_DIRS):
        return False
    if unit_base(unit) in BASE_SERVICES:
        return True
    return any(
        package_provides_unit(package, unit)
        for package in state.get("packages", {})
    )


def install_packages(state, args):
    names = args.get("name") or args.get("pkg") or args.get("package") or []
    if isinstance(names, str):
        names = [names]
    removing = str(args.get("state") or "present").lower() in {
        "absent",
        "removed",
        "purged",
    }
    changed = False
    packages = state.setdefault("packages", {})
    for package in names:
        package = str(package).split("=", 1)[0]
        if removing:
            changed = packages.pop(package, None) is not None or changed
            continue
        if packages.get(package) != "present":
            packages[package] = "present"
            changed = True
    return changed


def remove(state, path):
    prefix = path.rstrip("/") + "/"
    paths = [
        item for item in state["paths"] if item == path or item.startswith(prefix)
    ]
    for item in paths:
        del state["paths"][item]
        state.setdefault("contents", {}).pop(item, None)
    return bool(paths)


def record_service(state, name, enabled=None, service_state=None):
    service = state["services"].setdefault(
        name, {"enabled": False, "state": "stopped"}
    )
    if enabled is not None:
        service["enabled"] = enabled
    if service_state:
        service["state"] = service_state


def destination(state, path, url):
    """Return the file a download lands on, creating the directory if needed."""
    name = posixpath.basename(url.split("?")[0])
    is_dir = path.endswith("/") or state["paths"].get(path) == "directory"
    if not is_dir and name and not posixpath.splitext(path.rstrip("/"))[1]:
        is_dir = True
    if not is_dir:
        return path
    directory = path.rstrip("/")
    if directory:
        create(state, directory, "directory")
    return posixpath.join(path, name)


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
            if flag in words and words.index(flag) + 1 < len(words):
                create(state, words[words.index(flag) + 1])

    # Source builds normally install their unit from the source directory.
    if words and words[0] == "make" and {"install", "config"} & set(words[1:]):
        program = posixpath.basename(str(args.get("chdir", "")).rstrip("/"))
        if program:
            create(state, posixpath.join("/etc/systemd/system", f"{program}.service"))

    if "systemctl" in command or re.search(r"(^|\s)service\s", command):
        actions = {
            "start": "started",
            "restart": "restarted",
            "reload": "reloaded",
            "stop": "stopped",
        }
        for index, word in enumerate(words):
            if word in actions and index + 1 < len(words):
                record_service(state, words[index + 1], service_state=actions[word])
            elif word == "enable" and index + 1 < len(words):
                record_service(state, words[index + 1], enabled=True)
            elif word == "disable" and index + 1 < len(words):
                record_service(state, words[index + 1], enabled=False)
        finish(state, changed=False, rc=0, stdout="", stderr="")

    outputs = (
        ("dpkg-query", "installed"),
        ("rev-parse", "mock-commit"),
        ("describe --tags", "v0.1.5"),
        ("remote get-url", "https://example.invalid/iiab-test-repo.git"),
        ("--version", "Python 3.14.0"),
        ("df ", "1000"),
        ("ls /sys/class/net |", "1"),
        ("is-active", "active"),
        ("pip install", "Successfully installed iiab-test-package"),
    )
    stdout = next((value for token, value in outputs if token in command), "")
    finish(state, changed=False, rc=0, stdout=stdout, stderr="")


def main():
    name = module_name()
    args = module_args()
    state = load_state()

    if name == "stat":
        path = args.get("path", "")
        finish(
            state,
            changed=False,
            stat={
                "exists": stat_exists(state, path),
                "isdir": state["paths"].get(path) == "directory",
                "size": 0,
                "islnk": False,
            },
        )

    if name in FILE_MODULES:
        path = args.get("path") or args.get("dest") or args.get("name")
        if not path:
            fail(state, f"{name} mock needs a path or destination")
        if name in {"template", "copy"} and (
            path.endswith("/") or state["paths"].get(path) == "directory"
        ):
            path = posixpath.join(path, posixpath.basename(args.get("src", "")))
        if name == "get_curl" and args.get("url"):
            path = destination(state, path, str(args["url"]))
        # Match template/copy semantics for user settings: force: false keeps
        # an existing destination exactly as it is.
        if (
            name in {"template", "copy"}
            and exists(state, path)
            and is_false(args.get("force", True))
        ):
            finish(state, changed=False, skipped=True, path=path, dest=path)
        if args.get("state") == "absent":
            changed = remove(state, path)
        else:
            kind = "directory" if args.get("state") == "directory" else "file"
            content = None
            if kind == "file":
                if name == "template":
                    content = "managed template: " + str(args.get("src", ""))
                elif name == "copy":
                    content = str(
                        args.get("content")
                        or ("managed copy: " + str(args.get("src", "")))
                    )
                elif name == "get_curl":
                    content = "managed download: " + str(args.get("url", ""))
                elif name in {"lineinfile", "blockinfile", "replace", "ini_file"}:
                    content = f"managed {name} write: {path}"
            changed = create(state, path, kind, content)
        finish(state, changed=changed, path=path, dest=path)

    if name in {"group", "user"}:
        finish(state, changed=False)

    if name == "disk_usage":
        finish(state, changed=False, used=1000, mounts=[])

    if name == "git":
        destination_dir = args.get("dest")
        create(state, destination_dir, "directory")
        create(state, posixpath.join(destination_dir, ".git"), "directory")
        finish(state, changed=True, after="mock-commit")

    if name == "get_url":
        dest = args.get("dest") or args.get("path")
        if dest:
            dest = destination(state, dest, str(args.get("url", "")))
            create(state, dest)
        finish(state, changed=False, dest=dest)

    if name in PACKAGE_MODULES:
        finish(state, changed=install_packages(state, args))

    if name in {"unarchive", "mount", "sysctl", "mariadb_user", "postgresql_user"}:
        finish(state, changed=False)

    if name in {"mariadb_db", "postgresql_db"}:
        if args.get("name"):
            state.setdefault("databases", {})[str(args["name"])] = str(
                args.get("state", "present")
            ).lower()
        finish(state, changed=False)

    if name in {"command", "shell"}:
        command_result(state, args)

    if name == "uri":
        status = 302 if str(args.get("method", "GET")).upper() == "POST" else 200
        content = '{"tag_name": "v0.1.5"}'
        finish(
            state,
            changed=False,
            status=status,
            url=args.get("url", ""),
            attempts=1,
            cookies={"MATOMO_SESSID": "mock"},
            content=content,
            json=json.loads(content),
        )

    if name in {"systemd", "systemd_service", "service"}:
        if not args.get("name"):
            finish(state, changed=False)
        service = args["name"]
        installed = os.environ.get("IIAB_MOCK_INSTALLED") == "true"
        if (
            not installed
            and service not in state["services"]
            and not unit_available(state, service)
        ):
            fail(state, f"service {service} is not installed")
        record_service(
            state,
            service,
            enabled=args.get("enabled"),
            service_state=args.get("state"),
        )
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


def enabled_var(role: str) -> str:
    return f"{role_lifecycle.install_prefix(role) or role_var(role)}_enabled"


OWNERSHIP_KINDS = ("user_settings", "program_data", "user_data")
USER_SETTING_SENTINEL = (
    "IIAB lifecycle test: a normal apply must not overwrite this user setting\n"
)
USER_DATA_SENTINEL = "IIAB lifecycle test: user data must survive every operation\n"


def defaults_file(role: str) -> Path | None:
    defaults = ROOT_DIR / "roles" / role / "defaults"
    for name in ("main.yml", "main.yaml"):
        path = defaults / name
        if path.is_file():
            return path
    return None


def load_vars_file(path: Path) -> dict:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError):
        return {}
    return data if isinstance(data, dict) else {}


def resolved_ownership(role: str, vars_file: str = "") -> dict[str, list[str]]:
    """Resolve a role's user_settings/program_data/user_data declarations.

    Role defaults are not loaded as host facts in the lifecycle playbook, so
    resolve the declared paths here with the same vars the test passes to the
    playbook.  This is the test-side half of the Data ownership contract.
    """
    defaults = defaults_file(role)
    if defaults is None:
        return {kind: [] for kind in OWNERSHIP_KINDS}

    raw: dict = load_vars_file(defaults)
    base = Path(vars_file) if vars_file else ROOT_DIR / "vars" / "default_vars.yml"
    raw.update(load_vars_file(base))
    for name in ("main.yml", "main.yaml"):
        raw.update(load_vars_file(ROOT_DIR / "roles" / role / "vars" / name))

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
                names = jinja_meta.find_undeclared_variables(environment.parse(value))
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

    prefix = role_var(role)
    result: dict[str, list[str]] = {}
    for kind in OWNERSHIP_KINDS:
        value = render(raw.get(f"{prefix}_{kind}", []), set())
        if not isinstance(value, list):
            value = []
        result[kind] = [
            str(item)
            for item in value
            if item and "{{" not in str(item) and "{%" not in str(item)
        ]
    return result


def state_has_path(state: dict, path: str) -> bool:
    paths = state.get("paths", {})
    if path in paths:
        return True
    prefix = path.rstrip("/") + "/"
    return any(item.startswith(prefix) for item in paths)


def ownership_content(state: dict, path: str):
    contents = state.get("contents", {})
    if path.rstrip("/") != path:
        return contents.get(path.rstrip("/") + "/.iiab-user-setting")
    return contents.get(path)


def seed_ownership(state: dict, ownership: dict[str, list[str]]) -> None:
    """Seed declared paths so an operation's effect on them is observable."""
    paths = state.setdefault("paths", {})
    contents = state.setdefault("contents", {})

    def seed(path: str, sentinel: str | None):
        kind = "directory" if path.endswith("/") else "file"
        paths[path] = kind
        if sentinel is None:
            return
        if kind == "directory":
            marker = path.rstrip("/") + "/.iiab-user-setting"
            paths[marker] = "file"
            contents[marker] = sentinel
        else:
            contents[path] = sentinel

    for path in ownership["user_settings"]:
        seed(path, USER_SETTING_SENTINEL)
    for path in ownership["user_data"]:
        seed(path, USER_DATA_SENTINEL)


def ownership_problem(
    state: dict,
    ownership: dict[str, list[str]],
    operation: str,
    check_user_settings: bool,
) -> str | None:
    missing = [
        path for path in ownership["user_data"] if not state_has_path(state, path)
    ]
    if missing:
        return f"{operation} removed declared user data: " + ", ".join(missing)

    if check_user_settings:
        changed = [
            path
            for path in ownership["user_settings"]
            if ownership_content(state, path) != USER_SETTING_SENTINEL
        ]
        if changed:
            return (
                f"{operation} overwrote declared user settings: "
                + ", ".join(changed)
            )
    return None


def ownership_warnings(role: str, vars_file: str = "") -> list[Warning]:
    """Warn when a path is declared in more than one ownership class."""
    ownership = resolved_ownership(role, vars_file)
    classes: dict[str, list[str]] = {}
    for kind in OWNERSHIP_KINDS:
        for path in ownership[kind]:
            classes.setdefault(path.rstrip("/"), []).append(kind)

    defaults = defaults_file(role)
    location = (
        str(defaults.relative_to(ROOT_DIR)) if defaults else f"roles/{role}/defaults"
    )
    return [
        Warning(
            location,
            None,
            f"{path} is declared as both {' and '.join(kinds)}; a path belongs "
            "to exactly one ownership class",
        )
        for path, kinds in classes.items()
        if len(kinds) > 1
    ]


def initial_state(role: str, installed: bool = False) -> dict:
    return {
        "paths": {
            "/etc/systemd/system": "directory",
            "/lib/systemd/system": "directory",
            "/usr/lib/systemd/system": "directory",
        },
        "contents": {},
        "services": {"nginx": {"enabled": True, "state": "started"}},
        "packages": {},
    }


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
    """A lifecycle finding."""

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


def print_warnings(warnings: list[Warning], header: str | None = None) -> None:
    if not warnings:
        return
    if header:
        print(f"  {header}: {len(warnings)}")
    for item in warnings:
        print(item.text(), end="")


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
) -> str:
    lifecycle = lifecycle or {}
    play = {
        "hosts": "localhost",
        "connection": "local",
        "gather_facts": False,
        "vars_files": [vars_file or str(ROOT_DIR / "vars" / "default_vars.yml")],
        "module_defaults": {"iiab_state": {"path": "{{ iiab_state_file }}"}},
        "vars": {
            "ansible_python_interpreter": sys.executable,
            "ansible_facts": {
                "machine": "x86_64",
                "distribution": "Debian",
                "distribution_major_version": "13",
                "distribution_version": "13.0",
                "pkg_mgr": "apt",
                "default_ipv4": {"alias": "eth0", "gateway": "192.0.2.1"},
                "ansible_local": {
                    "local_facts": {
                        "systemd_networkd": "disabled",
                        "network_manager": "disabled",
                        "dhcpcd": "disabled",
                    }
                },
            },
            "is_proot": False,
            "iiab_stage": 8,
            "no_net_restart": False,
            "iiab_wireless_lan_iface": "wlan0",
            "iiab_lan_iface": "eth0",
            "iiab_wan_iface": "eth0",
            "rpi_model": "none",
            "os_ver": "debian-13",
            "is_debian": True,
            "is_raspbian": False,
            "is_ubuntu": False,
            "is_linuxmint": False,
            "dpkg_arch": {"stdout": "amd64"},
            "php_version": "8.2",
            "python_version": "3.14",
            "skip_role_on_error": False,
            "iiab_mock_state": str(scenario / "state.json"),
            "iiab_mock_installed": str(installed).lower(),
        },
        "environment": {
            "IIAB_MOCK_STATE": str(scenario / "state.json"),
            "IIAB_MOCK_INSTALLED": str(installed).lower(),
        },
        "tasks": [
            {
                "set_fact": {
                    install_name: True,
                    enabled_name: enabled,
                    "uninstall": bool(lifecycle.get("uninstall", False)),
                    "reinstall": bool(lifecycle.get("reinstall", False)),
                }
            },
        ],
    }
    # Roles notify the shared NGINX handlers in 0-init.  Load them without
    # running 0-init's tasks, so each role can still be tested on its own.
    play["tasks"].extend(
        [
            {
                "name": "Load the shared handlers from 0-init",
                "include_role": {"name": "0-init", "tasks_from": "noop"},
            },
            {"include_role": {"name": role}},
        ]
    )
    return yaml.safe_dump([play], sort_keys=False)


def create_mock_library(directory: Path) -> Path:
    library = directory / "library"
    library.mkdir()
    (library / "iiab_state").symlink_to(ROOT_DIR / "modules" / "iiab_state.py")
    module = directory / "mock-module.py"
    module.write_text(MOCK_MODULE_SOURCE, encoding="utf-8")
    module.chmod(0o755)
    actions = directory / "actions"
    actions.mkdir()
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
    }
    for name in names:
        (library / name).symlink_to(module)
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
    # default_vars.yml sets skip_role_on_error: True, and vars_files beat
    # play-level vars. Force it as an extra var so a real role failure fails
    # the lifecycle test instead of silently passing.
    scenario_vars = {
        "skip_role_on_error": False,
        "iiab_state_file": str(state_file.parent / "iiab_state.yml"),
    }
    scenario_vars.update(extra_vars or {})
    command = [
        shutil.which("ansible-playbook") or "ansible-playbook",
        "--forks=1",
        "-i",
        "localhost,",
        str(playbook),
        "--extra-vars",
        json.dumps(scenario_vars),
    ]
    return subprocess.run(
        command,
        cwd=ROOT_DIR,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )


def marker_present(state_yaml: Path, role: str) -> bool:
    prefix = re.escape(role_var(role))
    return (
        re.search(
            rf"^{prefix}_(?:installed|downloaded): True$",
            state_yaml.read_text(encoding="utf-8"),
            re.MULTILINE,
        )
        is not None
    )


def scenario_failure(output: list[str], result) -> str:
    output.append("FAIL\n")
    output.append("".join(result.stdout.splitlines(True)[-40:]))
    output.append("".join(result.stderr.splitlines(True)[-40:]))
    return "".join(output)


def run_scenario(
    title: str,
    role: str,
    vars_file: str,
    library: Path,
    scenario: Path,
    enabled_name: str,
    install_name: str,
    steps: list[tuple[str, dict, bool | None]],
    seed_marker: bool = False,
    initial_installed: bool = False,
    check_user_settings: bool = True,
) -> str:
    """Run lifecycle steps in one virtual host.

    Each step is (name, values, expect_marker).  expect_marker True requires
    the installed marker afterwards, False requires it to be gone, and None
    skips the check.  Declared ownership is seeded before the first step so a
    normal apply cannot silently overwrite user settings or delete user data.
    """
    scenario.mkdir()
    prepare_controller_files(scenario)
    state_yaml = scenario / "iiab_state.yml"
    if seed_marker:
        state_yaml.write_text(f"{role_var(role)}_installed: True\n", encoding="utf-8")
    else:
        state_yaml.touch()
    state_file = scenario / "state.json"
    ownership = resolved_ownership(role, vars_file)
    state = initial_state(role, initial_installed)
    seed_ownership(state, ownership)
    state_file.write_text(json.dumps(state), encoding="utf-8")
    output = [f"  {title:<19}"]

    for name, values, expect_marker in steps:
        playbook = scenario / f"{name}.yml"
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
        result = run_ansible(
            playbook,
            library,
            state_file,
            installed=values["installed"],
            extra_vars={
                install_name: True,
                enabled_name: values["enabled"],
                "uninstall": values.get("uninstall", False),
                "reinstall": values.get("reinstall", False),
            },
        )
        if result.returncode:
            return scenario_failure(output, result)
        if expect_marker is not None and marker_present(state_yaml, role) != expect_marker:
            problem = (
                "did not remove the role's markers"
                if not expect_marker
                else "did not keep the role's installed marker"
            )
            output.append(f"FAIL\n{name} {problem}\n")
            output.append(state_yaml.read_text(encoding="utf-8"))
            return "".join(output)

    final_state = json.loads(state_file.read_text(encoding="utf-8"))
    problem = ownership_problem(
        final_state, ownership, title, check_user_settings=check_user_settings
    )
    if problem:
        output.append(f"FAIL\n{problem}\n")
        output.append(state_file.read_text(encoding="utf-8"))
        return "".join(output)

    output.append("PASS\n")
    return "".join(output)


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
    expect_marker = {"uninstall": False, "reinstall": True}.get(name)
    return run_scenario(
        name,
        role,
        vars_file,
        library,
        temp_dir / name,
        enabled_name,
        install_name,
        [(name, values, expect_marker)],
        # ./runrole leaves markers in place during --reinstall, so start the
        # same way and prove the role does not remove them while rebuilding.
        seed_marker=name == "reinstall",
        initial_installed=values["installed"],
        # --reinstall may reset user settings; only user data must survive.
        check_user_settings=name != "reinstall",
    )


def clean_install_result(
    role: str,
    vars_file: str,
    library: Path,
    temp_dir: Path,
    enabled_name: str,
    install_name: str,
) -> str:
    """Mirror --clean-install: uninstall then a normal apply on one host."""
    return run_scenario(
        "clean-install",
        role,
        vars_file,
        library,
        temp_dir / "clean-install",
        enabled_name,
        install_name,
        [
            (
                "clean-install-uninstall",
                {"installed": True, "enabled": True, "uninstall": True, "reinstall": False},
                False,
            ),
            (
                "clean-install-install",
                {"installed": False, "enabled": True, "uninstall": False, "reinstall": False},
                True,
            ),
        ],
        initial_installed=True,
    )


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
    ]
    skipped: list[str] = []
    if role_supports(role, "reinstall"):
        operations.append(("reinstall", {"installed": True, "enabled": True, "reinstall": True}))
    else:
        skipped.append("reinstall")
    uninstall_supported = role_supports(role, "uninstall")
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
    ownership = ownership_warnings(role, vars_file)
    print_warnings(ownership, "ownership declarations")
    if not quiet:
        for name in skipped:
            print(f"  {name:<19} SKIP (unsupported)")

    with tempfile.TemporaryDirectory(prefix="iiab-role-lifecycle.") as directory:
        temp_dir = Path(directory)
        library = create_mock_library(temp_dir)
        failures = 0
        for name, values in operations:
            if name == "clean-install":
                output = clean_install_result(
                    role, vars_file, library, temp_dir, enabled_name, install_name
                )
            else:
                values.setdefault("uninstall", False)
                values.setdefault("reinstall", False)
                output = operation_result(
                    name,
                    role,
                    vars_file,
                    library,
                    temp_dir,
                    enabled_name,
                    install_name,
                    values,
                )
            if not quiet or "FAIL" in output:
                print(output, end="")
            if "FAIL\n" in output:
                failures = 1
    # A path in more than one ownership class makes preservation ambiguous, so
    # it is an error even without --strict.
    if ownership:
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
