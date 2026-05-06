#!/bin/bash

if [ -f /.iiab-image ] || [ ! -f /etc/iiab/install-flags/iiab-refreshed ]; then
    echo -e "\n\e[41;1mPlease run 'sudo iiab-freshen'!\e[0m"
fi
