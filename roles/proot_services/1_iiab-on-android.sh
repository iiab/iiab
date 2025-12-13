#!/bin/bash
# This is a convenient script to test the current IIAB on Android implementation.
# It assumes you are inside a Termux proot-distro Debian environment (running as root).
#
# PRoot-Distro allows you to install multiple OSes; here we use Debian and then log in.
#
# See more details at:
#   https://github.com/iiab/iiab/blob/master/vars/local_vars_android.yml

set -e

#-----------------------------
# Safety checks
#-----------------------------
if [ "$UID" -ne 0 ]; then
    echo "This script should be run as root (the default in proot-distro)."
    echo "Careful: maybe this script is not being executed in the right terminal?"
    exit 1
fi

#-----------------------------
# Config
#-----------------------------
LOCAL_VARS_URL="https://raw.githubusercontent.com/iiab/iiab/refs/heads/master/vars/local_vars_android.yml"

#-----------------------------
# Setup Android-specific local vars
#-----------------------------
mkdir -p /etc/iiab
curl -s "$LOCAL_VARS_URL" > /etc/iiab/local_vars.yml

#-----------------------------
# Run complete Android build
#-----------------------------
curl -s https://iiab.io/install.txt | bash
