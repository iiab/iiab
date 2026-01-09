#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

# -----------------------------------------------------------------------------
# GENERATED FILE: 2026-01-08T19:20:20-05:00 - do not edit directly.
# Source modules: termux-setup/*.sh + manifest.sh
# Rebuild: (cd termux-setup && bash build_bundle.sh)
# -----------------------------------------------------------------------------


# ---- BEGIN 00_lib_common.sh ----
# shellcheck shell=bash
# Module file (no shebang). Bundled by build_bundle.sh

RED="\033[31m"; YEL="\033[33m"; GRN="\033[32m"; BLU="\033[34m"; RST="\033[0m"; BOLD="\033[1m"

log()      { printf "${BLU}[iiab]${RST} %s\n" "$*"; }
ok()       { printf "${GRN}[iiab]${RST} %s\n" "$*"; }
warn()     { printf "${YEL}[iiab] WARNING:${RST} %s\n" "$*" >&2; }
warn_red() { printf "${RED}${BOLD}[iiab] WARNING:${RST} %s\n" "$*" >&2; }
indent()   { sed 's/^/ /'; }

have() { command -v "$1" >/dev/null 2>&1; }
need() { have "$1" || return 1; }
die()  { echo "[!] $*" >&2; exit 1; }

# -------------------------
# Global defaults (may be overridden via environment)
# -------------------------
STATE_DIR="${STATE_DIR:-${HOME}/.iiab-android}"
ADB_STATE_DIR="${ADB_STATE_DIR:-${STATE_DIR}/adbw_pair}"
LOG_DIR="${LOG_DIR:-${STATE_DIR}/logs}"

HOST="${HOST:-127.0.0.1}"
CONNECT_PORT="${CONNECT_PORT:-}"
TIMEOUT_SECS="${TIMEOUT_SECS:-180}"

# Defaults used by ADB flows / logging / misc
CLEANUP_OFFLINE="${CLEANUP_OFFLINE:-1}"
DEBUG="${DEBUG:-0}"

# ---- END 00_lib_common.sh ----


# ---- BEGIN 10_mod_logging.sh ----
# shellcheck shell=bash
# Module file (no shebang). Bundled by build_bundle.sh

# -------------------------
# Logging
# -------------------------
LOG_ENABLED=1
LOG_FILE=""          # if empty, auto-generate under $LOG_DIR
LOG_KEEP=3           # keep only the last 3 logs

prune_old_logs() {
  [[ -d "${LOG_DIR:-}" ]] || return 0
  local keep="${LOG_KEEP:-3}"
  local i=0 f
  while IFS= read -r f; do
    [[ -n "${f:-}" ]] || continue
    i=$((i + 1))
    (( i <= keep )) && continue
    rm -f -- "$f" 2>/dev/null || true
  done < <(ls -1t "$LOG_DIR"/*.log 2>/dev/null || true)
}

setup_logging() {
  # Save original console fds so interactive tools still work after we redirect stdout/stderr.
  exec 3>&1 4>&2

  # If logging is disabled, still allow --debug to trace to console.
  if [[ "${LOG_ENABLED:-1}" -ne 1 ]]; then
    if [[ "${DEBUG:-0}" -eq 1 ]]; then
      set -x
      ok "Debug trace enabled (bash -x) -> console (logging disabled)"
    fi
    return 0
  fi

  mkdir -p "$LOG_DIR"

  if [[ -z "${LOG_FILE:-}" ]]; then
    LOG_FILE="${LOG_DIR}/0_termux-setupv2.$(date +%Y%m%d-%H%M%S).log"
  else
    mkdir -p "$(dirname -- "$LOG_FILE")"
  fi

  # Header (best-effort)
  local started
  started="$(date -Is 2>/dev/null || date 2>/dev/null || echo "?")"
  {
    echo "=== iiab termux setup v2 log ==="
    echo "Started: $started"
    echo "Script: $0"
    echo "Args: ${*:-}"
    echo "Android SDK=${ANDROID_SDK:-?} Release=${ANDROID_REL:-?}"
    echo "PWD: $(pwd 2>/dev/null || true)"
    echo "================================"
  } >>"$LOG_FILE" 2>/dev/null || true

  chmod 600 "$LOG_FILE"

  prune_old_logs

  # Duplicate stdout/stderr to console + log (strip ANSI in log)
  exec \
    > >(tee >(sed -E 's/\x1B\[[0-9;]*[ -/]*[@-~]//g' >>"$LOG_FILE")) \
    2> >(tee >(sed -E 's/\x1B\[[0-9;]*[ -/]*[@-~]//g' >>"$LOG_FILE") >&2)

  ok "Logging to: $LOG_FILE"

  # If --debug, send xtrace only to log
  if [[ "${DEBUG:-0}" -eq 1 ]]; then
    exec 9>>"$LOG_FILE"
    export BASH_XTRACEFD=9
    export PS4='+(${BASH_SOURCE}:${LINENO}): ${FUNCNAME[0]:+${FUNCNAME[0]}(): }'
    set -x
    ok "Debug trace enabled (bash -x) -> log only"
  fi
}

# ---- END 10_mod_logging.sh ----


# ---- BEGIN 20_mod_termux_base.sh ----
# shellcheck shell=bash
# Module file (no shebang). Bundled by build_bundle.sh

# If baseline fails, store the last command that failed for better diagnostics.
BASELINE_ERR=""

baseline_prereqs_ok() {
  have proot-distro && have adb && have termux-notification && have termux-dialog && have sha256sum
}

baseline_missing_prereqs() {
  # Print missing prerequisites, one per line.
  local missing=()
  have proot-distro        || missing+=("proot-distro")
  have adb                 || missing+=("adb")
  have termux-notification || missing+=("termux-notification")
  have termux-dialog       || missing+=("termux-dialog")
  have sha256sum           || missing+=("sha256sum (coreutils)")

  # Print as lines (caller can join if desired)
  printf '%s\n' "${missing[@]}"
}

baseline_bail_details() {
  warn "Baseline package installation failed (network / repo unreachable or packages missing)."
  [[ -n "${BASELINE_ERR:-}" ]] && warn "Last failing command: ${BASELINE_ERR}"
  local miss=()
  mapfile -t miss < <(baseline_missing_prereqs || true)
  ((${#miss[@]})) && warn "Missing prerequisites: ${miss[*]}"
  warn "Not stamping; rerun later when prerequisites are available."
}

# Termux apt options (avoid conffile prompts)
TERMUX_APT_OPTS=( "-y" "-o" "Dpkg::Options::=--force-confdef" "-o" "Dpkg::Options::=--force-confold" )
termux_apt() { apt-get "${TERMUX_APT_OPTS[@]}" "$@"; }

# -------------------------
# Android info
# -------------------------
get_android_sdk()     { getprop ro.build.version.sdk 2>/dev/null || true; }
get_android_release() { getprop ro.build.version.release 2>/dev/null || true; }
ANDROID_SDK="$(get_android_sdk)"
ANDROID_REL="$(get_android_release)"

# -------------------------
# Wakelock (Termux:API)
# -------------------------
WAKELOCK_HELD=0
acquire_wakelock() {
  if have termux-wake-lock; then
    if termux-wake-lock; then
      WAKELOCK_HELD=1
      ok "Wakelock acquired (termux-wake-lock)."
    else
      warn "Failed to acquire wakelock (termux-wake-lock)."
    fi
  else
    warn "termux-wake-lock not available. Install: pkg install termux-api + Termux:API app."
  fi
}
release_wakelock() {
  if [[ "$WAKELOCK_HELD" -eq 1 ]] && have termux-wake-unlock; then
    termux-wake-unlock || true
    ok "Wakelock released (termux-wake-unlock)."
  fi
}

# -------------------------
# One-time repo selector
# -------------------------
step_termux_repo_select_once() {
  local stamp="$STATE_DIR/stamp.termux_repo_selected"
  [[ -f "$stamp" ]] && return 0
  if ! have termux-change-repo; then
    warn "termux-change-repo not found; skipping mirror selection."
    return 0
  fi

  if [[ -r /dev/tty ]]; then
    printf "\n${YEL}[iiab] One-time setup:${RST} Select a nearby Termux repository mirror for faster downloads.\n" >&2
    local ans="Y"
    printf "[iiab] Launch termux-change-repo now? [Y/n]: " > /dev/tty
    if ! read -r ans < /dev/tty; then
      warn "No interactive TTY available; skipping mirror selection (run 'termux-change-repo' directly to be prompted)."
      return 0
    fi
    ans="${ans:-Y}"
    if [[ "$ans" =~ ^[Yy]$ ]]; then
      # Logging redirects stdout/stderr to pipes, which can break the UI.
      # Run it using /dev/tty and the original console fds (3/4).
      if [[ -r /dev/tty ]]; then
        termux-change-repo </dev/tty >&3 2>&4 || true
      else
        termux-change-repo || true
      fi
      ok "Mirror selection completed (or skipped inside the UI)."
    else
      warn "Mirror selection skipped by user."
    fi
    date > "$stamp"
    return 0
  fi

  warn "No /dev/tty available; skipping mirror selection."
  return 0
}

# -------------------------
# Baseline packages
# -------------------------
step_termux_base() {
  local stamp="$STATE_DIR/stamp.termux_base"

  BASELINE_OK=0

  # Even if we have a stamp, validate that core commands still exist.
  if [[ -f "$stamp" ]]; then
    if baseline_prereqs_ok; then
      BASELINE_OK=1
      ok "Termux baseline already prepared (stamp found)."
      return 0
    fi
    warn "Baseline stamp found but prerequisites are missing; forcing reinstall."
    rm -f "$stamp"
  fi

  log "Updating Termux packages (noninteractive) and installing baseline dependencies..."
  export DEBIAN_FRONTEND=noninteractive

  if ! termux_apt update; then
    BASELINE_ERR="termux_apt update"
    baseline_bail_details
    return 1
  fi

  if ! termux_apt upgrade; then
    BASELINE_ERR="termux_apt upgrade"
    baseline_bail_details
    return 1
  fi

  if ! termux_apt install \
    ca-certificates \
    curl \
    coreutils \
    grep \
    sed \
    gawk \
    openssh \
    proot proot-distro \
    android-tools \
    termux-api
  then
    BASELINE_ERR="termux_apt install (baseline deps)"
    baseline_bail_details
    return 1
  fi

  if baseline_prereqs_ok; then
    BASELINE_OK=1
    ok "Termux baseline ready."
    date > "$stamp"
    return 0
  fi

  BASELINE_ERR="post-install check (commands missing after install)"
  baseline_bail_details
  return 1
}

# ---- END 20_mod_termux_base.sh ----


# ---- BEGIN 30_mod_debian.sh ----
# shellcheck shell=bash
# Module file (no shebang). Bundled by build_bundle.sh

# -------------------------
# Debian bootstrap
# -------------------------
debian_exists() {
  have proot-distro || return 1
  proot-distro login debian -- true >/dev/null 2>&1
}

ensure_proot_distro() {
  if have proot-distro; then return 0; fi
  warn "proot-distro not found; attempting to install..."
  termux_apt install proot-distro || true
  have proot-distro
}

proot_install_debian_safe() {
  local out rc
  set +e
  out="$(proot-distro install debian 2>&1)"
  rc=$?
  set -e
  if [[ $rc -eq 0 ]]; then return 0; fi
  if echo "$out" | grep -qi "already installed"; then
    warn "Debian is already installed; continuing."
    return 0
  fi
  printf "%s\n" "$out" >&2
  return $rc
}

step_debian_bootstrap_default() {
  if ! ensure_proot_distro; then
    warn "Unable to ensure proot-distro; skipping Debian bootstrap."
    return 0
  fi

  if [[ "$RESET_DEBIAN" -eq 1 ]]; then
    warn "Reset requested: reinstalling Debian (clean environment)..."
    if proot-distro help 2>/dev/null | grep -qE '\breset\b'; then
      proot-distro reset debian || true
    else
      if debian_exists; then proot-distro remove debian || true; fi
      proot_install_debian_safe || true
    fi
  else
    if debian_exists; then
      ok "Debian already present in proot-distro. Not reinstalling."
    else
      log "Installing Debian (proot-distro install debian)..."
      proot_install_debian_safe || true
    fi
  fi

  log "Installing minimal tools inside Debian (noninteractive)..."
  if ! debian_exists; then
    warn_red "Debian is not available in proot-distro (install may have failed). Rerun later."
    return 0
  fi
  local rc=0
  set +e
  proot-distro login debian -- bash -lc '
    set -e
    # Fix for Android/Termux DNS issues (missing resolv.conf)
    echo "nameserver 8.8.8.8" > /etc/resolv.conf

    export DEBIAN_FRONTEND=noninteractive
    apt-get update
    apt-get -y -o Dpkg::Options::=--force-confdef -o Dpkg::Options::=--force-confold \
      install ca-certificates curl coreutils
  '
  rc=$?
  set -e
  if [[ $rc -eq 0 ]]; then
    ok "Debian bootstrap complete."
  else
    warn_red "Debian bootstrap incomplete (inner apt-get failed, rc=$rc)."
    warn "You can retry later with: proot-distro login debian"
  fi
}

# ---- END 30_mod_debian.sh ----


# ---- BEGIN 40_mod_termux_api.sh ----
# shellcheck shell=bash
# Module file (no shebang). Bundled by build_bundle.sh

# -------------------------
# Termux:API notifications + prompts
# -------------------------
NOTIF_BASE_ID=9400
NOTIF_SEQ=0
LAST_NOTIF_ID=""

# Termux:API sanity check (notifications)
termux_api_ready() {
  have termux-notification || return 1

  # Quick probe: some setups fail until Termux:API app is installed/allowed.
  local msg="iiab test notification"
  if ! termux-notification --id "$NOTIF_BASE_ID" --title "iiab" --content "$msg" --priority max --sound >/dev/null 2>&1; then
    return 1
  fi
  if have termux-notification-remove; then
    termux-notification-remove "$NOTIF_BASE_ID" >/dev/null 2>&1 || true
  fi
  return 0
}

sanitize_timeout() {
  # Ensure TIMEOUT_SECS is a positive integer
  if ! [[ "${TIMEOUT_SECS:-}" =~ ^[0-9]+$ ]]; then
    warn "Invalid --timeout='${TIMEOUT_SECS:-}'. Falling back to 180."
    TIMEOUT_SECS=180
  elif (( TIMEOUT_SECS < 5 )); then
    warn "Very low --timeout=${TIMEOUT_SECS}. Forcing minimum 5 seconds."
    TIMEOUT_SECS=5
  fi
}

cleanup_notif() {
  have termux-notification-remove || return 0
  termux-notification-remove "$NOTIF_BASE_ID" >/dev/null 2>&1 || true
  if [[ -n "${LAST_NOTIF_ID:-}" ]]; then
    termux-notification-remove "$LAST_NOTIF_ID" >/dev/null 2>&1 || true
  fi
}

notify_ask_one() {
  # args: key title content
  local key="$1" title="$2" content="$3"
  local out="$ADB_STATE_DIR/$key.reply"
  rm -f "$out"

  # Fresh notification each time + sound (use a new ID so Android plays sound each time)
  local nid
  nid=$((NOTIF_BASE_ID + 1 + NOTIF_SEQ))
  NOTIF_SEQ=$((NOTIF_SEQ + 1))
  LAST_NOTIF_ID="$nid"

  if have termux-notification-remove; then
    termux-notification-remove "$nid" >/dev/null 2>&1 || true
  fi

  # Direct reply: Termux:API injects the user input into $REPLY for the action.
  # Write it to a known file, then the main loop reads it.
  local action
  action="sh -lc 'umask 077; printf \"%s\" \"\$REPLY\" > \"${out}\"'"

  termux-notification \
    --id "$nid" \
    --ongoing \
    --priority max \
    --title "$title" \
    --content "$content" \
    --sound \
    --button1 "Answer" \
    --button1-action "$action" \
    || return 1

  local start now reply
  start="$(date +%s)"

  while true; do
    if [[ -f "$out" ]]; then
      reply="$(tr -d '\r\n' < "$out" 2>/dev/null || true)"
      rm -f "$out" >/dev/null 2>&1 || true
      if have termux-notification-remove; then
        termux-notification-remove "$nid" >/dev/null 2>&1 || true
      fi
      printf '%s' "$reply"
      return 0
    fi

    now="$(date +%s)"
    if (( now - start >= TIMEOUT_SECS )); then
      if have termux-notification-remove; then
        termux-notification-remove "$nid" >/dev/null 2>&1 || true
      fi
      return 1
    fi
    sleep 1
  done
}

ask_port_5digits() {
  # args: key title
  local key="$1" title="$2" v=""
  while true; do
    v="$(notify_ask_one "$key" "$title" "(5 digits)")" || return 1
    v="${v//[[:space:]]/}"
    [[ "$v" =~ ^[0-9]{5}$ ]] || continue
    echo "$v"
    return 0
  done
}

ask_code_6digits() {
  local v=""
  while true; do
    v="$(notify_ask_one code "PAIR CODE" "(6 digits)")" || return 1
    v="${v//[[:space:]]/}"
    [[ -n "$v" ]] || continue
    [[ "$v" =~ ^[0-9]+$ ]] || continue
    # Normalize to 6 digits (allow missing leading zeros)
    if ((${#v} < 6)); then
      v="$(printf "%06d" "$v")"
    fi
    [[ "$v" =~ ^[0-9]{6}$ ]] || continue
    echo "$v"
    return 0
  done
}

# ---- END 40_mod_termux_api.sh ----


# ---- BEGIN 50_mod_adb.sh ----
# shellcheck shell=bash
# Module file (no shebang). Bundled by build_bundle.sh

# -------------------------
# ADB wireless pair/connect wizard
# -------------------------

# Local stamp so we can detect "connect-only" misuse after reinstall/clear-data.
ADB_PAIRED_STAMP="${ADB_STATE_DIR}/stamp.adb_paired"

adb_hostkey_fingerprint() {
  # Returns a stable fingerprint for THIS Termux install's adb host key.
  # Defaulted to sha256 being available/confirmed in the baseline.
  local pub="${HOME}/.android/adbkey.pub"
  [[ -r "$pub" ]] || return 1
  sha256sum "$pub" | awk '{print $1}'
}

adb_stamp_write() {
  # args: mode serial
  local mode="$1" serial="$2" fp=""
  fp="$(adb_hostkey_fingerprint 2>/dev/null || true)"
  {
    echo "ts=$(date -Is 2>/dev/null || date || true)"
    echo "mode=${mode}"
    echo "host=${HOST}"
    echo "serial=${serial}"
    echo "connect_port=${CONNECT_PORT:-}"
    echo "hostkey_fp=${fp}"
  } >"$ADB_PAIRED_STAMP" 2>/dev/null || true
  chmod 600 "$ADB_PAIRED_STAMP"
}

adb_stamp_read_fp() {
  [[ -r "$ADB_PAIRED_STAMP" ]] || return 1
  sed -n 's/^hostkey_fp=//p' "$ADB_PAIRED_STAMP" 2>/dev/null | head -n 1
}

adb_warn_connect_only_if_suspicious() {
  # Called only in connect-only flows.
  local cur_fp old_fp
  cur_fp="$(adb_hostkey_fingerprint 2>/dev/null || true)"
  old_fp="$(adb_stamp_read_fp 2>/dev/null || true)"

  if [[ ! -f "$ADB_PAIRED_STAMP" ]]; then
    warn "connect-only assumes THIS Termux install has been paired before."
    warn "No local pairing stamp found ($ADB_PAIRED_STAMP)."
    warn "If you reinstalled Termux / cleared data / changed user, you must re-pair (run: --adb-only)."
    [[ -n "$cur_fp" ]] && warn "Current ADB hostkey fingerprint: ${cur_fp:0:12}..."
    return 0
  fi

  if [[ -n "$old_fp" && -n "$cur_fp" && "$old_fp" != "$cur_fp" ]]; then
    warn_red "ADB host key changed since last pairing stamp."
    warn "Old fingerprint: ${old_fp:0:12}...  Current: ${cur_fp:0:12}..."
    warn "Android Wireless debugging -> Paired devices: remove the old entry, then run: --adb-only"
  fi
}

adb_connect_verify() {
  # args: serial (HOST:PORT)
  local serial="$1" out rc start now state
  set +e
  out="$(adb connect "$serial" 2>&1)"
  rc=$?
  set -e

  # Always verify via `adb devices` (adb may exit 0 even on failure).
  start="$(date +%s)"
  while true; do
    state="$(adb_device_state "$serial" || true)"
    [[ "$state" == "device" ]] && { printf '%s\n' "$out"; return 0; }
    now="$(date +%s)"
    (( now - start >= 5 )) && break
    sleep 1
  done

  warn_red "adb connect did not result in a usable device entry for: $serial (state='${state:-none}')."
  warn "adb connect output: ${out:-<none>}"
  warn "If you recently reinstalled Termux/cleared data, the phone may show an OLD paired device. Remove it and re-pair."
  return 1
}

cleanup_offline_loopback() {
  local keep_serial="$1"  # e.g. 127.0.0.1:41313
  local serial state rest
  while read -r serial state rest; do
    [[ -n "${serial:-}" ]] || continue
    [[ "$serial" == ${HOST}:* ]] || continue
    [[ "$state" == "offline" ]] || continue
    [[ "$serial" == "$keep_serial" ]] && continue
    adb disconnect "$serial" >/dev/null 2>&1 || true
  done < <(adb devices 2>/dev/null | tail -n +2 | sed '/^[[:space:]]*$/d')
}

adb_pair_connect() {
  need adb || die "Missing adb. Install: pkg install android-tools"

  # Only require Termux:API when we will prompt the user
  if [[ "$ONLY_CONNECT" != "1" || -z "${CONNECT_PORT:-}" ]]; then
    termux_api_ready || die "Termux:API not ready."
  fi

  echo "[*] adb: $(adb version | head -n 1)"
  adb start-server >/dev/null 2>&1 || true

  if [[ "$ONLY_CONNECT" == "1" ]]; then
    adb_warn_connect_only_if_suspicious
    if [[ -n "$CONNECT_PORT" ]]; then
      CONNECT_PORT="${CONNECT_PORT//[[:space:]]/}"
      [[ "$CONNECT_PORT" =~ ^[0-9]{5}$ ]] || die "Invalid CONNECT PORT (must be 5 digits): '$CONNECT_PORT'"
    else
      echo "[*] Asking CONNECT PORT..."
      CONNECT_PORT="$(ask_port_5digits connect "CONNECT PORT")" || die "Timeout waiting CONNECT PORT."
    fi

    local serial="${HOST}:${CONNECT_PORT}"
    adb disconnect "$serial" >/dev/null 2>&1 || true
    echo "[*] adb connect $serial"
    adb_connect_verify "$serial" >/dev/null || die "adb connect failed to $serial. Verify Wireless debugging is enabled, and pairing exists for THIS Termux install."

    if [[ "$CLEANUP_OFFLINE" == "1" ]]; then
      cleanup_offline_loopback "$serial"
    fi

    echo "[*] Devices:"
    adb devices -l

    echo "[*] ADB check (shell):"
    adb -s "$serial" shell sh -lc 'echo "it worked: adb shell is working"; id' || true
    adb_stamp_write "connect-only" "$serial"

    cleanup_notif
    ok "ADB connected (connect-only): $serial"
    return 0
  fi

  if [[ -n "$CONNECT_PORT" ]]; then
    CONNECT_PORT="${CONNECT_PORT//[[:space:]]/}"
    [[ "$CONNECT_PORT" =~ ^[0-9]{5}$ ]] || die "Invalid --connect-port (must be 5 digits): '$CONNECT_PORT'"
  else
    echo "[*] Asking CONNECT PORT..."
    CONNECT_PORT="$(ask_port_5digits connect "CONNECT PORT")" || die "Timeout waiting CONNECT PORT."
  fi

  echo "[*] Asking PAIR PORT..."
  local pair_port
  pair_port="$(ask_port_5digits pair "PAIR PORT")" || die "Timeout waiting PAIR PORT."

  echo "[*] Asking PAIR CODE..."
  local code
  code="$(ask_code_6digits)" || die "Timeout waiting PAIR CODE."

  local serial="${HOST}:${CONNECT_PORT}"
  adb disconnect "$serial" >/dev/null 2>&1 || true

  echo "[*] adb pair ${HOST}:${pair_port}"
  printf '%s\n' "$code" | adb pair "${HOST}:${pair_port}" || die "adb pair failed. Verify PAIR PORT and PAIR CODE (and that the pairing dialog is showing)."

  echo "[*] adb connect $serial"
  adb_connect_verify "$serial" >/dev/null || die "adb connect failed after pairing. Re-check CONNECT PORT and Wireless debugging."

  if [[ "$CLEANUP_OFFLINE" == "1" ]]; then
    cleanup_offline_loopback "$serial"
  fi

  echo "[*] Devices:"
  adb devices -l

  echo "[*] ADB check (shell):"
  adb -s "$serial" shell sh -lc 'echo "it worked: adb shell is working"; getprop ro.product.model; getprop ro.build.version.release' || true
  adb_stamp_write "paired" "$serial"

  cleanup_notif
  ok "ADB connected: $serial"
}

# Return state for an exact serial (e.g. "device", "offline", empty)
adb_device_state() {
  local s="$1"
  adb devices 2>/dev/null | awk -v s="$s" 'NR>1 && $1==s {print $2; exit}'
}

# Return first loopback serial in "device" state (e.g. 127.0.0.1:41313)
adb_any_loopback_device() {
  adb devices 2>/dev/null | awk -v h="$HOST" '
    NR>1 && $2=="device" && index($1, h":")==1 {print $1; found=1; exit}
    END { exit (found ? 0 : 1) }
  '
}

# Pick the loopback serial we will operate on:
# - If CONNECT_PORT is set, require that exact HOST:PORT to be in "device" state.
# - Otherwise, return the first loopback device.
adb_pick_loopback_serial() {
  if [[ -n "${CONNECT_PORT:-}" ]]; then
    local p="${CONNECT_PORT//[[:space:]]/}"
    [[ "$p" =~ ^[0-9]{5}$ ]] || return 1
    local target="${HOST}:${p}"
    [[ "$(adb_device_state "$target")" == "device" ]] && { echo "$target"; return 0; }
    return 1
  fi
  adb_any_loopback_device
}

# If already connected, avoid re-pairing/re-connecting prompts (useful for --all),
# BUT only consider loopback/target connections as "already connected".
adb_pair_connect_if_needed() {
  need adb || die "Missing adb. Install: pkg install android-tools"
  adb start-server >/dev/null 2>&1 || true

  local serial=""

  # If user provided a connect-port, insist on that exact target serial.
  if [[ -n "${CONNECT_PORT:-}" ]]; then
    CONNECT_PORT="${CONNECT_PORT//[[:space:]]/}"
    [[ "$CONNECT_PORT" =~ ^[0-9]{5}$ ]] || die "Invalid --connect-port (must be 5 digits): '$CONNECT_PORT'"

    local target="${HOST}:${CONNECT_PORT}"

    if [[ "$(adb_device_state "$target")" == "device" ]]; then
      ok "ADB already connected to target: $target (skipping pair/connect)."
      return 0
    fi

    # Try connect-only first (in case it was already paired before)
    adb connect "$target" >/dev/null 2>&1 || true
    if [[ "$(adb_device_state "$target")" == "device" ]]; then
      ok "ADB connected to target: $target (connect-only succeeded; skipping pair)."
      return 0
    fi

    # Not connected: run full wizard (pair+connect)
    adb_pair_connect
    return $?
  fi

  # No explicit port: only skip if we already have a loopback device connected.
  if serial="$(adb_any_loopback_device 2>/dev/null)"; then
    ok "ADB already connected (loopback): $serial (skipping pair/connect)."
    return 0
  fi

  adb_pair_connect
}

require_adb_connected() {
  need adb || { warn_red "Missing adb. Install: pkg install android-tools"; return 1; }
  adb start-server >/dev/null 2>&1 || true
  if ! adb_pick_loopback_serial >/dev/null 2>&1; then
    warn_red "No ADB device connected."
    warn "If already paired before: run --connect-only [PORT]."
    warn "Otherwise: run --adb-only to pair+connect."
    return 1
  fi
  return 0
}

adb_loopback_serial_or_die() {
  local s
  s="$(adb_pick_loopback_serial 2>/dev/null)" || return 1
  echo "$s"
}

# ---- END 50_mod_adb.sh ----


# ---- BEGIN 60_mod_ppk_checks.sh ----
# shellcheck shell=bash
# Module file (no shebang). Bundled by build_bundle.sh

# PPK / phantom-process checks and tuning via ADB (best-effort)
# Moved out of 99_main.sh to keep it as an orchestrator.

# -------------------------
# PPK / phantom-process tuning (best-effort)
# -------------------------
ppk_fix_via_adb() {
  need adb || die "Missing adb. Install: pkg install android-tools"

  local serial
  if ! serial="$(adb_pick_loopback_serial)"; then
    CHECK_NO_ADB=1
    warn "No ADB loopback device connected (expected ${HOST}:${CONNECT_PORT:-*})."
    return 1
  fi
  ok "Using ADB device: $serial"

  log "Setting PPK: max_phantom_processes=256"
# Some Android versions may ignore/rename this; we don't hard-fail.
adb -s "$serial" shell sh -s <<'EOF' || true
    set -e
    # Persist device_config changes if supported
    if command -v device_config >/dev/null 2>&1; then
      device_config set_sync_disabled_for_tests persistent >/dev/null 2>&1 || true
      device_config put activity_manager max_phantom_processes 256 || true
      echo "dumpsys effective max_phantom_processes:"
      dumpsys activity settings 2>/dev/null | grep -i "max_phantom_processes=" | head -n 1 || true
    else
      echo "device_config not found; skipping."
    fi
EOF

  ok "PPK set done (best effort)."
  return 0
}

# Prefer Android 14+ feature-flag override if present:
# OFF -> true, ON -> false
adb_get_child_restrictions_flag() {
  local serial="$1"
  adb -s "$serial" shell getprop persist.sys.fflag.override.settings_enable_monitor_phantom_procs \
    2>/dev/null | tr -d '\r' || true
}

# -------------------------
# Check readiness (best-effort)
# -------------------------
check_readiness() {
  # Reset exported check signals so final_advice() never sees stale values
  CHECK_NO_ADB=0
  CHECK_SDK=""
  CHECK_MON=""
  CHECK_PPK=""

  need adb || die "Missing adb. Install: pkg install android-tools"
  adb start-server >/dev/null 2>&1 || true

  local serial
  if ! serial="$(adb_pick_loopback_serial)"; then
    CHECK_NO_ADB=1
    # Best-effort: keep local SDK so final_advice can still warn on A12-13.
    CHECK_SDK="${ANDROID_SDK:-}"
    warn_red "No ADB device connected. Cannot run checks."
    warn "If already paired before: run --connect-only [PORT]."
    warn "Otherwise: run --adb-only to pair+connect."
    return 1
  fi

  ok "Check using ADB device: $serial"

  local dev_enabled sdk rel mon mon_fflag ds ppk_eff
  sdk="$(adb -s "$serial" shell getprop ro.build.version.sdk 2>/dev/null | tr -d '\r' || true)"
  rel="$(adb -s "$serial" shell getprop ro.build.version.release 2>/dev/null | tr -d '\r' || true)"
  dev_enabled="$(adb -s "$serial" shell settings get global development_settings_enabled 2>/dev/null | tr -d '\r' || true)"
  mon_fflag="$(adb_get_child_restrictions_flag "$serial")"
  if [[ "$mon_fflag" == "true" || "$mon_fflag" == "false" ]]; then
    mon="$mon_fflag"
  else
    mon="$(adb -s "$serial" shell settings get global settings_enable_monitor_phantom_procs 2>/dev/null | tr -d '\r' || true)"
  fi

  # Get effective value from dumpsys (device_config get may return 'null' even when an effective value exists)
  ds="$(adb -s "$serial" shell dumpsys activity settings 2>/dev/null | tr -d '\r' || true)"
  ppk_eff="$(printf '%s\n' "$ds" | awk -F= '/max_phantom_processes=/{print $2; exit}' | tr -d '[:space:]' || true)"

  # Export check signals for the final advice logic
  CHECK_SDK="${sdk:-}"
  CHECK_MON="${mon:-}"
  CHECK_PPK="${ppk_eff:-}"

  log " Android release=${rel:-?} sdk=${sdk:-?}"

  if [[ "${dev_enabled:-}" == "1" ]]; then
    ok " Developer options: enabled (development_settings_enabled=1)"
  elif [[ -n "${dev_enabled:-}" ]]; then
    warn " Developer options: unknown/disabled (development_settings_enabled=${dev_enabled})"
  else
    warn " Developer options: unreadable (permission/ROM differences)."
  fi

  # Android 14+ only: "Disable child process restrictions" proxy flag
  if [[ "${sdk:-}" =~ ^[0-9]+$ ]] && (( sdk >= 34 )); then
    if [[ "${mon:-}" == "false" ]]; then
      ok " Child restrictions: OK (monitor=false)"
    elif [[ "${mon:-}" == "true" ]]; then
      warn " Child restrictions: NOT OK (monitor=true)"
    elif [[ -n "${mon:-}" && "${mon:-}" != "null" ]]; then
      warn " Child restrictions: unknown (${mon})"
    else
      warn " Child restrictions: unreadable/absent"
    fi
  fi

  # Android 12-13 only: PPK matters (use effective value from dumpsys)
  if [[ "${sdk:-}" =~ ^[0-9]+$ ]] && (( sdk >= 31 && sdk <= 33 )); then
    if [[ "${ppk_eff:-}" =~ ^[0-9]+$ ]]; then
      if (( ppk_eff >= 256 )); then
        ok " PPK: OK (max_phantom_processes=${ppk_eff})"
      else
        warn " PPK: low (max_phantom_processes=${ppk_eff}) -> suggest: run --ppk-only"
      fi
    else
      warn " PPK: unreadable (dumpsys max_phantom_processes='${ppk_eff:-}')."
    fi
  fi

  log " dumpsys (phantom-related):"
  printf '%s\n' "$ds" | grep -i phantom || true

  if [[ "${sdk:-}" =~ ^[0-9]+$ ]] && (( sdk >= 34 )); then
    log " Note: On A14+, max_phantom_processes is informational; rely on Child restrictions."
  fi
  if [[ "${sdk:-}" =~ ^[0-9]+$ ]] && (( sdk >= 34 )) && [[ "${mon:-}" == "false" ]]; then
    log " Child restrictions OK."
  fi
  return 0
}

self_check_android_flags() {
  have adb || return 0
  adb start-server >/dev/null 2>&1 || true

  local serial sdk rel mon mon_fflag ds ppk_eff
  serial="$(adb_pick_loopback_serial 2>/dev/null)" || {
    warn "ADB: no loopback device connected. Tip: run --adb-only (pair+connect) or --check for more info."
    return 0
  }

  sdk="$(adb -s "$serial" shell getprop ro.build.version.sdk 2>/dev/null | tr -d '\r' || true)"
  rel="$(adb -s "$serial" shell getprop ro.build.version.release 2>/dev/null | tr -d '\r' || true)"
  log " Android flags (quick): release=${rel:-?} sdk=${sdk:-?} serial=$serial"

  if [[ "$sdk" =~ ^[0-9]+$ ]] && (( sdk >= 34 )); then
    mon_fflag="$(adb_get_child_restrictions_flag "$serial")"
    if [[ "$mon_fflag" == "true" || "$mon_fflag" == "false" ]]; then
      mon="$mon_fflag"
    else
      mon="$(adb -s "$serial" shell settings get global settings_enable_monitor_phantom_procs 2>/dev/null | tr -d '\r' || true)"
    fi

    if [[ "$mon" == "false" ]]; then
      ok " Child restrictions: OK (monitor=false)"
    elif [[ "$mon" == "true" ]]; then
      warn " Child restrictions: NOT OK (monitor=true) -> check Developer Options"
    else
      warn " Child restrictions: unknown/unreadable (monitor='${mon:-}')"
    fi
  fi

  if [[ "$sdk" =~ ^[0-9]+$ ]] && (( sdk >= 31 && sdk <= 33 )); then
    ds="$(adb -s "$serial" shell dumpsys activity settings 2>/dev/null | tr -d '\r' || true)"
    ppk_eff="$(printf '%s\n' "$ds" | awk -F= '/max_phantom_processes=/{print $2; exit}' | tr -d '[:space:]' || true)"

    if [[ "$ppk_eff" =~ ^[0-9]+$ ]]; then
      if (( ppk_eff >= 256 )); then
        ok " PPK: OK (max_phantom_processes=$ppk_eff)"
      else
        warn " PPK: low (max_phantom_processes=$ppk_eff) -> suggest: --ppk-only"
      fi
    else
      warn " PPK: unreadable (max_phantom_processes='${ppk_eff:-}')"
    fi
  fi

  # Avoid redundant tip when we're already in --check mode.
  if [[ "${MODE:-}" != "check" && "${MODE:-}" != "all" ]]; then
    log " Tip: run --check for full details."
  fi
}

# ---- END 60_mod_ppk_checks.sh ----


# ---- BEGIN 99_main.sh ----
# shellcheck shell=bash
# Module file (no shebang). Bundled by build_bundle.sh

# 0_termux-setupv2.sh
# - Termux bootstrap (packages, wakelock)
# - proot-distro + Debian bootstrap
# - ADB wireless pair/connect via Termux:API notifications (no Shizuku)
# - Optional PPK / phantom-process tweaks (best-effort)

# -------------------------
# Defaults
# -------------------------
# NOTE: Core defaults live in 00_lib_common.sh to guarantee availability for all modules.

# Ensure state directories exist (safe even if user overrides via environment).
mkdir -p "$STATE_DIR" "$ADB_STATE_DIR" "$LOG_DIR"

BASELINE_OK=0
BASELINE_ERR=""
RESET_DEBIAN=0
ONLY_CONNECT=0

CHECK_NO_ADB=0
CHECK_SDK=""
CHECK_MON=""
CHECK_PPK=""

# Modes are mutually exclusive (baseline is default)
MODE="baseline"      # baseline|with-adb|adb-only|connect-only|ppk-only|check|all
MODE_SET=0
CONNECT_PORT_FROM=""   # "", "flag", "positional"

usage() {
  cat <<'EOF'
Usage:
  ./0_termux-setupv2.sh
    -> Termux baseline + Debian bootstrap (idempotent). No ADB prompts.

  ./0_termux-setupv2.sh --with-adb
    -> Termux baseline + Debian bootstrap + ADB pair/connect if needed (skips if already connected).

  ./0_termux-setupv2.sh  --adb-only [--connect-port PORT]
    -> Only ADB pair/connect if needed (no Debian; skips if already connected).
       Tip: --connect-port skips the CONNECT PORT prompt (you’ll still be asked for PAIR PORT + PAIR CODE).

  ./0_termux-setupv2.sh --connect-only [CONNECT_PORT]
    -> Connect-only (no pairing). Use this after the device was already paired before.

  ./0_termux-setupv2.sh --ppk-only
    -> Set PPK only: max_phantom_processes=256 (requires ADB already connected).
       Android 14-16 usually achieve this via "Disable child process restrictions" in Developer Options.

  ./0_termux-setupv2.sh --check
    -> Check readiness: developer options flag (if readable),
       (Android 14+) "Disable child process restrictions" proxy flag, and (Android 12-13) PPK effective value.

  ./0_termux-setupv2.sh --all
    -> baseline + Debian + ADB pair/connect if needed + (Android 12-13 only) apply --ppk + run --check.

  Optional:
    --connect-port 41313    (5 digits) Skip CONNECT PORT prompt used with --adb-only
    --timeout 180           Seconds to wait per prompt
    --reset-debian          Reset (reinstall) Debian in proot-distro
    --no-log                Disable logging
    --log-file /path/file   Write logs to a specific file
    --debug                 Extra logs

Notes:
- ADB prompts require: `pkg install termux-api` + Termux:API app installed + notification permission.
- Wireless debugging must be enabled.
- This script never uses adb root.
EOF
}

trap 'cleanup_notif >/dev/null 2>&1 || true; release_wakelock >/dev/null 2>&1 || true' EXIT INT TERM

# NOTE: Termux:API prompts live in 40_mod_termux_api.sh

# -------------------------
# Self-check
# -------------------------
self_check() {
  log "Self-check summary:"
  log " Android release=${ANDROID_REL:-?} sdk=${ANDROID_SDK:-?}"

  if have proot-distro; then
    log " proot-distro: present"
    log " proot-distro list:"
    proot-distro list 2>/dev/null | indent || true
    if debian_exists; then ok " Debian: present"; else warn " Debian: not present"; fi
  else
    warn " proot-distro: not present"
  fi

  if have adb; then
    log " adb: present"
    adb devices -l 2>/dev/null | indent || true
    local serial
#    re-enable in need for verbose output.
#    if serial="$(adb_pick_loopback_serial 2>/dev/null)"; then
#      log " adb shell id (first device):"
#      adb -s "$serial" shell id 2>/dev/null | indent || true
#    fi
  else
    warn " adb: not present"
  fi
  # Quick Android flags check (best-effort; no prompts)
  self_check_android_flags || true

  if have termux-wake-lock; then ok " Termux:API wakelock: available"; else warn " Termux:API wakelock: not available"; fi
  if have termux-notification; then ok " Termux:API notifications: command present"; else warn " Termux:API notifications: missing"; fi
}

baseline_bail() {
  warn_red "Cannot continue: Termux baseline is incomplete."
  [[ -n "${BASELINE_ERR:-}" ]] && warn "Reason: ${BASELINE_ERR}"
  baseline_bail_details || true
  exit 1
}

final_advice() {
  if [[ "${BASELINE_OK:-0}" -ne 1 ]]; then
    warn_red "Baseline is not ready, so ADB prompts / Debian bootstrap may be unavailable."
    [[ -n "${BASELINE_ERR:-}" ]] && warn "Reason: ${BASELINE_ERR}"
    warn "Fix: check network + Termux repos, then re-run the script."
    return 0
  fi

  # 1) Android-related warnings (only meaningful if we attempted checks)
  local sdk="${CHECK_SDK:-${ANDROID_SDK:-}}"
  local adb_connected=0
  local serial="" mon="" mon_fflag=""

  # Best-effort: detect whether an ADB loopback device is already connected.
  # (We do NOT prompt/pair here; we only check current state.)
  if have adb; then
    adb start-server >/dev/null 2>&1 || true
    if adb_pick_loopback_serial >/dev/null 2>&1; then
      adb_connected=1
      serial="$(adb_pick_loopback_serial 2>/dev/null || true)"
    fi
  fi

  # Baseline safety gate:
  # On Android 12-13 (SDK 31-33), IIAB/proot installs can fail if PPK is low (often 32).
  # Baseline mode does NOT force ADB pairing nor run check_readiness(), so PPK may be unknown.
  # If PPK is not determined, suggest running --all BEFORE telling user to proceed to proot-distro.
  if [[ "$MODE" == "baseline" ]]; then
    if [[ "$sdk" =~ ^[0-9]+$ ]] && (( sdk >= 31 && sdk <= 33 )); then
      # If we didn't run checks, CHECK_PPK will be empty. Even with adb_connected=1, baseline
      # still doesn't populate CHECK_PPK unless user ran --check/--all.
      if [[ "${CHECK_PPK:-}" != "" && "${CHECK_PPK:-}" =~ ^[0-9]+$ ]]; then
        : # PPK determined -> ok to continue with normal advice below
      else
        warn "Android 12-13: PPK value hasn't been verified (max_phantom_processes may be low, e.g. 32)."
        warn "Before starting the IIAB install, run the complete setup so it can apply/check PPK=256; otherwise the installation may fail:"
        ok   "  ./0_termux-setupv2.sh --all"
        return 0
      fi
    elif [[ "$sdk" =~ ^[0-9]+$ ]] && (( sdk >= 34 )); then
      # On Android 14+, rely on "Disable child process restrictions"
      # Proxy signals: settings_enable_monitor_phantom_procs (or the fflag override).
      # Baseline does not run check_readiness(), so CHECK_MON is usually empty.
      if [[ "${CHECK_MON:-}" == "false" ]]; then
        : # Verified OK (rare in baseline) -> continue
      else
        # If ADB is already connected, try to read the flag best-effort (no prompts).
        if [[ "$adb_connected" -eq 1 && -n "${serial:-}" ]]; then
          mon_fflag="$(adb_get_child_restrictions_flag "$serial")"
          if [[ "$mon_fflag" == "true" || "$mon_fflag" == "false" ]]; then
            mon="$mon_fflag"
          else
            mon="$(adb -s "$serial" shell settings get global settings_enable_monitor_phantom_procs 2>/dev/null | tr -d '\r' || true)"
          fi
        fi

        if [[ "${mon:-}" == "false" ]]; then
          : # Restrictions already disabled -> ok to continue
        else
          if [[ "${mon:-}" == "true" ]]; then
            warn "Android 14+: child process restrictions appear ENABLED (monitor=true)."
          else
            warn "Android 14+: child process restrictions haven't been verified (monitor flag unreadable/unknown)."
          fi
          warn "Before starting the IIAB install, run the complete setup (--all) so it can guide you to verify such setting; otherwise the installation may fail:"
          ok   "  ./0_termux-setupv2.sh --all"
          return 0
        fi
      fi
    fi
  fi

  if [[ "${CHECK_NO_ADB:-0}" -eq 1 ]]; then
    # If we could not check, still warn on A12-13 because PPK is critical there
    if [[ "$sdk" =~ ^[0-9]+$ ]] && (( sdk >= 31 && sdk <= 33 )); then
      warn "A12-13: verify PPK=256 before installing IIAB."
    fi
  else
    # A14+ child restrictions proxy (only if readable)
    if [[ "$sdk" =~ ^[0-9]+$ ]] && (( sdk >= 34 )) && [[ "${CHECK_MON:-}" == "true" ]]; then
      warn "A14+: disable child process restrictions before installing IIAB."
    fi

    # Only warn about PPK on A12-13 (A14+ uses child restrictions)
    if [[ "$sdk" =~ ^[0-9]+$ ]] && (( sdk >= 31 && sdk <= 33 )); then
      if [[ "${CHECK_PPK:-}" =~ ^[0-9]+$ ]] && (( CHECK_PPK < 256 )); then
        warn "PPK is low (${CHECK_PPK}); consider --ppk-only."
      fi
    fi
  fi

  # 2) Debian “next step” should only be shown for modes that actually bootstrap Debian
  case "$MODE" in
    baseline|with-adb|all)
      if debian_exists; then
        ok "Next: proot-distro login debian"
      else
        warn "Debian not present. Run: proot-distro install debian"
      fi
      ;;
    *)
      # adb-only/connect-only/ppk-only/check: do not suggest Debian login as a generic ending
      ;;
  esac
}

# -------------------------
# Args
# -------------------------
set_mode() {
  local new="$1"
  if [[ "$MODE_SET" -eq 1 ]]; then
    die "Modes are mutually exclusive. Already set: --${MODE}. Tried: --${new}"
  fi
  MODE="$new"
  MODE_SET=1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --with-adb) set_mode "with-adb"; shift ;;
    --adb-only) set_mode "adb-only"; shift ;;
    --connect-only)
      set_mode "connect-only"
      ONLY_CONNECT=1
      # Optional positional port (5 digits)
      if [[ "${2:-}" =~ ^[0-9]{5}$ ]]; then
        [[ -n "${CONNECT_PORT_FROM:-}" && "${CONNECT_PORT_FROM}" != "positional" ]] && \
          die "CONNECT PORT specified twice (positional + --connect-port). Use only one."
        CONNECT_PORT="$2"
        CONNECT_PORT_FROM="positional"
        shift 2
      else
        shift
      fi
      ;;
    --ppk-only) set_mode "ppk-only"; shift ;;
    --check) set_mode "check"; shift ;;
    --all) set_mode "all"; shift ;;
    --connect-port)
      [[ -n "${CONNECT_PORT_FROM:-}" && "${CONNECT_PORT_FROM}" != "flag" ]] && \
        die "CONNECT PORT specified twice (positional + --connect-port). Use only one."
      CONNECT_PORT="${2:-}"
      CONNECT_PORT_FROM="flag"
      shift 2
      ;;
    --timeout) TIMEOUT_SECS="${2:-180}"; shift 2 ;;
    --host) HOST="${2:-127.0.0.1}"; shift 2 ;;
    --reset-debian|--clean-debian) RESET_DEBIAN=1; shift ;;
    --no-log) LOG_ENABLED=0; shift ;;
    --log-file) LOG_FILE="${2:-}"; shift 2 ;;
    --debug) DEBUG=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) shift ;;
  esac
done

validate_args() {
  if [[ -n "${CONNECT_PORT:-}" ]]; then
    CONNECT_PORT="${CONNECT_PORT//[[:space:]]/}"
    [[ "$CONNECT_PORT" =~ ^[0-9]{5}$ ]] || die "Invalid --connect-port (must be 5 digits): '$CONNECT_PORT'"
    case "$MODE" in
      adb-only|with-adb|connect-only|ppk-only|check|all) : ;;
      baseline)
        log "--connect-port requires an ADB mode."
        die "Use along with: --adb-only / --with-adb / --connect-only / --check / --ppk-only / --all"
        ;;
      *)
        die "--connect-port is not valid with mode=$MODE"
        ;;
    esac
  fi
}

# -------------------------
# Main flows
# -------------------------
main() {
  setup_logging "$@"
  validate_args
  sanitize_timeout
  acquire_wakelock

  case "$MODE" in
    baseline)
      step_termux_repo_select_once
      step_termux_base || baseline_bail
      step_debian_bootstrap_default
      ;;

    with-adb)
      step_termux_repo_select_once
      step_termux_base || baseline_bail
      step_debian_bootstrap_default
      adb_pair_connect_if_needed
      ;;

    adb-only)
      step_termux_base || baseline_bail
      adb_pair_connect_if_needed
      ;;

    connect-only)
      step_termux_base || baseline_bail
      adb_pair_connect
      ;;

    ppk-only)
      # No baseline, no Debian. Requires adb already available + connected.
      require_adb_connected || exit 1
      ppk_fix_via_adb || true
      ;;

    check)
      step_termux_base || baseline_bail
      check_readiness || true
      ;;

    all)
      step_termux_repo_select_once
      step_termux_base || baseline_bail
      step_debian_bootstrap_default
      adb_pair_connect_if_needed

      # Android 12-13 only (SDK 31-33): apply PPK tuning automatically
      if [[ "${ANDROID_SDK:-}" =~ ^[0-9]+$ ]] && (( ANDROID_SDK >= 31 && ANDROID_SDK <= 33 )); then
        log "Android SDK=${ANDROID_SDK} detected -> applying --ppk automatically (12-13 rule)."
        ppk_fix_via_adb || true
      else
        log "Android SDK=${ANDROID_SDK:-?} -> skipping auto-PPK (only for Android 12-13)."
      fi
      check_readiness || true
      ;;

    *)
      die "Unknown MODE='$MODE'"
      ;;
  esac

  self_check
  ok "0_termux-setupv2.sh completed (mode=$MODE)."
  log "---- Mode list ----"
  log "Connect-only             --connect-only [PORT]"
  log "Pair+connect             --adb-only [--connect-port PORT]"
  log "Check                    --check"
  log "Apply PPK                --ppk-only"
  log "Base+Debian+Pair+connect --with-adb"
  log "Full run                 --all"
  log "Reset Debian             --reset-debian"
  log "-------------------"
  final_advice
}

main "$@"

# ---- END 99_main.sh ----


