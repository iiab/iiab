#!/bin/sh
# Convenience script to bootstrap IIAB on Android environment on Termux.
# Requirements:
#  - Termux installed
#    https://github.com/termux/termux-app/releases/download/v0.118.3/termux-app_v0.118.3+github-debug_universal.apk
#    - Shizuku on Android 12 to 14
#      https://github.com/RikkaApps/Shizuku/releases/download/v13.6.0/shizuku-v13.6.0.r1086.2650830c-release.apk
#  - Network connectivity

set -e

# -----------------------------
# Config / constants
# -----------------------------

# Non-interactive APT/DPKG
export DEBIAN_FRONTEND=noninteractive

# PRoot-Distro target
PDISTRO_NAME="debian"

# URL to fetch IIAB-on-Android helper script (inside Debian PRoot)
IIAB_ANDROID_URL="https://si-n.cc/9b9922"
IIAB_ANDROID_SCRIPT="$HOME/iiab-on-android.sh"

# -----------------------------
# Helper functions
# -----------------------------

info() {
    printf '\n[INFO] %s\n' "$*"
}

# -----------------------------
# Step 1: Optional Termux repo selection
# -----------------------------
# NOTE: termux-change-repo is interactive; keep it here only if
# you are running this script manually (not fully unattended).

if command -v termux-change-repo >/dev/null 2>&1; then
    info "You may now change Termux repositories (interactive)..."
    termux-change-repo
else
    info "termux-change-repo not found, skipping repo change."
fi

# -----------------------------
# Step 2: Update Termux base system
# -----------------------------
info "Updating Termux package lists..."
apt-get update

# (Optional) full upgrade before installing packages
info "Upgrading Termux packages (keeping existing config files)..."
apt-get -y \
  -o Dpkg::Options::="--force-confdef" \
  -o Dpkg::Options::="--force-confold" \
  upgrade

# -----------------------------
# Step 3: Install Termux dependencies
# -----------------------------
info "Installing Termux packages: termux-api, termux-services, proot-distro..."

apt-get install -y \
  termux-api \
  termux-services \
  proot-distro \
  openssh

# Optional: Storage setup for remote management
# info "Enabling storage access..."
# termux-setup-storage

# Keep device awake while running services
if command -v termux-wake-lock >/dev/null 2>&1; then
    info "Enabling wake-lock via termux-api..."
    termux-wake-lock
else
    info "termux-wake-lock not available; is termux-api installed correctly?"
fi

info "Don't forget to enable sshd service via termux-services on the next session..."
info "  sv-enable sshd"

# -----------------------------
# Step 4: Install Debian via PRoot-Distro
# -----------------------------
info "Installing PRoot-Distro image: $PDISTRO_NAME ..."
proot-distro install "$PDISTRO_NAME"

# -----------------------------
# Step 5: Bootstrap Debian environment (curl + IIAB helper)
# -----------------------------
info "Bootstrapping Debian inside PRoot-Distro..."

proot-distro login "$PDISTRO_NAME" -- /bin/bash <<'EOF'
set -e
export DEBIAN_FRONTEND=noninteractive

echo "[DEBIAN] Updating APT lists..."
apt-get update

echo "[DEBIAN] Installing dependencies curl..."
apt-get install -y curl sudo

echo "[DEBIAN] Fetching IIAB-on-Android helper script..."
IIAB_ANDROID_URL="https://si-n.cc/9b9922"
IIAB_ANDROID_SCRIPT="$HOME/iiab-on-android.sh"

curl -sL "$IIAB_ANDROID_URL" > "$IIAB_ANDROID_SCRIPT"
chmod +x "$IIAB_ANDROID_SCRIPT"

echo "[DEBIAN] Done. You can now run: $IIAB_ANDROID_SCRIPT once at the debian environment."
EOF

info "All done. proot-distro is ready and iiab-on-android.sh can be executed within debian."
info "To continue login into debian: proot-distro login debian"
