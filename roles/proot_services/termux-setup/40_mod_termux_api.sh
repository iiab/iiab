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

normalize_port_5digits() {
  # Accept either "12345" or strings that contain "...:12345" (e.g. "192.168.1.10:12345").
  # We extract the last ':' segment (if any), strip non-digits, and require exactly 5 digits.
  local raw="$1"
  raw="${raw//[[:space:]]/}"

  local tail="$raw"
  if [[ "$raw" == *:* ]]; then
    tail="${raw##*:}"
  fi

  # Strip any non-digits (handles cases like "IP:12345)" or "Port:12345")
  tail="${tail//[^0-9]/}"
  [[ "$tail" =~ ^[0-9]{5}$ ]] || return 1
  printf '%s' "$tail"
}

ask_port_5digits() {
  # args: key title
  local key="$1" title="$2" v="" p=""
  while true; do
    v="$(notify_ask_one "$key" "$title" "(5 digits PORT or IP:PORT)")" || return 1
    p="$(normalize_port_5digits "$v")" || continue
    echo "$p"
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
