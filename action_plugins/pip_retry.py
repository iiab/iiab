# -*- coding: utf-8 -*-
# Copyright: (c) 2026, IIAB contributors
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""pip_retry -- run ansible.builtin.pip with whole-task retries.

WHY THIS EXISTS
---------------
`register`, `until`, `retries` and `delay` are *task keywords*, not pip module
arguments.  Ansible has no "task defaults" mechanism, so `module_defaults`
cannot set them (it only feeds module parameters -- putting `retries` under
`module_defaults: pip:` fails with "Unsupported parameters for (pip) module").
That forces every call site to repeat this 4-line stanza:

    register: result
    until: result is succeeded
    retries: 5
    delay: 10

This action plugin exposes `retries`/`delay` as ordinary module arguments, so
they *can* be defaulted once:

    module_defaults:
      pip_retry:
        retries: 5
        delay: 10

It delegates the real work to ansible.builtin.pip on every attempt, so venv
creation, requirements files, extra_args, check mode, become, environment and
every other pip feature behave exactly as upstream -- no pip logic is
duplicated or forked here.

USAGE
-----
    - name: Install packages
      pip_retry:
        name:
          - jupyterlab
          - jupyterhub
        virtualenv: /opt/iiab/jupyterhub
        virtualenv_command: python3 -m venv /opt/iiab/jupyterhub
        extra_args: --no-cache-dir --prefer-binary

Any ansible.builtin.pip argument may be passed through unchanged.
`retries` keeps Ansible's task-keyword semantics: it is the number of
*additional* attempts, so `retries: 5` means up to 6 tries.

Unlike `until: result is succeeded`, deterministic failures ("No matching
distribution found", build errors, PEP 668 externally-managed environments,
...) are NOT retried, because they can never succeed.  Override the default
list with `retry_on:` (a list of substrings that ARE worth retrying).
"""
from __future__ import annotations

import time

from ansible.plugins.action import ActionBase
from ansible.utils.display import Display

display = Display()

#: Number of additional attempts after the first one (task-keyword semantics).
DEFAULT_RETRIES = 5
#: Seconds to wait between attempts.
DEFAULT_DELAY = 10

#: Errors that will never succeed on a retry.  Matching on the message avoids
#: burning the whole retry budget on a typo, a missing compiler or PEP 668.
PERMANENT_FAILURES = (
    "No matching distribution found",
    "Could not find a version that satisfies the requirement",
    "Invalid requirement",
    "is not a valid",
    "externally-managed-environment",
    "Externally managed environment",
    "Could not build wheels",
    "subprocess-exited-with-error",
    "No module named",
    "Unable to find any of",
)


class ActionModule(ActionBase):
    """Retry ansible.builtin.pip as a single, defaultable task."""

    TRANSFERS_FILES = False
    _supports_check_mode = True
    _supports_async = False

    def run(self, tmp=None, task_vars=None):
        # ActionBase.run() enforces async/check-mode support and returns the
        # (normally empty) seed result.
        base_result = super(ActionModule, self).run(tmp, task_vars)
        task_vars = task_vars or {}

        args = dict(self._task.args)
        try:
            retries = int(args.pop("retries", DEFAULT_RETRIES))
            delay = float(args.pop("delay", DEFAULT_DELAY))
        except (TypeError, ValueError):
            return dict(
                failed=True,
                msg="pip_retry: 'retries' must be an integer and 'delay' a number",
            )

        retry_on = args.pop("retry_on", None)
        if isinstance(retry_on, str):
            retry_on = [retry_on]

        # Ansible's `retries` keyword means "additional attempts", so the total
        # is retries + 1 (this also keeps `retries: 5` behaviour on migration).
        attempts = max(0, retries) + 1
        result = {}

        for attempt in range(1, attempts + 1):
            result = self._execute_module(
                module_name="ansible.builtin.pip",
                module_args=dict(args),
                task_vars=task_vars,
            )
            result.update(base_result)

            if not result.get("failed"):
                if attempts > 1:
                    result["attempts"] = attempt
                return result

            failure_text = self._failure_text(result)
            if retry_on is not None:
                retryable = any(str(s) in failure_text for s in retry_on)
            else:
                retryable = not any(
                    str(s) in failure_text for s in PERMANENT_FAILURES
                )

            if not retryable or attempt >= attempts:
                result["attempts"] = attempt
                return result

            display.vvv(
                "pip_retry: attempt %d of %d failed, retrying in %ss"
                % (attempt, attempts, delay)
            )
            if delay > 0:
                time.sleep(delay)

        # Unreachable, but keeps static analysers happy.
        return result

    @staticmethod
    def _failure_text(result):
        return "\n".join(
            str(result.get(key, "")) for key in ("msg", "stderr", "stdout")
        )
