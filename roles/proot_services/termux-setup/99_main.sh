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
