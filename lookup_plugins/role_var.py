"""Look up an IIAB role's variable/marker prefix.

The directory name and the variable prefix differ for a few roles, e.g.
``calibre-web`` uses ``calibreweb_install`` and ``calibreweb_installed``.
``scripts/role_lifecycle.py`` owns that mapping; this plugin is only a thin
Ansible wrapper so role task files do not hard-code prefixes:

    lifecycle_prefix: "{{ lookup('role_var', role_name) }}"

Pass ``kind='install'`` for the ``<prefix>_install`` / ``<prefix>_enabled``
prefix (``iiab-admin`` -> ``admin_console``), or an empty string for helper
roles that have no install/enabled switches.
"""

from __future__ import annotations

import sys
from pathlib import Path

from ansible.plugins.lookup import LookupBase

# scripts/role_lifecycle.py is shared with ./runrole and the lifecycle test.
# It only uses the standard library, so it also works before
# Ansible is installed when those tools import it directly.
_SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from role_lifecycle import install_prefix, role_var  # noqa: E402


class LookupModule(LookupBase):
    def run(self, terms, variables=None, kind="marker", **kwargs):
        # kind='install' returns the <prefix>_install / <prefix>_enabled
        # prefix (iiab-admin -> admin_console), or '' for helper roles.
        lookup = install_prefix if kind == "install" else role_var
        return [lookup(str(term)) for term in terms]
