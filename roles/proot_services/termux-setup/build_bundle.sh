#!/usr/bin/env bash
set -euo pipefail

# build_bundle.sh
# Bundles modules listed in manifest.sh into ../0_termux-setup.sh

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$SCRIPT_DIR"

MANIFEST="${ROOT_DIR}/manifest.sh"
[[ -f "$MANIFEST" ]] || { echo "[!] Missing manifest.sh at: $MANIFEST" >&2; exit 1; }

# Modules live next to build_bundle.sh (same dir)
MOD_DIR="$ROOT_DIR"

PARENT_DIR="$(cd -- "${ROOT_DIR}/.." && pwd)"
OUT_DIR="${ROOT_DIR}/dist"
OUT_FILE="${PARENT_DIR}/0_termux-setup.sh"
TMP_FILE="${OUT_DIR}/.0_termux-setup.tmp.$RANDOM$RANDOM"

mkdir -p "$OUT_DIR"
build_ts="$(date -Is)"

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
cat  << EOF > "$TMP_FILE"
#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

# -----------------------------------------------------------------------------
# GENERATED FILE: ${build_ts} - do not edit directly.
# Source modules: termux-setup/*.sh + manifest.sh
# Rebuild: (cd termux-setup && bash build_bundle.sh)
# -----------------------------------------------------------------------------

EOF

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
chmod 700 "$TMP_FILE"
mv -f -- "$TMP_FILE" "$OUT_FILE"
chmod 700 "$OUT_FILE"

echo "[ok] Wrote: $OUT_FILE"
