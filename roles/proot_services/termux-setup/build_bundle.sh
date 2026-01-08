#!/usr/bin/env bash
set -euo pipefail

# build_bundle.sh
# Bundles modules listed in manifest.sh into ../0_termux-setup_v2.sh

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$SCRIPT_DIR"

MANIFEST="${ROOT_DIR}/manifest.sh"
[[ -f "$MANIFEST" ]] || { echo "[!] Missing manifest.sh at: $MANIFEST" >&2; exit 1; }

# Modules live next to build_bundle.sh (same dir)
MOD_DIR="$ROOT_DIR"

PARENT_DIR="$(cd -- "${ROOT_DIR}/.." && pwd)"
OUT_DIR="${ROOT_DIR}/dist"
OUT_FILE="${PARENT_DIR}/0_termux-setup_v2.sh"
TMP_FILE="${OUT_DIR}/.0_termux-setup_v2.tmp.$RANDOM$RANDOM"

mkdir -p "$OUT_DIR"

# Load MODULES array
# shellcheck source=/dev/null
source "$MANIFEST"

# With "set -u", don't reference an unset array directly.
if ! declare -p MODULES >/dev/null 2>&1; then
  echo "[!] manifest.sh did not define MODULES array." >&2
  exit 1
fi
if (( ${#MODULES[@]} < 1 )); then
  echo "[!] MODULES array is empty in manifest.sh." >&2
  exit 1
fi

cleanup_tmp() { rm -f -- "$TMP_FILE" 2>/dev/null || true; }
trap cleanup_tmp EXIT

# Bundle header
{
  echo '#!/data/data/com.termux/files/usr/bin/bash'
  echo 'set -euo pipefail'
  echo
  echo '# -----------------------------------------------------------------------------'
  echo '# GENERATED FILE: do not edit directly.'
  echo '# Source modules: termux-setup/*.sh + manifest.sh'
  echo '# Rebuild: (cd termux-setup && bash build_bundle.sh)'
  echo '# -----------------------------------------------------------------------------'
  echo
} >"$TMP_FILE"

# Append each module
for mod in "${MODULES[@]}"; do
  src="${MOD_DIR}/${mod}"

  if [[ ! -f "$src" ]]; then
    echo "[!] Missing module: $src" >&2
    exit 1
  fi

  # Disallow standalone scripts: modules must not have a shebang
  if head -n 1 "$src" | grep -q '^#!'; then
    echo "[!] Module must NOT include a shebang: $src" >&2
    exit 1
  fi

  {
    echo
    echo "# ---- BEGIN ${mod} ----"
    cat "$src"
    echo
    echo "# ---- END ${mod} ----"
    echo
  } >>"$TMP_FILE"
done

# Ensure final newline
printf '\n' >>"$TMP_FILE"

# Install bundle atomically
chmod 700 "$TMP_FILE" 2>/dev/null || true
mv -f -- "$TMP_FILE" "$OUT_FILE"
chmod 700 "$OUT_FILE" 2>/dev/null || true

echo "[ok] Wrote: $OUT_FILE"
