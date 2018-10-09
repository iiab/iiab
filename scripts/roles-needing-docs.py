#!/usr/bin/env python3

'''
This script checks every role in the (Internet-in-a-Box) project and prints its
name to stdout if (1) the role directory does not contain a README file, and
(2) the role is not listed in /opt/iiab/iiab/unmaintained-roles.txt

For ease of use, you can pipe the output of this script to a file or to a 
clipboard utility (e.g. pbcopy on macOS, xclip on Linux).
'''

import os
from os.path import join as make_path
from glob import glob

def included_roles():
    all_roles = set(os.listdir("/opt/iiab/iiab/roles"))
    excluded_roles = \
        map(str.rstrip,
            open(make_path("/opt/iiab/iiab/scripts",
                           "/opt/iiab/iiab/unmaintained-roles.txt")))
    included_roles = list(all_roles.difference(excluded_roles))
    included_roles.sort()
    return included_roles

for role in included_roles():
    readme = make_path("/opt/iiab/iiab/roles", role, "README.*")
    if not glob(readme):
        print(role)
