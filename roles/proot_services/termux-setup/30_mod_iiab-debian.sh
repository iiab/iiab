# shellcheck shell=bash
# Module file (no shebang). Bundled by build_bundle.sh

# -------------------------
# IIAB Debian bootstrap
# -------------------------
iiab_exists() {
  have proot-distro || return 1
  proot-distro login iiab -- true >/dev/null 2>&1
}

ensure_proot_distro() {
  if have proot-distro; then return 0; fi
  warn "proot-distro not found; attempting to install..."
  termux_apt install proot-distro || true
  have proot-distro
}

proot_install_iiab_safe() {
  local out rc
  set +e
  if ! proot-distro install --help 2>/dev/null | grep -q -- '--override-alias'; then
    warn_red "proot-distro is too old (missing --override-alias). Please upgrade Termux packages and retry."
    return 1
  fi
  out="$(proot-distro install --override-alias iiab debian 2>&1)"
  rc=$?
  set -e
  if [[ $rc -eq 0 ]]; then return 0; fi
  if echo "$out" | grep -qi "already installed"; then
    warn "IIAB Debian is already installed; continuing."
    return 0
  fi
  printf "%s\n" "$out" >&2
  return $rc
}

step_iiab_bootstrap_default() {
  if ! ensure_proot_distro; then
    warn "Unable to ensure proot-distro; skipping IIAB Debian bootstrap."
    return 0
  fi

  if [[ "$RESET_IIAB" -eq 1 ]]; then
    warn "Reset requested: reinstalling IIAB Debian (clean environment)..."
    if proot-distro help 2>/dev/null | grep -qE '\breset\b'; then
      proot-distro reset iiab || true
      # If reset was requested but iiab wasn't installed yet (or reset failed), ensure it's present.
      iiab_exists || proot_install_iiab_safe || true
    else
      if iiab_exists; then proot-distro remove iiab || true; fi
      proot_install_iiab_safe || true
    fi
  else
    if iiab_exists; then
      ok "IIAB Debian already present in proot-distro. Not reinstalling."
    else
      log "Installing IIAB Debian (proot-distro install --override-alias iiab debian)..."
      proot_install_iiab_safe || true
    fi
  fi

  log "Installing minimal tools inside IIAB Debian (noninteractive)..."
  if ! iiab_exists; then
    warn_red "IIAB Debian is not available in proot-distro (install may have failed). Rerun later."
    return 0
  fi
  local rc=0
  set +e
  proot-distro login iiab -- bash -lc '
    set -e
    export DEBIAN_FRONTEND=noninteractive
    apt-get update
    apt-get -y -o Dpkg::Options::=--force-confdef -o Dpkg::Options::=--force-confold \
      install ca-certificates coreutils curl e2fsprogs sudo
  '
  rc=$?
  set -e
  if [[ $rc -eq 0 ]]; then
    ok "IIAB Debian bootstrap complete."
  else
    warn_red "IIAB Debian bootstrap incomplete (inner apt-get failed, rc=$rc)."
    warn "You can retry later with: proot-distro login iiab"
  fi
}
