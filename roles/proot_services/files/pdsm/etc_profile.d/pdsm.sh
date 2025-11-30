# Auto-start psm services on login (proot)
PSM_DIR="/usr/local/pdsm"
ENABL="$PSM_DIR/services-enabled"

if [ -d "$ENABL" ]; then
  for svc in "$ENABL"/*; do
    [ -x "$svc" ] || continue
    "$svc" start
  done
fi

