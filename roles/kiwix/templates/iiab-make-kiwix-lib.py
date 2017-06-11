#!/usr/bin/python

"""

   Creates library.xml file for kiwix from contents of /zims/content and index

   Author: Tim Moody <tim(at)timmoody(dot)com>

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
XSCE_PATH='/etc/iiab'
if not XSCE_PATH in sys.path:
   sys.path.append(XSCE_PATH)
from iiab_env import get_iiab_env

# Config Files
iiab_config_file = "/etc/iiab/iiab.ini"

# Variables that should be read from config file
# All of these variables will be read from config files and recomputed in init()
iiab_zim_path = "/library/zims"
kiwix_library_xml = "/library/zims/library.xml"

iiab_base_path = "/opt/schoolserver"
kiwix_manage = iiab_base_path + "/kiwix/bin/kiwix-manage"
doc_root = get_iiab_env('WWWROOT')
zim_version_idx = doc_root + "/common/assets/zim_version_idx.json"
zim_versions = {}

def main():
    """Server routine"""

    init()

    # remove existing file
    try:
        os.remove(kiwix_library_xml)
    except OSError:
        pass

    # add each file in /library/zims/content with corresponding index
    # only add a single .zim for each .zimxx file

    files_processed = {}
    content = iiab_zim_path + "/content/"
    index = iiab_zim_path + "/index/"

    flist = os.listdir(content)
    flist.sort()
    for filename in flist:
        zimpos = filename.find(".zim")
        if zimpos != -1:
            filename = filename[:zimpos]
            if filename not in files_processed:
                files_processed[filename] = True
                command = kiwix_manage + " " + kiwix_library_xml + " add " + content + filename + ".zim -i " + index + filename + ".zim.idx"
                #command = kiwix_manage + " " + kiwix_library_xml + " add " + content + filename + ".zim"
                #print command
                args = shlex.split(command)
                try:
                    outp = subprocess.check_output(args)

                    # create map of generic zim name to actual, assumes pattern of <name>_<yyyy-mm>
                    # all current files follow this pattern, but some older ones, no longer in the catalog, do not
                    ulpos = filename.rfind("_")
                    wiki_name = filename[:ulpos]
                    zim_versions[wiki_name] = filename # if there are multiples, last should win
                except: #skip things that don't work
                    print 'skipping ' + filename
                    pass

    with open(zim_version_idx, 'w') as fp:
        json.dump(zim_versions, fp)

    sys.exit()

def init():

    global iiab_base_path
    global iiab_zim_path
    global kiwix_library_xml
    global kiwix_manage

    config = ConfigParser.SafeConfigParser()
    config.read(iiab_config_file)
    iiab_base_path = config.get('location','iiab_base')
    iiab_zim_path = config.get('kiwix-serve','iiab_zim_path')
    kiwix_library_xml = config.get('kiwix-serve','kiwix_library_xml')
    kiwix_manage = iiab_base_path + "/kiwix/bin/kiwix-manage"

# Now start the application

if __name__ == "__main__":

    # Run the main routine
    main()
