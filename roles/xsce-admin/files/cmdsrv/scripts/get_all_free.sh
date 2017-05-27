#!/bin/bash

parted -m <<EOF
print all free
quit
EOF
