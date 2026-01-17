#!/bin/bash

# Make sure we're in the right directory
SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
cd $SCRIPT_DIR

set -euo pipefail

curl -fsSL https://deb.nodesource.com/setup_24.x | sudo bash - &&\
sudo apt install -y nodejs

git clone https://github.com/iiab/maps.black
cd maps.black
git checkout 1e188ffbdc4f18a5c258598d48c64fe1dbbd9c8e
cd client

npm ci
npm run prebuild
npm run build-http
