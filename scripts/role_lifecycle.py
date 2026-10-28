#!/usr/bin/env python3
"""Role metadata shared by ./runrole, ./runroles, and the lifecycle test.

This module is the single source of truth for:

* the role name -> state-marker prefix mapping (``calibre-web`` ->
  ``calibreweb``);
* the role name -> install/enabled prefix mapping (``iiab-admin`` ->
  ``admin_console``);
* which extended operations a role implements;
* which roles are runnable (``roles/<name>/tasks/main.yml`` exists).

``runrole`` and ``runroles`` call the CLI (see ``main``) so the shell and the
Python lifecycle test can never disagree about whether a flag is supported.
Only the standard library is used, so this runs before Ansible is installed.

An extended operation is derived, not declared:

* ``--clean-install`` is ``--uninstall`` followed by a normal apply, so a role
  supports it exactly when it supports ``--uninstall``;
* ``--reinstall`` is available to every role unless ``meta/runrole.yml`` sets
  ``reinstall: false`` (e.g. azuracast requires manual Docker cleanup);
* ``--uninstall`` is supported when the role's entry point hands off to
  ``tasks/uninstall.yml`` or guards work with ``when: uninstall`` inline.
  An unused ``uninstall.yml`` alone does not opt a role in. ``meta/runrole.yml``
  can opt in a role whose implementation cannot be detected from its tasks.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
ROLES_DIR = ROOT_DIR / "roles"

SKIP_ROLE_DIRS = {"0-DEPRECATED-ROLES"}

ROLE_NAME = re.compile(r"[A-Za-z0-9_-]+")

# Roles whose state-marker prefix differs from the directory name.
ROLE_VAR_OVERRIDES = {
    "calibre-web": "calibreweb",
    "iiab-admin": "iiab_admin",
    "osm-vector-maps": "osm_vector_maps",
}

# Roles whose install/enabled prefix differs from their marker prefix.
# iiab-admin is the important case: its marker is iiab_admin_installed, but
# the Admin Console's configuration vars are admin_console_*.
INSTALL_PREFIX_OVERRIDES = {
    "iiab-admin": "admin_console",
}

# Helper roles that are always installed/configured by a stage playbook.  They
# have no <role>_install / <role>_enabled vars, so runrole must not invent them
# or report a conflict when they have a state marker.
NO_INSTALL_PREFIX = {"firmware", "pylibs", "www_base", "www_options"}

INCLUDE = re.compile(
    r"^\s*(-\s+)?(?:include_tasks|import_tasks):\s*['\"]?"
    r"(?:[^'\"]*/)?(?P<feature>[A-Za-z0-9_-]+)(?:\.ya?ml)?['\"]?\s*$",
    re.MULTILINE,
)

# A role whose entry point hands off to 0-init's shared lifecycle runner.
LIFECYCLE_RUNNER = re.compile(
    r"^\s*tasks_from:\s*['\"]?lifecycle['\"]?\s*$",
    re.MULTILINE,
)


def role_var(role: str) -> str:
    """Return the state-marker prefix used by *role*."""
    return ROLE_VAR_OVERRIDES.get(role, role)


def install_prefix(role: str) -> str:
    """Return the prefix for <prefix>_install / <prefix>_enabled.

    An empty string means the role has no install/enabled switches: it is a
    helper role that a stage playbook always runs.
    """
    if role in NO_INSTALL_PREFIX:
        return ""
    return INSTALL_PREFIX_OVERRIDES.get(role, role_var(role))


def tasks_dir(role: str) -> Path:
    return ROLES_DIR / role / "tasks"


def entrypoint(role: str) -> Path | None:
    """Return the role's tasks/main.yml (or main.yaml), if it has one."""
    directory = tasks_dir(role)
    for name in ("main.yml", "main.yaml"):
        path = directory / name
        if path.is_file():
            return path
    return None


def exists(role: str) -> bool:
    """True when *role* is a runnable role directory."""
    return bool(ROLE_NAME.fullmatch(role)) and entrypoint(role) is not None


def available_roles() -> list[str]:
    """Return every runnable role, excluding stage roles and deprecated roles."""
    roles = []
    if not ROLES_DIR.is_dir():
        return roles
    for role_dir in sorted(ROLES_DIR.iterdir()):
        if not role_dir.is_dir() or role_dir.name in SKIP_ROLE_DIRS:
            continue
        if re.match(r"^\d-", role_dir.name):
            continue
        if any((role_dir / "tasks" / name).is_file() for name in ("main.yml", "main.yaml")):
            roles.append(role_dir.name)
    return roles


def _manifest_value(role: str, feature: str) -> bool | None:
    """Return a meta/runrole.yml boolean, or None when it is not declared."""
    path = ROLES_DIR / role / "meta" / "runrole.yml"
    if not path.is_file():
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    match = re.search(
        rf"^{re.escape(feature)}:\s*(true|false|yes|no|on|off)\s*$",
        text,
        re.IGNORECASE | re.MULTILINE,
    )
    if match is None:
        return None
    return match.group(1).lower() in {"true", "yes", "on"}


def _manifest_says(role: str, feature: str) -> bool:
    return _manifest_value(role, feature) is True


def _entrypoint_implements(role: str, feature: str) -> bool:
    """True when main.yml hands off to *feature*.yml or gates on it inline."""
    path = entrypoint(role)
    if path is None:
        return False
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return False
    if any(match.group("feature") == feature for match in INCLUDE.finditer(text)):
        return True
    for line in text.splitlines():
        stripped = line.strip()
        if re.match(rf"^-\s+not\s+{re.escape(feature)}\s*$", stripped):
            continue
        if re.match(rf"^-\s+{re.escape(feature)}\s*$", stripped):
            return True
        if re.match(rf"^{re.escape(feature)}(?:\s+(?:or|and))?\s*(#.*)?$", stripped):
            return True
        if "when:" in line:
            if re.search(rf"\bnot\s+{re.escape(feature)}\b", line):
                continue
            if re.search(rf"\b{re.escape(feature)}\b", line.split("when:", 1)[1]):
                return True
    return False


def _uses_lifecycle_runner(role: str) -> bool:
    """True when main.yml hands off to 0-init's shared lifecycle runner."""
    path = entrypoint(role)
    if path is None:
        return False
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return False
    return LIFECYCLE_RUNNER.search(text) is not None


def supports_uninstall(role: str) -> bool:
    if not exists(role):
        return False
    if _manifest_says(role, "uninstall"):
        return True
    if _uses_lifecycle_runner(role):
        # The runner calls tasks/uninstall.yml when uninstall is set.  An
        # unused uninstall.yml alone still does not opt a role in.
        return (tasks_dir(role) / "uninstall.yml").is_file()
    return _entrypoint_implements(role, "uninstall")


def supports(role: str, feature: str) -> bool:
    """True when *role* implements *feature*.

    ``clean_install`` is the derived pair uninstall-then-install, so it is
    supported exactly when ``uninstall`` is.

    ``reinstall`` is available to ordinary roles, but a role may explicitly
    opt out in ``meta/runrole.yml`` (``reinstall: false``) when rebuilding it
    requires manual cleanup that runrole must not pretend to automate.
    """
    if feature == "reinstall":
        return exists(role) and _manifest_value(role, "reinstall") is not False
    if feature in ("uninstall", "clean_install"):
        return supports_uninstall(role)
    raise ValueError(f"unknown feature: {feature}")


def capabilities(role: str) -> list[str]:
    """Return the extended operations *role* accepts, in escalation order."""
    result = []
    if supports(role, "reinstall"):
        result.append("reinstall")
    if supports_uninstall(role):
        result.extend(["uninstall", "clean_install"])
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Report IIAB role names, variable prefixes, and capabilities.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    var = subparsers.add_parser("var", help="print a role's state-marker prefix")
    var.add_argument("role")

    install_var = subparsers.add_parser(
        "install-var",
        help="print a role's <prefix>_install/<prefix>_enabled prefix (empty if none)",
    )
    install_var.add_argument("role")

    exists_parser = subparsers.add_parser("exists", help="exit 0 when the role exists")
    exists_parser.add_argument("role")

    supports_parser = subparsers.add_parser(
        "supports", help="exit 0 when the role implements a feature"
    )
    supports_parser.add_argument("role")
    supports_parser.add_argument("feature", choices=["reinstall", "uninstall", "clean_install"])

    capabilities_parser = subparsers.add_parser(
        "capabilities", help="print the role's extended operations"
    )
    capabilities_parser.add_argument("role")

    subparsers.add_parser("list", help="print every runnable role, one per line")

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "list":
        for role in available_roles():
            print(role)
        return 0

    if args.command == "exists":
        return 0 if exists(args.role) else 1
    if args.command == "supports":
        return 0 if supports(args.role, args.feature) else 1

    if not exists(args.role):
        print(f"role_lifecycle: unknown role: {args.role}", file=sys.stderr)
        return 2

    if args.command == "var":
        print(role_var(args.role))
        return 0
    if args.command == "install-var":
        print(install_prefix(args.role))
        return 0
    if args.command == "capabilities":
        print(" ".join(capabilities(args.role)))
        return 0

    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
