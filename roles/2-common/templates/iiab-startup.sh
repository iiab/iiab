#!/bin/bash
# put initialization that needs to happen at every startup for IIAB here

if [ ! -f /etc/iiab/uuid ]; then
   uuidgen > /etc/iiab/uuid
fi
exit 0

