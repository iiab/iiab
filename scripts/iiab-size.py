#!/usr/bin/python3
# Auto-calculate IIAB + EduPack disk space needs, in advance [& design review]
# https://github.com/iiab/iiab/pull/3594

import os, sys, syslog
from datetime import date
import pwd, grp
import shutil
import argparse
import sqlite3
import iiab.iiab_lib as iiab
import iiab.adm_lib as adm
import requests
import json
import importlib
from functools import reduce
iiab_item_size = importlib.import_module("iiab-item-size")

def main():
    parser = argparse.ArgumentParser(description="Read menu file for get size.")
    parser.add_argument("menuFile", help="Is the menu file.")
    # menu_dir
    args =  parser.parse_args()

    menu_file = args.menuFile
    if not os.path.exists(menu_file):
        print('Menu file ' + menu_file + ' not found.')
        exit(1)

    total_size= content_from_menu(menu_file)

    print('total: ',iiab.human_readable(total_size))
    print(f'total (bytes): ', total_size)

    sys.exit()

def content_from_menu(menu_file):
    menu = adm.read_json(menu_file)
    items = iiab_item_size.get_items_size(menu["menu_items_1"])
    total_size = reduce(lambda accumulator,item: accumulator+int(item['size']), items, 0)    
    return total_size

# Now start the application
if __name__ == "__main__":
    main()
