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
