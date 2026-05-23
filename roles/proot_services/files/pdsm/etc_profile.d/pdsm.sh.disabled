# Auto-start psm services on login (proot)

# Limit to interactive shells
case $- in
    *i*) ;;
    *)  return ;;
esac

PDSM_BIN="/usr/local/bin/pdsm"
PDSM_DIR="/usr/local/pdsm"
ENABL="$PDSM_DIR/services-enabled"
PDSM_LOG="/tmp/pdsm-startup.log"

if [ -d "$ENABL" ]; then
  for svc in "$ENABL"/*; do
    [ -x "$svc" ] || continue
    "$svc" start >>"$PDSM_LOG" 2>&1
  done
fi

# Initial session status check.
[ -f "$PDSM_BIN" ] ; "$PDSM_BIN" status
