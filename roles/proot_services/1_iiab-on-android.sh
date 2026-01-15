#!/usr/bin/env bash
# This is a convenient script to test the current Android IIAB implementation
# it requires that you install termux, once on it install proot-distro.

# PRoot-Distro allows to install multiple OSes, we use Debian then login.

# See more details at:
# - https://github.com/iiab/iiab/blob/master/vars/local_vars_android.yml

set -euo pipefail

#-----------------------------
# Safety checks
#-----------------------------
if [ "$(id -u)" != "0" ]; then
    echo "This script should be run as root, which is the default in proot-distro"
    echo "Careful, maybe this script is not been executed on the right terminal?"
    exit 1
fi

#-----------------------------
# Config
#-----------------------------
LOCAL_VARS_URL="https://raw.githubusercontent.com/iiab/iiab/refs/heads/master/vars/local_vars_android.yml"

INSTALL_PRIMARY="https://iiab.io/install.txt"
INSTALL_FALLBACK="https://raw.githubusercontent.com/iiab/iiab-factory/refs/heads/master/install.txt"

CURL="curl -fsSL --retry 5 --retry-connrefused --retry-delay 2"

#-----------------------------
# Update package db + deps
#-----------------------------
apt-get update
apt-get install -y ca-certificates \
                   coreutils \
                   curl \
                   e2fsprogs \
                   sudo

#-----------------------------
# Setup Android-specific local vars
#-----------------------------
if [ ! -d /etc/iiab ]; then
    mkdir -p /etc/iiab
fi

tmp_vars="$(mktemp)"
$CURL "$LOCAL_VARS_URL" -o "$tmp_vars"
install -m 0644 "$tmp_vars" /etc/iiab/local_vars.yml
rm -f "$tmp_vars"

#-----------------------------
# Fetch install.txt with fallback and run it
#-----------------------------
tmp_install="$(mktemp)"

if $CURL "$INSTALL_PRIMARY" -o "$tmp_install"; then
  :
else
  echo "Warning: failed to fetch $INSTALL_PRIMARY"
  echo "Falling back to $INSTALL_FALLBACK"
  $CURL "$INSTALL_FALLBACK" -o "$tmp_install"
fi

bash "$tmp_install"
rm -f "$tmp_install"
