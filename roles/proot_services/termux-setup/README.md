# termux-setup modules

This project is maintained as multiple Bash "modules" that are bundled into a single script:
`0_termux-setup_v2.sh` (the file served for: `curl ... | bash`).

## Rules

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

## Rebuild:

```
cd termux-setup
bash build_bundle.sh
```
