#!/bin/bash

# Make sure we're in the right directory
SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
cd $SCRIPT_DIR

set -euo pipefail

curl -fsSL https://deb.nodesource.com/setup_24.x | sudo bash - &&\
sudo apt install -y nodejs

npm ci
npm run prebuild
npm run build-http
