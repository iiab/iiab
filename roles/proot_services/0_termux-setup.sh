#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

# IIAB on Android - Termux bootstrap (standalone)
#
# Requirements:
#  - Termux installed
#  - Network connectivity
#  - Shizuku + rish (Android 12/13 only) to raise Phantom Process Killer (PPK) limit
#
# Default behavior (idempotent):
# - One-time Termux repo mirror selection (prompted once; no TTY checks)
# - Acquire wakelock when possible (Termux:API)
# - Prepare Termux baseline packages (noninteractive, avoids dpkg conffile prompts)
# - Ensure proot-distro + Debian exists (install by default)
# - Last step: On Android 12/13 only, re-apply PPK fix via rish (if available)
# - Self-check summary at the end
#
# Flags:
# - --ppk-only              Run only PPK fix + self-check
# - --reset-debian          Reset (reinstall) Debian (clean environment), then proceed normally
# - --cleanup-rish-export   After installing rish into PATH, delete ~/rish and ~/rish*.dex (off by default)

RED="\033[31m"
YEL="\033[33m"
GRN="\033[32m"
BLU="\033[34m"
RST="\033[0m"
BOLD="\033[1m"

log()      { printf "${BLU}[iiab]${RST} %s\n" "$*"; }
ok()       { printf "${GRN}[iiab]${RST} %s\n" "$*"; }
warn()     { printf "${YEL}[iiab] WARNING:${RST} %s\n" "$*" >&2; }
warn_red() { printf "${RED}${BOLD}[iiab] WARNING:${RST} %s\n" "$*" >&2; }

have() { command -v "$1" >/dev/null 2>&1; }

STATE_DIR="${HOME}/.iiab-android"
mkdir -p "$STATE_DIR"

PPK_ONLY=0
RESET_DEBIAN=0
CLEANUP_RISH_EXPORT=0

for arg in "$@"; do
  case "$arg" in
    --ppk-only) PPK_ONLY=1 ;;
    --reset-debian|--clean-debian) RESET_DEBIAN=1 ;;
    --cleanup-rish-export) CLEANUP_RISH_EXPORT=1 ;;
    -h|--help)
      cat <<'EOF'
Usage:
  ./0_termux-setup.sh
      Default run (idempotent): Termux baseline + Debian bootstrap + PPK fix (Android 12/13) + self-check

  ./0_termux-setup.sh --ppk-only
      Run ONLY the last step: PPK fix (Android 12/13) + self-check

  ./0_termux-setup.sh --reset-debian
      Reset (reinstall) Debian in proot-distro (clean environment), then proceed normally

  ./0_termux-setup.sh --cleanup-rish-export
      After installing rish into PATH, delete ~/rish and ~/rish*.dex (off by default)

Notes:
  - This script will NOT delete rish exports unless --cleanup-rish-export is used.
  - PPK fix is re-applied to 256 on every run (Android 12/13) when possible.
  - Repo selection is prompted once (skipped for --ppk-only).
EOF
      exit 0
      ;;
  esac
done

get_android_sdk()     { getprop ro.build.version.sdk 2>/dev/null || true; }
get_android_release() { getprop ro.build.version.release 2>/dev/null || true; }

ANDROID_SDK="$(get_android_sdk)"
ANDROID_REL="$(get_android_release)"

# Avoid dpkg conffile prompts (Termux layer)
TERMUX_APT_OPTS=(
  "-y"
  "-o" "Dpkg::Options::=--force-confdef"
  "-o" "Dpkg::Options::=--force-confold"
)
termux_apt() { apt-get "${TERMUX_APT_OPTS[@]}" "$@"; }

# -------------------------
# Wakelock (Termux:API)
# -------------------------
WAKELOCK_HELD=0

acquire_wakelock() {
  # This helps prevent the device from sleeping during long installs.
  if have termux-wake-lock; then
    termux-wake-lock || true
    WAKELOCK_HELD=1
    ok "Wakelock acquired (termux-wake-lock)."
  else
    warn "termux-wake-lock not available. (Install Termux:API: pkg install termux-api + Termux:API app.)"
  fi
}

release_wakelock() {
  if [[ "$WAKELOCK_HELD" -eq 1 ]] && have termux-wake-unlock; then
    termux-wake-unlock || true
    ok "Wakelock released (termux-wake-unlock)."
  fi
}

trap 'release_wakelock' EXIT

# -------------------------
# Step 0: One-time repo selector (no TTY checks)
# -------------------------
step_termux_repo_select_once() {
  local stamp="$STATE_DIR/stamp.termux_repo_selected"
  if [[ -f "$stamp" ]]; then
    return 0
  fi

  if ! have termux-change-repo; then
    warn "termux-change-repo not found; skipping mirror selection."
    return 0
  fi

  # When running via "curl | bash", stdin is not a TTY.
  # Try to prompt via /dev/tty if available. If not, skip WITHOUT stamping.
  if [[ -r /dev/tty ]]; then
    printf "\n${YEL}[iiab] One-time setup:${RST} Select a nearby Termux repository mirror for faster downloads.\n" >&2

    local ans="Y"
    if ! read -r -p "[iiab] Launch termux-change-repo now? [Y/n]: " ans < /dev/tty; then
      warn "No interactive TTY available; skipping mirror selection (run the script directly to be prompted)."
      return 0
    fi

    ans="${ans:-Y}"
    if [[ "$ans" =~ ^[Yy]$ ]]; then
      termux-change-repo || true
      ok "Mirror selection completed (or skipped inside the UI)."
    else
      warn "Mirror selection skipped by user."
    fi

    date > "$stamp"
    return 0
  fi

  warn "No /dev/tty available; skipping mirror selection (run the script directly to be prompted)."
  return 0
}

# -------------------------
# Step 1: Termux baseline packages (idempotent)
# -------------------------
step_termux_base() {
  local stamp="$STATE_DIR/stamp.termux_base"
  if [[ -f "$stamp" ]]; then
    ok "Termux baseline already prepared (stamp found)."
    return 0
  fi

  log "Updating Termux packages (noninteractive) and installing baseline dependencies..."
  export DEBIAN_FRONTEND=noninteractive

  termux_apt update || true
  termux_apt upgrade || true

  termux_apt install \
    curl \
    ca-certificates \
    coreutils \
    grep \
    sed \
    openssh \
    proot \
    proot-distro || true

  ok "Termux baseline ready."
  date > "$stamp"
}

# -------------------------
# Debian helpers (robust)
# -------------------------
debian_exists() {
  have proot-distro || return 1
  proot-distro login debian -- true >/dev/null 2>&1
}

ensure_proot_distro() {
  if have proot-distro; then
    return 0
  fi
  warn "proot-distro is not available. Attempting to install it..."
  termux_apt install proot-distro || true
  have proot-distro
}

proot_install_debian_safe() {
  local out rc
  set +e
  out="$(proot-distro install debian 2>&1)"
  rc=$?
  set -e

  if [[ $rc -eq 0 ]]; then
    return 0
  fi
  if echo "$out" | grep -qi "already installed"; then
    warn "Debian is already installed; continuing."
    return 0
  fi

  printf "%s\n" "$out" >&2
  return $rc
}

# -------------------------
# Step 2: Ensure Debian exists (default), optionally reset it
# -------------------------
step_debian_bootstrap_default() {
  if ! ensure_proot_distro; then
    warn "Unable to ensure proot-distro. Skipping Debian bootstrap."
    return 0
  fi

  if [[ "$RESET_DEBIAN" -eq 1 ]]; then
    warn "Reset requested: reinstalling Debian (clean environment)..."
    # Prefer reset (if available), fallback to remove+install
    if proot-distro help 2>/dev/null | grep -qE '\breset\b'; then
      proot-distro reset debian
    else
      if debian_exists; then proot-distro remove debian; fi
      proot_install_debian_safe
    fi
  else
    if debian_exists; then
      ok "Debian already present in proot-distro. Not reinstalling."
    else
      log "Installing Debian (proot-distro install debian)..."
      proot_install_debian_safe
    fi
  fi

  log "Installing minimal tools inside Debian (noninteractive)..."
  proot-distro login debian -- bash -lc '
    set -e
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -y
    apt-get -y \
      -o Dpkg::Options::=--force-confdef \
      -o Dpkg::Options::=--force-confold \
      install ca-certificates curl coreutils
  ' || true

  ok "Debian bootstrap complete."
}

# -------------------------
# rish helpers
# -------------------------
android_major_12_to_13() {
  case "${ANDROID_SDK:-}" in
    31|32) echo "12" ;;  # Android 12 / 12L
    33)    echo "13" ;;  # Android 13
    *)     echo "" ;;
  esac
}

rish_export_available_in_home() {
  [[ -f "$HOME/rish" ]] && ls -1 "$HOME"/rish*.dex >/dev/null 2>&1
}

install_rish_to_path_if_available() {
  if ! rish_export_available_in_home; then
    return 1
  fi

  local dex PREFIX_BIN
  dex="$(ls -1 "$HOME"/rish*.dex 2>/dev/null | head -n1 || true)"
  PREFIX_BIN="/data/data/com.termux/files/usr/bin"

  install -m 0755 "$HOME/rish" "$PREFIX_BIN/rish"
  install -m 0644 "$dex" "$PREFIX_BIN/$(basename "$dex")"
  # Typical adjustment required by rish
  sed -i 's/PKG/com.termux/g' "$PREFIX_BIN/rish" || true

  if [[ "$CLEANUP_RISH_EXPORT" -eq 1 ]]; then
    warn "Cleanup requested: removing rish exports from HOME (~/rish, ~/rish*.dex)."
    rm -f "$HOME/rish" "$HOME"/rish*.dex || true
  fi
  return 0
}

run_rish() {
  local out
  out="$(rish -c "$1" 2>&1)" || {
    printf "%s\n" "$out"
    return 1
  }
  printf "%s\n" "$out"
  return 0
}

# -------------------------
# LAST STEP: Android 12/13 PPK fix via rish
# -------------------------
step_ppk_fix_android_12_13() {
  local major rel sdk
  major="$(android_major_12_to_13)"
  rel="${ANDROID_REL:-?}"
  sdk="${ANDROID_SDK:-?}"

  if [[ -z "$major" ]]; then
    ok "Android release=$rel sdk=$sdk -> PPK fix not applicable (only Android 12/13)."
    return 0
  fi

  log "Android $major (release=$rel sdk=$sdk) -> PPK fix target: max_phantom_processes=256"

  if ! have rish; then
    install_rish_to_path_if_available || true
  fi

  if ! have rish; then
    warn_red "PPK fix could not be applied: rish is not available."
    warn_red "Start Shizuku, then export 'rish' and the matching .dex into Termux (SAF)."
    warn_red "Continuing without changing PPK."
    return 0
  fi

  log "Current phantom setting:"
  local cur
  cur="$(run_rish "dumpsys activity settings | grep -i phantom || true" || true)"
  if echo "$cur" | grep -qi "Server is not running"; then
    warn_red "Shizuku/rish server is not running (or not authorized)."
    warn_red "Open Shizuku -> start the service -> authorize rish, then re-run:"
    warn_red "  ./0_termux-setup.sh --ppk-only"
    return 0
  fi
  printf "%s\n" "$cur"

  local target=256
  log "Applying: device_config put activity_manager max_phantom_processes $target"
  local apply
  apply="$(run_rish "device_config put activity_manager max_phantom_processes $target" || true)"
  if echo "$apply" | grep -qi "Server is not running"; then
    warn_red "Shizuku/rish server is not running (or not authorized)."
    warn_red "Open Shizuku -> start the service -> authorize rish, then re-run:"
    warn_red "  ./0_termux-setup.sh --ppk-only"
    return 0
  fi

  log "Final phantom setting:"
  run_rish "dumpsys activity settings | grep -i phantom || true" || true

  ok "PPK fix applied (or re-applied)."
}

# -------------------------
# Self-check summary
# -------------------------
self_check() {
  local rel sdk major
  rel="${ANDROID_REL:-?}"
  sdk="${ANDROID_SDK:-?}"
  major="$(android_major_12_to_13)"

  log "Self-check summary:"
  log "  Android release=$rel sdk=$sdk"

  if have proot-distro; then
    log "  proot-distro: present"
    log "  proot-distro list:"
    proot-distro list 2>/dev/null | sed 's/^/    /' || true
    if debian_exists; then
      ok "  Debian: present"
    else
      warn "  Debian: not present"
    fi
  else
    warn "  proot-distro: not present"
  fi

  if rish_export_available_in_home; then
    ok "  rish export: present in HOME (~/rish, ~/rish*.dex)"
  else
    warn "  rish export: not found in HOME"
  fi

  if have rish; then
    ok "  rish: installed in PATH"
    log "  rish -c id:"
    run_rish "id" | sed 's/^/    /' || true
    if [[ -n "$major" ]]; then
      log "  phantom setting (via rish):"
      run_rish "dumpsys activity settings | grep -i phantom || true" | sed 's/^/    /' || true
    fi
  else
    warn "  rish: not installed in PATH"
  fi
}

# -------------------------
# Main
# -------------------------
main() {
  acquire_wakelock
  step_termux_repo_select_once
  step_termux_base

  if [[ "$PPK_ONLY" -eq 1 ]]; then
    step_ppk_fix_android_12_13
    self_check
    ok "Done (--ppk-only)."
    exit 0
  fi

  step_debian_bootstrap_default

  # IMPORTANT: keep this last so users can re-run it quickly.
  step_ppk_fix_android_12_13

  self_check

  ok "0_termux-setup.sh completed."
  log "Tip: re-run only the PPK fix: ./0_termux-setup.sh --ppk-only"
  log "Tip: clean Debian environment: ./0_termux-setup.sh --reset-debian"
  ok "You can proceed with: proot-distro login debian"
}

main "$@"
