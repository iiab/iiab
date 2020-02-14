#!/usr/bin/python3

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
#import ConfigParser
import configparser
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
menuImages = doc_root + "/js-menu/menu-files/images/"
menuJsonPath = doc_root + "/home/menu.json"

assets_dir = doc_root + "/common/assets/"
lang_codes_path = assets_dir + "lang_codes.json"
lang_codes = {}
old_zim_map = {"bad.zim" : "unparseable name"}

# Working variables
# zim_files - list of zims and possible index from file system
# path_to_id_map - list of zims in current library.xml with id (for delete)
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
        path_to_id_map = {}
    else:
          zims_installed, path_to_id_map = read_library_xml(kiwix_library_xml)

    zim_files = get_zim_list(zim_path)

    # Remove zims not in file system from library.xml
    remove_list_str = ""
    for item in path_to_id_map:
        if item not in zim_files:
            rem_libr_xml(path_to_id_map[item])

    # Add zims from file system that are not in library.xml
    for item in zim_files:
          if item not in path_to_id_map:
              add_libr_xml(kiwix_library_xml, zim_path, item, zim_files[item])

    print("Writing zim_versions_idx")
    write_zim_versions_idx()
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
            zim_info = {}
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
                    # but old gutenberg and some other names are not canonical
                    if filename.rfind("-") < 0: # non-canonical name
                        ulpos = filename[:ulpos].rfind("_")
                    wiki_name = filename[:ulpos]
                zim_info['file_name'] = filename
                zim_versions[wiki_name] = zim_info # if there are multiples, last should win
    return files_processed

def read_library_xml(lib_xml_file, kiwix_exclude_attr=[""]): # duplicated from iiab-cmdsrv
    kiwix_exclude_attr.append("id") # don't include id
    kiwix_exclude_attr.append("favicon") # don't include large favicon
    zims_installed = {}
    path_to_id_map = {}
    try:
        tree = ET.parse(lib_xml_file)
        root = tree.getroot()
        xml_item_no = 0
        for child in root:
            #xml_item_no += 1 # hopefully this is the array number
            attributes = {}
            if 'id' not in child.attrib: # is this necessary? implies there are records with no book id which would break index for removal
                  print ("xml record missing Book Id")
            id = child.attrib['id']
            for attr in child.attrib:
                if attr not in kiwix_exclude_attr:
                    attributes[attr] = child.attrib[attr] # copy if not id or in exclusion list
            zims_installed[id] = attributes
            path_to_id_map[child.attrib['path']] = id
    except IOError:
        zims_installed = {}
    return zims_installed, path_to_id_map

def rem_libr_xml(id):
    command = kiwix_manage + " " + kiwix_library_xml + " remove " + id
    #print command
    args = shlex.split(command)
    try:
        outp = subprocess.check_output(args)
    except subprocess.CalledProcessError as e:
        if e.returncode != 2: # skip bogus file open error in kiwix-manage
            print (outp)

def add_libr_xml(kiwix_library_xml, zim_path, zimname, zimidx):
    command = kiwix_manage + " " + kiwix_library_xml + " add " + zim_path + "/" + zimname
    if zimidx:
          command += " -i " + zim_path + "/" + zimidx
    #print command
    args = shlex.split(command)
    try:
        outp = subprocess.check_output(args)

    except: #skip things that don't work
        #print 'skipping ' + zimname
        pass

def read_lang_codes():
   global lang_codes
   with open(lang_codes_path,"r") as f:
      reads = f.read()
      #print("menu.json:%s"%reads)
      lang_codes = json.loads(reads)

def kiwix_lang_to_iso2(zim_lang_code):
    return lang_codes[zim_lang_code]['iso2']

def init():

    global iiab_base_path
    global zim_path
    global kiwix_library_xml
    global kiwix_manage

#    config = ConfigParser.SafeConfigParser()
    config = configparser.ConfigParser()
    config.read(iiab_ini_file)
    iiab_base_path = config.get('location','iiab_base')
    zim_path = config.get('kiwix','iiab_zim_path')
    kiwix_library_xml = config.get('kiwix','kiwix_library_xml')
    kiwix_manage = iiab_base_path + "/kiwix/bin/kiwix-manage"
    read_lang_codes()

def parse_args():
    parser = argparse.ArgumentParser(description="Create library.xml for Kiwix.")
    parser.add_argument("--device", help="no trailing /. change the target device from internal storage to something else like /media/usb0")
    parser.add_argument("--no_tmp", help="don't append .tmp to the library.xml name", action="store_true")
    parser.add_argument("-f", "--force", help="force complete rebuild of library.xml", action="store_true")
    parser.add_argument("-v", "--verbose", help="Print messages.", action="store_true")
    return parser.parse_args()

def write_zim_versions_idx():
   global zim_versions
   zims_installed,path_to_id_map = read_library_xml(kiwix_library_xml)
   for perma_ref in zim_versions:
      zim_versions[perma_ref]['menu_item'] = find_menuitem_from_zimname(perma_ref)
      articlecount,mediacount,size,tags,lang,date = \
           get_substitution_data(perma_ref, zims_installed, path_to_id_map)
      zim_versions[perma_ref]['article_count'] = articlecount
      zim_versions[perma_ref]['media_count'] = mediacount
      size = human_readable(float(size) * 1024) # kiwix reports in K
      zim_versions[perma_ref]['size'] = size
      zim_versions[perma_ref]['tags'] = tags

      zim_versions[perma_ref]['language'] = lang
      zim_versions[perma_ref]['zim_date'] = date

   # Write Version Map
   if os.path.isdir(zim_version_idx_dir):
      with open(zim_version_idx_dir + zim_version_idx_file, 'w') as fp:
         fp.write(json.dumps(zim_versions,indent=2 ))
         fp.close()
   else:
      print (zim_version_idx_dir + " not found.")

def get_substitution_data(perma_ref,zims_installed, path_to_id_map):
   #reconstruct the path in the id map
   path = 'content/' + zim_versions[perma_ref]['file_name'] + '.zim'
   id = path_to_id_map[path]
   item = zims_installed[id]

   if len(item) != 0 or perma_ref == 'test':
      mediacount = item.get('mediaCount','')
      articlecount = item.get('articleCount','')
      size = item.get('size','')
      tags = item.get('tags','')
      zim_lang = item.get('language')
      menu_def_lang = kiwix_lang_to_iso2(zim_lang)
      date =  item.get('date','')
      return (articlecount,mediacount,size,tags,menu_def_lang,date)
   return ('0','0','0','0','0','0')

def get_menu_def_zimnames(intended_use='zim'):
   menu_def_dict = {}
   os.chdir(menuDefs)
   for filename in os.listdir('.'):
      if fnmatch.fnmatch(filename, '*.json'):
         try:
            with open(filename,'r') as json_file:
                readstr = json_file.read()
                data = json.loads(readstr)
         except:
            print("failed to parse %s"%filename)
            print(readstr)
         if data.get('intended_use','') != 'zim':
            continue
         zimname = data.get('zim_name','')
         if zimname != '':
            menu_def_dict[data['zim_name']] = menuDefs + filename
   return menu_def_dict

def find_menuitem_from_zimname(zimname):
   defs = get_menu_def_zimnames()
   defs_filename = defs.get(zimname,'')
   if defs_filename != '':
      #print("reading menu-def:%s"%defs_filename)
      with open(defs_filename,'r') as json_file:
          readstr = json_file.read()
          data = json.loads(readstr)
          return data.get('menu_item_name','')
   return ''

def get_kiwix_catalog_item(perma_ref):
   # Read the kiwix catalog
   with open(KIWIX_CAT, 'r') as kiwix_cat:
      json_data = kiwix_cat.read()
      download = json.loads(json_data)
      zims = download['zims']
      for uuid in zims.keys():
         #print("%s   %s"%(zims[uuid]['perma_ref'],perma_ref,))
         if zims[uuid]['perma_ref'] == perma_ref:
            return zims[uuid]
      return {}

def human_readable(num):
    # return 3 significant digits and unit specifier
    # TFM 7/15/2019 change to factor of 1024, not 1000 to match similar calcs elsewhere
    num = float(num)
    units = [ '','K','M','G']
    for i in range(4):
        if num<10.0:
            return "%.2f%s"%(num,units[i])
        if num<100.0:
            return "%.1f%s"%(num,units[i])
        if num < 1000.0:
            return "%.0f%s"%(num,units[i])
        num /= 1024.0

# Now start the application
if __name__ == "__main__":

    # Run the main routine
    main()
