#!/usr/bin/env python3
"""Smoke-test ./runrole without running Ansible or touching /etc.

The lifecycle test covers a role's phases.  This test covers the command-line
driver around them: read-only commands, preflight failures, the extra variables
that select an operation, and the requirement that a failed multi-role
reinstall only affects the role that ran.

Ansible and ansible-playbook are replaced with stubs on PATH.  The state file
and local_vars.yml live in a temporary directory, and IIAB_SKIP_LOCAL_FACTS
keeps the driver from copying facts into /etc/ansible.
"""

from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
RUNROLE = ROOT_DIR / "runrole"
IIAB_STATE = ROOT_DIR / "scripts" / "iiab-state"

FAKE_ANSIBLE = """#!/bin/bash
exit 0
"""

FAKE_ANSIBLE_PLAYBOOK = """#!/bin/bash
printf '%s\\n' "$*" >> "$FAKE_ANSIBLE_LOG"
exit "${FAKE_ANSIBLE_EXIT:-0}"
"""


def load_role_lifecycle():
    spec = importlib.util.spec_from_file_location(
        "iiab_role_lifecycle_test", ROOT_DIR / "scripts" / "role_lifecycle.py"
    )
    if spec is None or spec.loader is None:
        raise SystemExit("could not load scripts/role_lifecycle.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Harness:
    def __init__(self, root: Path):
        self.root = root
        self.bin_dir = root / "bin"
        self.bin_dir.mkdir()
        self.fake_log = root / "ansible-playbook.log"
        self.state = root / "iiab_state.yml"
        self.local_vars = root / "local_vars.yml"
        self.env = os.environ.copy()
        self.env.update(
            {
                "PATH": f"{self.bin_dir}{os.pathsep}{self.env['PATH']}",
                "IIAB_STATE_FILE": str(self.state),
                "LOCAL_VARS_FILE": str(self.local_vars),
                "IIAB_SKIP_LOCAL_FACTS": "1",
                "FAKE_ANSIBLE_LOG": str(self.fake_log),
                "ANSIBLE_LOG_PATH": str(root / "iiab-debug.log"),
            }
        )
        (self.bin_dir / "ansible").write_text(FAKE_ANSIBLE, encoding="utf-8")
        (self.bin_dir / "ansible-playbook").write_text(
            FAKE_ANSIBLE_PLAYBOOK, encoding="utf-8"
        )
        for name in ("ansible", "ansible-playbook"):
            (self.bin_dir / name).chmod(0o755)
        shutil.copyfile(ROOT_DIR / "vars" / "default_vars.yml", self.local_vars)

    def set_local_vars(self, text: str) -> None:
        self.local_vars.write_text(text, encoding="utf-8")

    def set_state(self, text: str) -> None:
        self.state.write_text(text, encoding="utf-8")

    def reset_log(self) -> None:
        self.fake_log.write_text("", encoding="utf-8")

    def run(self, *args: str, exit_code: int = 0):
        env = self.env.copy()
        env["FAKE_ANSIBLE_EXIT"] = str(exit_code)
        self.reset_log()
        return subprocess.run(
            [str(RUNROLE), *args],
            cwd=ROOT_DIR,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def playbook_calls(self) -> list[str]:
        if not self.fake_log.is_file():
            return []
        return [line for line in self.fake_log.read_text().splitlines() if line]

    def is_installed(self, prefix: str) -> bool:
        return (
            subprocess.run(
                [str(IIAB_STATE), "--file", str(self.state), "is-installed", prefix],
                text=True,
                capture_output=True,
                check=False,
            ).returncode
            == 0
        )


def check(results: list[str], name: str, condition: bool, detail: str = "") -> None:
    results.append(name)
    if condition:
        print(f"  {name:<44} PASS")
        return
    print(f"  {name:<44} FAIL")
    if detail:
        print(detail)
    raise SystemExit(1)


def test_role_lifecycle_detection(results: list[str]) -> None:
    role_lifecycle = load_role_lifecycle()
    with tempfile.TemporaryDirectory() as directory:
        roles = Path(directory) / "roles"
        original = role_lifecycle.ROLES_DIR
        role_lifecycle.ROLES_DIR = roles
        try:
            def add_role(name: str, main: str, manifest: str = "") -> None:
                tasks = roles / name / "tasks"
                tasks.mkdir(parents=True)
                (tasks / "main.yml").write_text(main, encoding="utf-8")
                if manifest:
                    meta = roles / name / "meta"
                    meta.mkdir()
                    (meta / "runrole.yml").write_text(manifest, encoding="utf-8")

            add_role(
                "bare-uninstall",
                "---\n- name: Remove it\n  file:\n    path: /tmp/x\n    state: absent\n  when: uninstall\n",
            )
            add_role(
                "internal-uninstall",
                "---\n- name: Remove it\n  file:\n    path: /tmp/x\n    state: absent\n  when: iiab_role_uninstall | bool\n",
            )
            add_role(
                "not-internal-uninstall",
                "---\n- name: Keep it\n  debug:\n    msg: keep\n  when: not iiab_role_uninstall\n",
            )
            add_role(
                "manifest-comment",
                "---\n- debug:\n    msg: hello\n",
                "reinstall: false  # documented opt-out\n",
            )
            add_role(
                "manifest-commented-out",
                "---\n- debug:\n    msg: hello\n",
                "# reinstall: false\n",
            )
            add_role(
                "manifest-uninstall",
                "---\n- debug:\n    msg: hello\n",
                "uninstall: true\n",
            )
            add_role(
                "converted-without-phase",
                "---\n- name: Run the lifecycle\n  include_role:\n    name: 0-init\n    tasks_from: lifecycle\n",
                "uninstall: true\n",
            )

            check(
                results,
                "detects when: uninstall",
                role_lifecycle.supports_uninstall("bare-uninstall"),
            )
            check(
                results,
                "detects when: iiab_role_uninstall",
                role_lifecycle.supports_uninstall("internal-uninstall"),
            )
            check(
                results,
                "ignores when: not iiab_role_uninstall",
                not role_lifecycle.supports_uninstall("not-internal-uninstall"),
            )
            check(
                results,
                "manifest value with trailing comment",
                role_lifecycle._manifest_value("manifest-comment", "reinstall")
                is False,
            )
            check(
                results,
                "commented-out manifest value is ignored",
                role_lifecycle._manifest_value(
                    "manifest-commented-out", "reinstall"
                )
                is None,
            )
            check(
                results,
                "manifest uninstall flag is honored",
                role_lifecycle.supports_uninstall("manifest-uninstall"),
            )
            check(
                results,
                "manifest cannot add a phase to a converted role",
                not role_lifecycle.supports_uninstall("converted-without-phase"),
            )
        finally:
            role_lifecycle.ROLES_DIR = original


def test_runrole(results: list[str], harness: Harness) -> None:
    harness.set_state("")

    result = harness.run("--list")
    check(results, "--list exits 0", result.returncode == 0, result.stderr)
    check(results, "--list lists awstats", "awstats" in result.stdout)

    result = harness.run("--status", "awstats")
    check(results, "--status exits 0", result.returncode == 0, result.stderr)
    check(results, "--status shows not installed", "not installed" in result.stdout)

    result = harness.run("--check-local-vars", "firmware")
    check(
        results,
        "--check-local-vars helper role exits 0",
        result.returncode == 0,
        result.stderr,
    )
    check(
        results,
        "--check-local-vars helper skips Ansible",
        "Nothing to validate" in result.stdout and not harness.playbook_calls(),
        result.stdout,
    )

    result = harness.run("--uninstall", "awstats")
    check(
        results,
        "--uninstall without markers fails",
        result.returncode == 1 and "no installed markers" in result.stderr,
        result.stderr,
    )
    check(
        results,
        "--uninstall preflight runs no playbook",
        not harness.playbook_calls(),
        str(harness.playbook_calls()),
    )

    # A failed multi-role reinstall must not erase the next role's markers.
    harness.set_state(
        "bluetooth_installed: True\nsshd_installed: True\n"
    )
    result = harness.run("--reinstall", "bluetooth", "sshd", exit_code=1)
    check(
        results,
        "--reinstall failure exits 1",
        result.returncode == 1,
        result.stderr,
    )
    check(
        results,
        "--reinstall ran only the first role",
        len(harness.playbook_calls()) == 1,
        str(harness.playbook_calls()),
    )
    check(
        results,
        "--reinstall removes the failed role's marker",
        not harness.is_installed("bluetooth"),
    )
    check(
        results,
        "--reinstall keeps later roles' markers",
        harness.is_installed("sshd"),
    )

    # --add must pass the install var and the generic/internal operation flags.
    local_vars = harness.local_vars.read_text(encoding="utf-8")
    harness.set_local_vars(
        local_vars.replace("awstats_install: True", "awstats_install: False")
    )
    harness.set_state("")
    result = harness.run("--add", "awstats")
    check(results, "--add exits 0", result.returncode == 0, result.stderr)
    calls = " ".join(harness.playbook_calls())
    check(results, "--add passes the install override", "awstats_install" in calls)
    check(
        results,
        "apply passes uninstall/upgrade=false",
        "uninstall" in calls and "upgrade" in calls,
        calls,
    )

    # --uninstall must pass the bare and internal flags.  The stub leaves the
    # marker, so the driver reports the mismatch and exits 1.
    harness.set_state("awstats_installed: True\n")
    result = harness.run("-y", "--uninstall", "awstats")
    calls = " ".join(harness.playbook_calls())
    check(
        results,
        "--uninstall passes uninstall=true",
        "uninstall" in calls and "iiab_role_uninstall" in calls,
        calls,
    )
    check(
        results,
        "--uninstall verifies the marker",
        result.returncode == 1 and "markers are still" in result.stderr,
        result.stderr,
    )


def main() -> int:
    results: list[str] = []
    with tempfile.TemporaryDirectory() as directory:
        harness = Harness(Path(directory))
        print("Testing ./runrole command handling...")
        test_runrole(results, harness)
        print("Testing role lifecycle detection...")
        test_role_lifecycle_detection(results)
    print(f"\n{len(results)} checks passed.")
    leftovers = list(ROOT_DIR.glob("runrole-tmp*.yml"))
    if leftovers:
        print("ERROR: temporary playbooks left behind:", leftovers)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
