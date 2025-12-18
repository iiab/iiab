#!/bin/bash
# This is a convenient script to test the current Android IIAB implementation
# it requires that you install termux, once on it install proot-distro.

# PRoot-Distro allows to install multiple OSes, we use Debian then login.

# See more details at:
# - https://github.com/iiab/iiab/blob/master/vars/local_vars_android.yml

set -e

#-----------------------------
# Safety checks
#-----------------------------
if [ $UID != 0 ]; then
    echo "This script should be run as root, which is the default in proot-distro"
    echo "Careful, maybe this script is not been executed on the right terminal?"
    exit 1
fi

#-----------------------------
# Config
#-----------------------------
LOCAL_VARS="https://raw.githubusercontent.com/iiab/iiab/refs/heads/master/vars/local_vars_android.yml"
PR="4122"
OWNER="iiab"
REPO="iiab"
INSTALL_URL="https://iiab.io/install.txt"
API="https://api.github.com/repos/${OWNER}/${REPO}"

# Update package db
apt-get update

# Install basic dependencies
apt-get install -y curl \
                   python3 \
                   sudo

#-----------------------------
# Setup Android-specific local vars
#-----------------------------
mkdir /etc/iiab
curl -fsSL $LOCAL_VARS > /etc/iiab/local_vars.yml

#-----------------------------
# Run complete Android build
#-----------------------------
## See more details at: https://github.com/iiab/iiab/pull/4122

## Fetch PR JSON + HTTP code (single request)
resp="$(curl -sS -H "Accept: application/vnd.github+json" \
  -w $'\n%{http_code}' "${API}/pulls/${PR}")"

body="${resp%$'\n'*}"
code="${resp##*$'\n'}"

if [[ "$code" != "200" ]]; then
  echo "GitHub API error fetching PR #${PR} (HTTP ${code})."
  echo "$body"
  exit 2
fi

state="$(python3 -c 'import sys,json; print(json.load(sys.stdin).get("state",""))' <<<"$body")"

if [[ "$state" == "open" ]]; then
  # PR still open -> install following that PR number
  curl -fsSL "$INSTALL_URL" | bash -s "$PR"
  exit 0
fi

if [[ "$state" == "closed" ]]; then
  # Distinguish merged vs closed-unmerged using the merge-check endpoint
  merge_code="$(curl -sS -o /dev/null -w '%{http_code}' \
    -H "Accept: application/vnd.github+json" "${API}/pulls/${PR}/merge" || true)"

  if [[ "$merge_code" == "204" ]]; then
    # PR merged -> normal install
    curl -fsSL "$INSTALL_URL" | bash
    exit 0
  else
    # Closed but not merged (usually 404 here)
    echo "Please verify if the changes you are trying to follow have changed from PR."
    exit 1
  fi
fi

echo "Unexpected PR state: '$state'"
exit 2
