"""Locate and import ``modules/iiab_state.py`` from an arbitrary caller.

``scripts/iiab-state`` and ``lookup_plugins/installed.py`` both need the state
parser, but neither can rely on the repository's ``modules`` directory being on
``sys.path``.  Keeping the lookup logic here means the candidate list and the
error handling cannot drift apart.
"""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path

_MODULE = None


class LoadError(Exception):
    """modules/iiab_state.py could not be found or imported."""


def candidates() -> list[Path]:
    return [
        Path(__file__).resolve().parents[1] / "modules" / "iiab_state.py",
        Path(os.environ.get("IIAB_DIR", "/opt/iiab/iiab")) / "modules" / "iiab_state.py",
    ]


def load_state_module():
    """Return modules/iiab_state.py as a module, loading it once per process."""
    global _MODULE
    if _MODULE is not None:
        return _MODULE

    path = next((candidate for candidate in candidates() if candidate.is_file()), None)
    if path is None:
        tried = ", ".join(str(candidate) for candidate in candidates())
        raise LoadError(f"could not find modules/iiab_state.py (tried: {tried})")

    spec = importlib.util.spec_from_file_location("iiab_state_module", path)
    if spec is None or spec.loader is None:
        raise LoadError(f"could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _MODULE = module
    return module
