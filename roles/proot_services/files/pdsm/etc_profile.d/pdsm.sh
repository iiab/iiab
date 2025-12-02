# Auto-start psm services on login (proot)

# Limit to interactive shells
case $- in
    *i*) ;;
    *)  return ;;
esac

PSM_DIR="/usr/local/pdsm"
ENABL="$PSM_DIR/services-enabled"
PDSM_LOCK="$PSM_DIR/.psm-services.started"

# If lock exists, no nothing.
if [ -f "$PDSM_LOCK" ]; then
    return
fi

# Create lock before starting anything.
: >"$PDSM_LOCK"

if [ -d "$ENABL" ]; then
  for svc in "$ENABL"/*; do
    [ -x "$svc" ] || continue
    "$svc" start
  done
fi

