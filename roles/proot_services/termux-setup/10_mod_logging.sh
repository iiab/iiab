# shellcheck shell=bash
# Module file (no shebang). Bundled by build_bundle.sh

# -------------------------
# Logging
# -------------------------
LOG_ENABLED=1
LOG_FILE=""          # if empty, auto-generate under $LOG_DIR
LOG_KEEP=20          # keep last N logs

rotate_logs() {
  [[ -d "${LOG_DIR:-}" ]] || return 0
  local n=$((LOG_KEEP + 1))
  while IFS= read -r f; do
    [[ -n "${f:-}" ]] || continue
    [[ -n "${LOG_FILE:-}" && "$f" == "$LOG_FILE" ]] && continue
    rm -f -- "$f" 2>/dev/null || true
  done < <(ls -1t "$LOG_DIR"/*.log 2>/dev/null | tail -n +"$n" || true)
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

  mkdir -p "$LOG_DIR" 2>/dev/null || true

  if [[ -z "${LOG_FILE:-}" ]]; then
    LOG_FILE="${LOG_DIR}/0_termux-setupv2.$(date +%Y%m%d-%H%M%S).log"
  else
    # Best-effort: ensure parent dir exists
    mkdir -p "$(dirname -- "$LOG_FILE")" 2>/dev/null || true
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

  # Best-effort: restrict log readability (may include debug/xtrace)
  chmod 600 "$LOG_FILE" 2>/dev/null || true

  rotate_logs

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
