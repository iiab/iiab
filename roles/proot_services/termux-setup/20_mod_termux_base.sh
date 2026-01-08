# shellcheck shell=bash
# Module file (no shebang). Bundled by build_bundle.sh

# If baseline fails, store the last command that failed for better diagnostics.
BASELINE_ERR=""

baseline_prereqs_ok() {
  have proot-distro && have adb && have termux-notification && have termux-dialog && have sha256sum
}

baseline_missing_prereqs() {
  # Print missing prerequisites, one per line.
  local missing=()
  have proot-distro        || missing+=("proot-distro")
  have adb                 || missing+=("adb")
  have termux-notification || missing+=("termux-notification")
  have termux-dialog       || missing+=("termux-dialog")
  have sha256sum           || missing+=("sha256sum (coreutils)")

  # Print as lines (caller can join if desired)
  printf '%s\n' "${missing[@]}"
}

baseline_bail_details() {
  warn "Baseline package installation failed (network / repo unreachable or packages missing)."
  [[ -n "${BASELINE_ERR:-}" ]] && warn "Last failing command: ${BASELINE_ERR}"
  local miss=()
  mapfile -t miss < <(baseline_missing_prereqs || true)
  ((${#miss[@]})) && warn "Missing prerequisites: ${miss[*]}"
  warn "Not stamping; rerun later when prerequisites are available."
}

# Termux apt options (avoid conffile prompts)
TERMUX_APT_OPTS=( "-y" "-o" "Dpkg::Options::=--force-confdef" "-o" "Dpkg::Options::=--force-confold" )
termux_apt() { apt-get "${TERMUX_APT_OPTS[@]}" "$@"; }

# -------------------------
# Android info
# -------------------------
get_android_sdk()     { getprop ro.build.version.sdk 2>/dev/null || true; }
get_android_release() { getprop ro.build.version.release 2>/dev/null || true; }
ANDROID_SDK="$(get_android_sdk)"
ANDROID_REL="$(get_android_release)"

# -------------------------
# Wakelock (Termux:API)
# -------------------------
WAKELOCK_HELD=0
acquire_wakelock() {
  if have termux-wake-lock; then
    if termux-wake-lock; then
      WAKELOCK_HELD=1
      ok "Wakelock acquired (termux-wake-lock)."
    else
      warn "Failed to acquire wakelock (termux-wake-lock)."
    fi
  else
    warn "termux-wake-lock not available. Install: pkg install termux-api + Termux:API app."
  fi
}
release_wakelock() {
  if [[ "$WAKELOCK_HELD" -eq 1 ]] && have termux-wake-unlock; then
    termux-wake-unlock || true
    ok "Wakelock released (termux-wake-unlock)."
  fi
}

# -------------------------
# One-time repo selector
# -------------------------
step_termux_repo_select_once() {
  local stamp="$STATE_DIR/stamp.termux_repo_selected"
  [[ -f "$stamp" ]] && return 0
  if ! have termux-change-repo; then
    warn "termux-change-repo not found; skipping mirror selection."
    return 0
  fi

  if [[ -r /dev/tty ]]; then
    printf "\n${YEL}[iiab] One-time setup:${RST} Select a nearby Termux repository mirror for faster downloads.\n" >&2
    local ans="Y"
    printf "[iiab] Launch termux-change-repo now? [Y/n]: " > /dev/tty
    if ! read -r ans < /dev/tty; then
      warn "No interactive TTY available; skipping mirror selection (run 'termux-change-repo' directly to be prompted)."
      return 0
    fi
    ans="${ans:-Y}"
    if [[ "$ans" =~ ^[Yy]$ ]]; then
      # Logging redirects stdout/stderr to pipes, which can break the UI.
      # Run it using /dev/tty and the original console fds (3/4).
      if [[ -r /dev/tty ]]; then
        termux-change-repo </dev/tty >&3 2>&4 || true
      else
        termux-change-repo || true
      fi
      ok "Mirror selection completed (or skipped inside the UI)."
    else
      warn "Mirror selection skipped by user."
    fi
    date > "$stamp"
    return 0
  fi

  warn "No /dev/tty available; skipping mirror selection."
  return 0
}

# -------------------------
# Baseline packages
# -------------------------
step_termux_base() {
  local stamp="$STATE_DIR/stamp.termux_base"

  BASELINE_OK=0

  # Even if we have a stamp, validate that core commands still exist.
  if [[ -f "$stamp" ]]; then
    if baseline_prereqs_ok; then
      BASELINE_OK=1
      ok "Termux baseline already prepared (stamp found)."
      return 0
    fi
    warn "Baseline stamp found but prerequisites are missing; forcing reinstall."
    rm -f "$stamp"
  fi

  log "Updating Termux packages (noninteractive) and installing baseline dependencies..."
  export DEBIAN_FRONTEND=noninteractive

  if ! termux_apt update; then
    BASELINE_ERR="termux_apt update"
    baseline_bail_details
    return 1
  fi

  if ! termux_apt upgrade; then
    BASELINE_ERR="termux_apt upgrade"
    baseline_bail_details
    return 1
  fi

  if ! termux_apt install \
    ca-certificates \
    curl \
    coreutils \
    grep \
    sed \
    gawk \
    openssh \
    proot proot-distro \
    android-tools \
    termux-api
  then
    BASELINE_ERR="termux_apt install (baseline deps)"
    baseline_bail_details
    return 1
  fi

  if baseline_prereqs_ok; then
    BASELINE_OK=1
    ok "Termux baseline ready."
    date > "$stamp"
    return 0
  fi

  BASELINE_ERR="post-install check (commands missing after install)"
  baseline_bail_details
  return 1
}
