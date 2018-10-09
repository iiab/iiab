#!/usr/bin/env python3

'''
This script checks every role in the project and prints its name to stdout if 
the role directory does not contain a README file.

For ease of use, you can pipe the output of this script to a file or to a 
clipboard utility (e.g. pbcopy on macOS, xclip on Linux).
'''

import os, glob

for role in sorted(os.listdir("roles")):
    readme_glob = os.path.join("roles", role, "README.*")
    if not glob.glob(readme_glob):
        print(role)
