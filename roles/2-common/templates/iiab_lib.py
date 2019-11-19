# iiab_lib.py
# common functions for IIAB
# Admin Console functions are in adm_lib.py

import os, sys, syslog
import pwd, grp
import time
from datetime import date, datetime
import json
import yaml
import re
import subprocess
import shlex
import configparser
import xml.etree.ElementTree as ET
import argparse
import iiab.iiab_const as cons

lang_codes = {}

def get_zim_list(path):
    files_processed = {}
    zim_versions = {} # we don't need this unless adm cons is installed, but easier to compute now
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
                if filename in cons.old_zim_map: # handle old names that don't parse
                    perma_ref = cons.old_zim_map[filename]
                else:
                    ulpos = filename.rfind("_")
                    # but old gutenberg and some other names are not canonical
                    if filename.rfind("-") < 0: # non-canonical name
                        ulpos = filename[:ulpos].rfind("_")
                    perma_ref = filename[:ulpos]
                zim_info['file_name'] = filename
                zim_versions[perma_ref] = zim_info # if there are multiples, last should win
    return files_processed, zim_versions

def read_library_xml(lib_xml_file, kiwix_exclude_attr=[""]): # duplicated from iiab-cmdsrv
    # returns dict of library.xml and map of zim id to zim file name (under <dev>/library/zims)

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
                print("xml record missing Book Id")
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
    command = cons.kiwix_manage + " " + kiwix_library_xml + " remove " + id
    #print command
    args = shlex.split(command)
    try:
        outp = subprocess.check_output(args)
    except subprocess.CalledProcessError as e:
        if e.returncode != 2: # skip bogus file open error in kiwix-manage
            print(outp)

def add_libr_xml(kiwix_library_xml, zim_path, zimname, zimidx):
    command = cons.kiwix_manage + " " + kiwix_library_xml + " add " + cons.zim_path + "/" + zimname
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
    with open(cons.lang_codes_path,"r") as f:
        reads = f.read()
        #print("menu.json:%s"%reads)
        lang_codes = json.loads(reads)

# there is a different algorithm in get_zim_list above

def calc_perma_ref(uri):
    url_slash = uri.split('/')
    url_end = url_slash[-1] # last element
    file_ref = url_end.split('.zim')[0] # true for both internal and external index
    perma_ref_parts = file_ref.split('_')
    perma_ref = perma_ref_parts[0]
    if len(perma_ref_parts) > 1:
        perma_ref_parts = perma_ref_parts[0:len(perma_ref_parts) - 1] # all but last, which should be date
        for part in perma_ref_parts[1:]: # start with 2nd
            if not part.isdigit():
                perma_ref += "_" + part
    return perma_ref

def kiwix_lang_to_iso2(zim_lang_code):
    return lang_codes[zim_lang_code]['iso2']

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

# Environment Functions

def get_iiab_env(name):
    """ read iiab.env file for a value, return "" if does not exist. return all value for *"""
    iiab_env = {}
    iiab_env_var = ''
    try:
        fd = open(cons.iiab_env_file,"r")
        for line in fd:
            line = line.lstrip()
            line = line.rstrip('\n')
            if len(line) == 0:
                continue
            if line[0] == "#":
                continue
            if line.find("=") == -1:
                continue
            chunks = line.split('=')
            iiab_env[chunks[0]] = chunks[1]
            if chunks[0] == name:
                iiab_env_var = chunks[1]
    except:
        pass
    finally:
        fd.close()
    if name == '*':
        return iiab_env
    else:
        return iiab_env_var
