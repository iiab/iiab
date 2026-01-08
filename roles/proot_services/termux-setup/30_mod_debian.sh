# shellcheck shell=bash
# Module file (no shebang). Bundled by build_bundle.sh

# -------------------------
# Debian bootstrap
# -------------------------
debian_exists() {
  have proot-distro || return 1
  proot-distro login debian -- true >/dev/null 2>&1
}

ensure_proot_distro() {
  if have proot-distro; then return 0; fi
  warn "proot-distro not found; attempting to install..."
  termux_apt install proot-distro || true
  have proot-distro
}

proot_install_debian_safe() {
  local out rc
  set +e
  out="$(proot-distro install debian 2>&1)"
  rc=$?
  set -e
  if [[ $rc -eq 0 ]]; then return 0; fi
  if echo "$out" | grep -qi "already installed"; then
    warn "Debian is already installed; continuing."
    return 0
  fi
  printf "%s\n" "$out" >&2
  return $rc
}

step_debian_bootstrap_default() {
  if ! ensure_proot_distro; then
    warn "Unable to ensure proot-distro; skipping Debian bootstrap."
    return 0
  fi

  if [[ "$RESET_DEBIAN" -eq 1 ]]; then
    warn "Reset requested: reinstalling Debian (clean environment)..."
    if proot-distro help 2>/dev/null | grep -qE '\breset\b'; then
      proot-distro reset debian || true
    else
      if debian_exists; then proot-distro remove debian || true; fi
      proot_install_debian_safe || true
    fi
  else
    if debian_exists; then
      ok "Debian already present in proot-distro. Not reinstalling."
    else
      log "Installing Debian (proot-distro install debian)..."
      proot_install_debian_safe || true
    fi
  fi

  log "Installing minimal tools inside Debian (noninteractive)..."
  if ! debian_exists; then
    warn_red "Debian is not available in proot-distro (install may have failed). Rerun later."
    return 0
  fi
  local rc=0
  set +e
  proot-distro login debian -- bash -lc '
    set -e
    # Fix for Android/Termux DNS issues (missing resolv.conf)
    echo "nameserver 8.8.8.8" > /etc/resolv.conf

    export DEBIAN_FRONTEND=noninteractive
    apt-get update
    apt-get -y -o Dpkg::Options::=--force-confdef -o Dpkg::Options::=--force-confold \
      install ca-certificates curl coreutils
  '
  rc=$?
  set -e
  if [[ $rc -eq 0 ]]; then
    ok "Debian bootstrap complete."
  else
    warn_red "Debian bootstrap incomplete (inner apt-get failed, rc=$rc)."
    warn "You can retry later with: proot-distro login debian"
  fi
}
