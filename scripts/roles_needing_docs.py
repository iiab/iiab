#!/usr/bin/env python3

'''
This script checks every role in the project and prints its name to stdout if 
the role directory does not contain a README file and it is not listed in 
scripts/docs_ignore.

For ease of use, you can pipe the output of this script to a file or to a 
clipboard utility (e.g. pbcopy on macOS, xclip on Linux).
'''

import os
from os.path import join as make_path
from glob import glob

def included_roles():
    all_roles = set(os.listdir("roles"))
    excluded_roles = \
        map(str.rstrip, open(make_path("scripts", "docs_ignore")))
    included_roles = list(all_roles.difference(excluded_roles))
    included_roles.sort()
    return included_roles

for role in included_roles():
    readme = make_path("roles", role, "README.*")
    if not glob(readme):
        print(role)
