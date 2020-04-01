#!/usr/bin/env python
from __future__ import print_function

import argparse
import yaml

def main():
    args = parse_args()
    comp_var_file = args.var_file

    def_vars = read_yaml('/opt/iiab/iiab/vars/default_vars.yml')
    comp_vars = read_yaml(comp_var_file)

    list_extra_vars(comp_var_file, comp_vars, def_vars)
    list_changed(comp_var_file, comp_vars, def_vars)

    #min_vars = adm.read_yaml('/opt/iiab/iiab/vars/local_vars_min.yml')
    #med_vars = adm.read_yaml('/opt/iiab/iiab/vars/local_vars_medium.yml')
    #big_vars = adm.read_yaml('/opt/iiab/iiab/vars/local_vars_big.yml')

    #list_extra_vars('min_vars', min_vars, def_vars)
    #list_extra_vars('med_vars', med_vars, def_vars)
    #list_extra_vars('big_vars', big_vars, def_vars)

    #min_vars = remove_dups('min_vars', min_vars, def_vars)
    #med_vars = remove_dups('med_vars', med_vars, def_vars)
    #big_vars = remove_dups('big_vars', big_vars, def_vars)


def list_changed(file_name, var_dict, def_vars):
    # { k : v for k,v in d.items() if v} - copy only filtered to new and return (muy pythonic)
    print('Changed in ' + file_name)
    for var_name in var_dict:
        var_val = var_dict[var_name]
        if var_val != def_vars.get(var_name):
            print(var_name + ':', var_dict[var_name])

def remove_dups(dict_name, var_dict, def_vars):
    # { k : v for k,v in d.items() if v} - copy only filtered to new and return (muy pythonic)
    for var_name in var_dict.copy():
        var_val = var_dict[var_name]
        if var_val == def_vars.get(var_name):
            del var_dict[var_name]
    print(dict_name)
    for var_name in var_dict:
        print(var_name, var_dict[var_name])
    return var_dict

def list_extra_vars(dict_name, var_dict, def_vars):
    for var_name in var_dict:
        if def_vars.get(var_name, 'ReallyNone!@#$') == 'ReallyNone!@#$':
            print(dict_name, var_name, 'not in default')

# from adm_lib

def read_yaml(file_name, loader=yaml.SafeLoader):
    try:
        with open(file_name, 'r') as f:
            y = yaml.load(f, Loader=loader)
            return y
    except:
        raise

def parse_args():
    parser = argparse.ArgumentParser(description="Compare vars file to default_vars.")
    parser.add_argument("var_file", help="the full path to the local vars file you want to compare.")
    #parser.add_argument("-z", "--zim", type=str, help="zim to update (e.g. wikipedia_en_medicine_maxi). Leave blank for All.")

    return parser.parse_args()

# Now start the application
if __name__ == "__main__":

    # Run the main routine
    main()
