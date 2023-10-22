#!/bin/bash

# K. KA Lite prep
if [ -d /library/ka-lite ]; then
    echo -e "\n\nKA LITE REQUIRES 2 THINGS...\n"

    echo -e "Register with KA Lite - just the anonymous registration...\n"
    # /usr/bin/kalite venv wrapper invokes 'export KALITE_HOME=/library/ka-lite'
    if [ ! -f $FLAGDIR/kalite-zone-complete ]; then
        echo -e "Now running 'kalite manage generate_zone' ...\n"
        kalite manage generate_zone || true    # Overrides 'set -e'
        touch $FLAGDIR/kalite-zone-complete
    else
        echo -e "'kalite manage generate_zone' IS ALREADY COMPLETE -- per existence of:"
        echo -e "$FLAGDIR/kalite-zone-complete\n"
    fi

    echo -e "\nInstall KA Lite's mandatory 0.9 GB English Pack... (en.zip)\n"
    if [ ! -f $FLAGDIR/kalite-en.zip-complete ]; then
        #echo -e 'Now retrieving it...\n'
        cd /tmp
        if [ -f en.zip ]; then
            if [ $(wc -c < en.zip) -ne 929916955 ]; then
                echo -e "\nERROR: /tmp/en.zip must be 929,916,955 bytes to proceed.\n" >&2
                exit 1
            else
                echo -e "\nUsing existing /tmp/en.zip whose 929,916,955 byte size is correct!\n"
            fi
        else
            wget http://pantry.learningequality.org/downloads/ka-lite/0.17/content/contentpacks/en.zip
        fi
        echo -e 'Now installing /tmp/en.zip into /library/ka-lite/content/*\n'
        kalite manage retrievecontentpack local en en.zip
        touch $FLAGDIR/kalite-en.zip-complete
    fi
fi
# WARNING: /tmp/en.zip (and all stuff in /tmp) is auto-deleted during reboots
# NEW WAY ABOVE - since 2018-07-03 - installs KA Lite's mandatory English Pack
#
# kalite manage retrievecontentpack download en
# OLD WAY ABOVE - fails w/ sev ISPs per https://github.com/iiab/iiab/issues/871
