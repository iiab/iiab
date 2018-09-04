#!/usr/bin/python

"""

   Creates temp library.xml file for kiwix from contents of /zims/content and index
   Updated to handle incremental additions and deletions

   Author: Tim Moody <tim(at)timmoody(dot)com>
   Contributors: Jerry Vonau <jvonau3(at)gmail.com>

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

IIAB_PATH='/etc/iiab'
if not IIAB_PATH in sys.path:
    sys.path.append(IIAB_PATH)
from iiab_env import get_iiab_env

# Config Files
# iiab_config_file should be in /etc/iiab/iiab.env
iiab_config_file = "{{ iiab_config_file }}" # nominally /etc/iiab/iiab.ini
# iiab_config_file = "/etc/iiab/iiab.ini" # comment out after testing

IIAB_INI = get_iiab_env('IIAB_INI') # future
if IIAB_INI:
    iiab_config_file = IIAB_INI

# Variables that should be read from config file
# All of these variables will be read from config files and recomputed in init()
zim_path = "/library/zims"

iiab_base_path = "/opt/iiab"
kiwix_manage = iiab_base_path + "/kiwix/bin/kiwix-manage"
doc_root = get_iiab_env('WWWROOT')
zim_version_idx_dir = doc_root + "/common/assets/"
zim_version_idx_file = "zim_version_idx.json"

old_zim_map = {"bad.zim" : "unparseable name"}

# Working variables
# zim_files - list of zims and possible index from file system
# path_to_array_map - list of zims in current library.xml with array index number (for delete)
zim_versions = {} # map of zim's generic name to version installed, e.g. wikipedia_es_all to wikipedia_es_all_2017-01

def main():
    """Server routine"""
    global kiwix_library_xml
    global zim_path
    global zim_version_idx_dir
    global zim_version_idx_file

    init()
    args = parse_args()
    if args.device: # allow override of path
        zim_path = args.device + zim_path
        zim_version_idx_dir = args.device + zim_version_idx_dir

    kiwix_library_xml = zim_path + "/library.xml"
    if not args.no_tmp: # don't append .tmp
        kiwix_library_xml += ".tmp"

    # remove existing file if force
    if args.force:
        try:
            os.remove(kiwix_library_xml)
        except OSError:
            pass
        zims_installed = {}
        path_to_array_map = {}
    else:
          zims_installed, path_to_array_map = read_library_xml(kiwix_library_xml)

    zim_files = get_zim_list(zim_path)

    # Remove zims not in file system from library.xml
    remove_list_str = ""
    for item in path_to_array_map:
          if item not in zim_files:
              remove_list_str += str(path_to_array_map[item]) + " "
    if remove_list_str:
        rem_libr_xml(remove_list_str)

    # Add zims from file system that are not in library.xml
    for item in zim_files:
          if item not in path_to_array_map:
              add_libr_xml(kiwix_library_xml, zim_path, item, zim_files[item])

    # Write Version Map
    if os.path.isdir(zim_version_idx_dir):
        with open(zim_version_idx_dir + zim_version_idx_file, 'w') as fp:
            json.dump(zim_versions, fp)
    else:
        print zim_version_idx_dir + " not found."
    sys.exit()

def get_zim_list(path):
    files_processed = {}
    zim_list = []
    content = path + "/content/"
    index = path + "/index/"
    flist = os.listdir(content)
    flist.sort()
    for filename in flist:
        zimpos = filename.find(".zim")
        if zimpos != -1:
            filename = filename[:zimpos]
            zimname = "content/" + filename + ".zim"
            zimidx = "index/" + filename + ".zim.idx"
            if zimname not in files_processed:
                if not os.path.isdir (path + "/" + zimidx): # only declare index if exists (could be embedded)
                    zimidx = None
                files_processed[zimname] = zimidx
                zimname = content + filename + ".zim"
                zimidx = index + filename + ".zim.idx"
                if filename in old_zim_map: # handle old names that don't parse
                    wiki_name = old_zim_map[filename]
                else:
                    ulpos = filename.rfind("_")
                    # but gutenberg don't - future maybe put in old_zim_map (en and fr, but instance dates may change)
                    if "gutenberg_" in filename:
                        ulpos = filename[:ulpos].rfind("_")
                    wiki_name = filename[:ulpos]
                zim_versions[wiki_name] = filename # if there are multiples, last should win
    return files_processed

def read_library_xml(lib_xml_file, kiwix_exclude_attr=[""]): # duplicated from iiab-cmdsrv
    kiwix_exclude_attr.append("id") # don't include id
    kiwix_exclude_attr.append("favicon") # don't include large favicon
    zims_installed = {}
    path_to_array_map = {}
    try:
        tree = ET.parse(lib_xml_file)
        root = tree.getroot()
        xml_item_no = 0
        for child in root:
            xml_item_no += 1 # hopefully this is the array number
            attributes = {}
            if 'id' not in child.attrib: # is this necessary? implies there are records with no book id which would break index for removal
                  print "xml record missing Book Id"
            id = child.attrib['id']
            for attr in child.attrib:
                if attr not in kiwix_exclude_attr:
                    attributes[attr] = child.attrib[attr] # copy if not id or in exclusion list
            zims_installed[id] = attributes
            path_to_array_map[child.attrib['path']] = xml_item_no
    except IOError:
        zims_installed = {}
    return zims_installed, path_to_array_map

def rem_libr_xml(list_str):
    command = kiwix_manage + " " + kiwix_library_xml + " remove " + list_str
    print command
    args = shlex.split(command)

    outp = subprocess.check_output(args)

def add_libr_xml(kiwix_library_xml, zim_path, zimname, zimidx):
    command = kiwix_manage + " " + kiwix_library_xml + " add " + zim_path + "/" + zimname
    if zimidx:
          command += " -i " + zim_path + "/" + zimidx
    print command
    args = shlex.split(command)
    try:
        outp = subprocess.check_output(args)

    except: #skip things that don't work
        print 'skipping ' + filename
        pass

def init():

    global iiab_base_path
    global zim_path
    global kiwix_library_xml
    global kiwix_manage

    config = ConfigParser.SafeConfigParser()
    config.read(iiab_config_file)
    iiab_base_path = config.get('location','iiab_base')
    zim_path = config.get('kiwix','iiab_zim_path')
    kiwix_library_xml = config.get('kiwix','kiwix_library_xml')
    kiwix_manage = iiab_base_path + "/kiwix/bin/kiwix-manage"

def parse_args():
    parser = argparse.ArgumentParser(description="Create library.xml for Kiwix.")
    parser.add_argument("--device", help="no trailing /. change the target device from internal storage to something else like /media/usb0")
    parser.add_argument("--no_tmp", help="don't append .tmp to the library.xml name", action="store_true")
    parser.add_argument("-f", "--force", help="force complete rebuild of library.xml", action="store_true")
    parser.add_argument("-v", "--verbose", help="Print messages.", action="store_true")
    return parser.parse_args()

# Now start the application

if __name__ == "__main__":

    # Run the main routine
    main()
