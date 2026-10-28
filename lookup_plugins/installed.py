"""Look up an optional IIAB state marker safely.

``*_installed`` (and similar) variables only exist after a role has written
them to the state file.  Testing one directly raises when the role was never
installed.  Use this lookup for boolean checks:

    when: lookup('installed', 'mysql')

The lookup accepts either the role name or the full marker name, and returns
false when the marker is undefined.  It reads the marker from the play's
variables when the state file was loaded through ``vars_files``; otherwise it
falls back to ``iiab_state_file`` directly, so a playbook or test can use the
lookup without loading the file.  The file itself is parsed by
``modules/iiab_state.py``, the same code the ``iiab_state`` module and
``scripts/iiab-state`` use.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from ansible.errors import AnsibleError
from ansible.module_utils.parsing.convert_bool import boolean
from ansible.plugins.lookup import LookupBase

# scripts/iiab_state_lib.py is shared with ./scripts/iiab-state, so both
# callers find and load modules/iiab_state.py the same way.
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from iiab_state_lib import LoadError, load_state_module  # noqa: E402

_UNDEFINED = object()
_CACHE = {}

try:
    state_module = load_state_module()
except LoadError as error:
    raise AnsibleError(f"Could not load modules/iiab_state.py: {error}") from error


def _load_state(path):
    try:
        status = os.stat(path)
    except FileNotFoundError:
        return {}
    except OSError as error:
        raise AnsibleError(f"Could not read IIAB state file {path}: {error}") from error

    cache_key = (path, status.st_ino, status.st_mtime_ns, status.st_size)
    if cache_key in _CACHE:
        return _CACHE[cache_key]

    try:
        data, _ = state_module.load_state(path)
    except state_module.StateError as error:
        raise AnsibleError(str(error)) from error

    _CACHE[cache_key] = data
    return data


class LookupModule(LookupBase):
    def run(self, terms, variables=None, **kwargs):
        variables = variables or {}
        path = variables.get("iiab_state_file") or state_module.DEFAULT_PATH
        # Lookup variables can still be raw templates.
        path = self._templar.template(path)

        results = []
        for term in terms:
            marker = str(term)
            if not marker.endswith(("_installed", "_downloaded")):
                marker += "_installed"

            value = variables.get(marker, _UNDEFINED)
            if value is _UNDEFINED:
                value = _load_state(path).get(marker, False)

            try:
                results.append(boolean(value, strict=False))
            except (TypeError, ValueError):
                results.append(bool(value))
        return results
