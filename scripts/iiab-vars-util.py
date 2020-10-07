#!/usr/bin/python3

import sys, yaml, os.path, argparse
import iiab.iiab_lib as iiab

local_vars = {}
merged_vars = {}

var_path = '/etc/iiab/'
iiab_local_vars_file = var_path + 'local_vars.yml'
default_vars_file = '/opt/iiab/iiab/vars/default_vars.yml'

check_var = sys.argv[1]
print(check_var)
merged_vars = iiab.read_yaml(default_vars_file)
local_vars = iiab.read_yaml(iiab_local_vars_file)

for key in local_vars:
    merged_vars[key] = local_vars[key]

print(merged_vars.get(check_var, None))
