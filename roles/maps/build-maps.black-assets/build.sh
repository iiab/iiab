#!/bin/bash

# Make sure we're in the right directory
SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
cd $SCRIPT_DIR

set -euo pipefail

curl -fsSL https://deb.nodesource.com/setup_24.x | sudo bash - &&\
sudo apt install -y nodejs

git clone https://github.com/iiab/maps.black
cd maps.black
git checkout 3b329af9448a13c25c179425bb9e818488b990ba
cd client

npm ci
npm run prebuild
npm run build-http
