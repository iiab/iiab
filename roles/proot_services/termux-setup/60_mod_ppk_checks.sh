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
