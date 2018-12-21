#!/usr/bin/python

"""

   Author: George Hunt <georgejhunt <at> gjail.com>

"""

import os, sys, syslog
import pwd, grp
import time
from datetime import date, datetime
import json
import yaml
import re
import subprocess
import shlex
import ConfigParser
import xml.etree.ElementTree as ET
import argparse
import fnmatch

IIAB_PATH='/etc/iiab'
if not IIAB_PATH in sys.path:
    sys.path.append(IIAB_PATH)
from iiab_env import get_iiab_env
KIWIX_CAT = IIAB_PATH + '/kiwix_catalog.json'

# Config Files
# iiab_ini_file should be in {{ iiab_env_file }} (/etc/iiab/iiab.env) ?
#iiab_ini_file = "{{ iiab_ini_file }}" # nominally /etc/iiab/iiab.ini
iiab_ini_file = "/etc/iiab/iiab.ini" # comment out after testing

IIAB_INI = get_iiab_env('IIAB_INI') # future
if IIAB_INI:
    iiab_ini_file = IIAB_INI

# Variables that should be read from config file
# All of these variables will be read from config files and recomputed in init()
zim_path = "/library/zims"

iiab_base_path = "/opt/iiab"
kiwix_manage = iiab_base_path + "/kiwix/bin/kiwix-manage"
doc_root = get_iiab_env('WWWROOT')
zim_version_idx_dir = doc_root + "/common/assets/"
zim_version_idx_file = "zim_version_idx.json"
#zim_version_idx_file = "zim_version_idx_test.json"
menuDefs = doc_root + "/js-menu/menu-files/menu-defs/"
menuJsonPath = doc_root + "/home/menu.json"

old_zim_map = {"bad.zim" : "unparseable name"}

# Working variables
# zim_files - list of zims and possible index from file system
# path_to_id_map - list of zims in current library.xml with id (for delete)
zim_versions = {} # map of zim's generic name to version installed, e.g. wikipedia_es_all to wikipedia_es_all_2017-01

iiab_menu_items={"calibre":"en-calibre",\
                 "calibre_web": "en-calibre-web",\
                 "cups":"en-cups",\
                 "elgg":"en-elgg",\
                 "kalite":"en-kalite",\
                 "kiwix":"en-kiwix",\
                 "kolibri":"en-kolibri",\
                 "lokole":"en-lokole",\
                 "mediawiki":"en-mediawiki",\
                 "moodle":"en-moodle",\
                 "nextcloud":"en-nextcloud",\
                 "sugarizer":"en-sugarizer",\
                 "teamviewer":"en-teamviewer",\
                 "wordpress":"en-wordpress"
}
def main():
   put_iiab_enabled_into_menu_json()
   put_kiwix_enabled_into_menu_json()
   put_oer2go_enabled_into_menu_json()


def put_iiab_enabled_into_menu_json():
   cmd = "cat " + iiab_ini_file + " | grep _enabled | cut -d_ -f1"
    #print cmd
   args = shlex.split(cmd)
   try:
      outp = subprocess.check_output(args)
   except subprocess.CalledProcessError as e:
      print(str(e))
      sys.exit(1)
   for iiab_option in outp.split('\n'):
      if iiab_option in iiab_menu_items:
         update_menu_json(iiab_menu_items[iiab_option])
         
def update_menu_json(new_item):
   with open(menuJsonPath,"r") as menu_fp:
      reads = menu_fp.read()
      #print("menu.json:%s"%reads)
      data = json.loads(reads)
      if data.get('autoupdate_menu','') == 'false' or\
         data.get('autoupdate_menu','') == 'False':
         return

      for item in data['menu_items_1']:
         if item == new_item:
            return
      # new_item does not exist in list
      last_item = data['menu_items_1'].pop()
      # always keep credits last
      if last_item.find('credits') == -1:
         data['menu_items_1'].append(last_item)
         data['menu_items_1'].append(new_item)
      else:
         data['menu_items_1'].append(new_item)
         data['menu_items_1'].append(last_item)
   with open(menuJsonPath,"w") as menu_fp:
      menu_fp.write(json.dumps(data, indent=2))

def put_kiwix_enabled_into_menu_json():
   pass

def put_oer2go_enabled_into_menu_json():
   pass

# Now start the application
if __name__ == "__main__":

    # Run the main routine
    main()
