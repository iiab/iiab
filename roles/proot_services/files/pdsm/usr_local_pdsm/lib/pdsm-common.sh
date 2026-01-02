#!/bin/sh
# Common helpers for PDSM services

# Base dir comes from environment (exported by pdsm), fallback to default.
PDSM_DIR="${PDSM_DIR:-/usr/local/pdsm}"
AVAIL_DIR="$PDSM_DIR/services-available"
# Define pdsm targeted php-fpm version.
PHP_FPM_VERSION=8.4
# Define a generic start time to all services.
: "${PDSM_START_TIMEOUT:=15}"

# Debug helper: only prints when PDSM_DEBUG=1
_pdsm_log() {
  [ "${PDSM_DEBUG:-0}" = 1 ] && echo "[pdsm] $*" >&2
}

require_service() {
  svc="$1"
  [ -z "$svc" ] && return 0

  _pdsm_log "require_service: svc=$svc avail_dir=$AVAIL_DIR"

  script="$AVAIL_DIR/$svc"

  if [ ! -x "$script" ]; then
    _pdsm_log "required service script not found or not executable: $script"
    return 1
  fi

  # If the service reports status=0, assume it's already running
  if "$script" status >/dev/null 2>&1; then
    _pdsm_log "$svc already running, skipping start"
    return 0
  fi

  _pdsm_log "starting required service: $svc ($script start)"
  "$script" start
}
