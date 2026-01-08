# shellcheck shell=bash
# Module file (no shebang). Bundled by build_bundle.sh

# -------------------------
# ADB wireless pair/connect wizard
# -------------------------

# Local stamp so we can detect "connect-only" misuse after reinstall/clear-data.
ADB_PAIRED_STAMP="${ADB_STATE_DIR}/stamp.adb_paired"

adb_hostkey_fingerprint() {
  # Returns a stable fingerprint for THIS Termux install's adb host key.
  local pub="${HOME}/.android/adbkey.pub"
  [[ -r "$pub" ]] || return 1
  if have sha256sum; then
    sha256sum "$pub" | awk '{print $1}'
  elif have shasum; then
    shasum -a 256 "$pub" | awk '{print $1}'
  elif have openssl; then
    openssl dgst -sha256 "$pub" 2>/dev/null | awk '{print $2}'
  elif have md5sum; then
    md5sum "$pub" | awk '{print $1}'
  else
    return 1
  fi
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
  chmod 600 "$ADB_PAIRED_STAMP" 2>/dev/null || true
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
