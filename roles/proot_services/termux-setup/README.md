# termux-setup modules

Welcome to the termux-setup modular "suite", these scripts are intended to help the development
of the termux seupt process into a ready to install IIAB state usually.

In order to look for instructions on how to install IIAB on Android, please
use the instructions listed at this [README.md](https://github.com/iiab/iiab/tree/master/roles/proot_services).

## Development notes

This project is maintained to simplify development an splited into multiple Bash "modules" that
are bundled into a single script:

```
0_termux-setup.sh
```

### Rules

- Modules MUST NOT include a shebang (`#!...`).
- Modules SHOULD NOT run top-level code (prefer functions), except `99_main.sh`.
- Do not add `set -euo pipefail` in modules (the bundle already sets it once).
- Keep module names stable and ordered via `manifest.sh`.

Recommended header for every module:

```
# termux-setup module.
# DO NOT add a shebang or "set -euo pipefail" here.
# Keep only function/variable definitions (no top-level execution).
# See: termux-setup/README.md
```

### Rebuild:

```
cd termux-setup
bash build_bundle.sh
```
