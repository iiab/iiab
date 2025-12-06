#!/usr/bin/env bash
#
# Copyright (C) 2025  Luis Guzman  <ark@switnet.org>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# Simple installer for PDSM tree
# Must be run as root (or via sudo)

set -e

# Helpers

log() {
    # Simple logger
    echo "[pdsm] $*"
}

# Sanity checks

if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
    echo "This installer must be run as root (try: sudo $0)" >&2
    exit 1
fi

# Queries script directory and set source directories
SCRIPT_PATH="${BASH_SOURCE[0]}"
SCRIPT_DIR="$(cd -- "$(dirname -- "$SCRIPT_PATH")" && pwd)"
SRC_ETC_PROFILE_D="${SCRIPT_DIR}/etc_profile.d"
SRC_USR_LOCAL_BIN="${SCRIPT_DIR}/usr_local_bin"
SRC_USR_LOCAL_PDSM="${SCRIPT_DIR}/usr_local_pdsm"

# Prevents failure from running on wrong path.
EXPECTED_DIR="/opt/iiab/iiab/roles/proot_services/files/pdsm"

if [ "${SCRIPT_DIR}" = "${EXPECTED_DIR}" ]; then
    if [[ ! -d "${SRC_ETC_PROFILE_D}" || \
          ! -d "${SRC_USR_LOCAL_BIN}" || \
          ! -d "${SRC_USR_LOCAL_PDSM}" ]]; then
        log "ERROR: Running from ${EXPECTED_DIR}, but required subdirectories"
        log "       etc_profile.d, usr_local_bin and usr_local_pdsm are missing."
        exit 1
    fi
    log "Using canonical installer location: ${SCRIPT_DIR}"
else
    if [[ ! -d "${SRC_ETC_PROFILE_D}" || \
          ! -d "${SRC_USR_LOCAL_BIN}" || \
          ! -d "${SRC_USR_LOCAL_PDSM}" ]]; then
        log "ERROR: This installer must be run either from:"
        log "         ${EXPECTED_DIR}"
        log "       or from a directory containing required subdirectories:"
        log "         ./etc_profile.d  ./usr_local_bin  ./usr_local_pdsm"
        log "       Current directory: ${SCRIPT_DIR}"
        exit 1
    fi
    log "Non-standard installer location, but required tree is present: ${SCRIPT_DIR}"
fi


# Destination paths

DEST_PROFILE_D="/etc/profile.d"
DEST_BIN="/usr/local/bin"
DEST_PDSM="/usr/local/pdsm"
DEST_PDSM_LIB="${DEST_PDSM}/lib"
DEST_PDSM_SAVAIL="${DEST_PDSM}/services-available"
DEST_PDSM_SENABLED="${DEST_PDSM}/services-enabled"

# Create directories

log "Ensuring local directories exist..."

## /usr/local/pdsm tree
install -d -m 0755 "${DEST_PDSM}"
install -d -m 0755 "${DEST_PDSM_LIB}"
install -d -m 0755 "${DEST_PDSM_SAVAIL}"
install -d -m 0755 "${DEST_PDSM_SENABLED}"


log "Proceding to install / update scripts to the latest available."
echo "> Please note that custom changes will be overwritten <"

# Install profile.d script

if [ -f "${SRC_ETC_PROFILE_D}/pdsm.sh" ]; then
    if [ ! -f "${DEST_PROFILE_D}/pdsm.sh" ]; then
        log "Installing profile script to ${DEST_PROFILE_D}/pdsm.sh"
    else
        log "Updating profile script to latest version."
    fi
    install -m 0644 "${SRC_ETC_PROFILE_D}/pdsm.sh" "${DEST_PROFILE_D}/pdsm.sh"
else
    log "Warning: No profile file exists, nothing installed."
fi

# Install /usr/local/bin/pdsm

if [ -f "${SRC_ETC_PROFILE_D}/pdsm.sh" ]; then
    if [ ! -f "${DEST_BIN}/pdsm" ]; then
        log "Installing binary to ${DEST_BIN}/pdsm"
    else
        log "Updating binary to ${DEST_BIN}/pdsm"
    fi
    install -m 0755 "${SRC_USR_LOCAL_BIN}/pdsm" "${DEST_BIN}/pdsm"
else
    log "Warning: No bin script exists, nothing installed."
fi

# Install /usr/local/pdsm/lib/pdsm-common.sh

if [ -f "${SRC_USR_LOCAL_PDSM}/lib/pdsm-common.sh" ]; then
    if [ ! -f "${DEST_PDSM_LIB}/pdsm-common.sh" ]; then
        log "Installing common library to ${DEST_PDSM_LIB}/pdsm-common.sh"
    else
        log "Updating common library to ${DEST_PDSM_LIB}/pdsm-common.sh"
    fi
    install -m 0644 \
        "${SRC_USR_LOCAL_PDSM}/lib/pdsm-common.sh" \
        "${DEST_PDSM_LIB}/pdsm-common.sh"
else
    log "Warning: No lib file exists, nothing installed."
fi

# Install services-available
    log "Installing services-available to ${DEST_PDSM_SAVAIL}/"
for srv in $(find "${SRC_USR_LOCAL_PDSM}"/services-available -type f);
do
  service="$(echo $srv|xargs basename)"
  if [ ! -f "$srv" ]; then
      echo "  > Installing $service service to ${DEST_PDSM_SAVAIL}/$service"
  else
      echo "  > Updating $service service to ${DEST_PDSM_SAVAIL}/$service"
  fi
    install -m 0755 "$srv" "${DEST_PDSM_SAVAIL}"/
done

log " - PDSM installation/update complete. - "
