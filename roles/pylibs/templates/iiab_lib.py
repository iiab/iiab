'''
Common functions for IIAB
Admin Console functions are in adm_lib.py
'''
import os
import json
import subprocess
import shlex
import xml.etree.ElementTree as ET
import iiab.iiab_const as CONST

lang_codes = {}
lang_iso2_codes = {}

def get_zim_list(path):
    '''
    Get a list of installed zims in the passed path

    Args:
      path (str): The path to search

    Returns:
      files_processed (dict): A dict all zims found and any index directory (now obsolete)
      zim_versions (dict): A dict that translates generic zim names to physically installed
    '''

    files_processed = {}
    zim_versions = {} # we don't need this unless adm cons is installed, but easier to compute now
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
                if not os.path.isdir(path + "/" + zimidx): # only declare index if exists (could be embedded)
                    zimidx = None
                files_processed[zimname] = zimidx
                zimname = content + filename + ".zim"
                zimidx = index + filename + ".zim.idx"
                if filename in CONST.old_zim_map: # handle old names that don't parse
                    perma_ref = CONST.old_zim_map[filename]
                else:
                    ulpos = filename.rfind("_")
                    # but old gutenberg and some other names are not canonical
                    if filename.rfind("-") < 0: # non-canonical name
                        ulpos = filename[:ulpos].rfind("_")
                    perma_ref = filename[:ulpos]
                zim_info['file_name'] = filename
                zim_versions[perma_ref] = zim_info # if there are multiples, last should win
    return files_processed, zim_versions

def read_library_xml(lib_xml_file, kiwix_exclude_attr=["favicon"]): # duplicated from iiab-cmdsrv but changed
    '''
    Read zim properties from library.xml
    Returns dict of library.xml and map of zim id to zim file name (under <dev>/library/zims)

    Args:
      lib_xml_file (str): Path to file to read. Can be on removable device
      kiwix_exclude_attr (list): Zim properties to exclude from return

    Returns:
      zims_installed (dict): A dictionary holding all installed zims and their attributes
      path_to_id_map (dict): A dictionary that translates zim ids to physical names
    '''

    kiwix_exclude_attr.append("id") # don't include id because is key
    zims_installed = {}
    path_to_id_map = {}
    try:
        tree = ET.parse(lib_xml_file)
        root = tree.getroot()
        for child in root:
            attributes = {}
            if 'id' not in child.attrib: # is this necessary? implies there are records with no book id which would break index for removal
                print("xml record missing Book Id")
            zim_id = child.attrib['id']
            for attr in child.attrib:
                if attr not in kiwix_exclude_attr:
                    attributes[attr] = child.attrib[attr] # copy if not id or in exclusion list
            zims_installed[zim_id] = attributes
            path_to_id_map[child.attrib['path']] = zim_id
    except IOError:
        zims_installed = {}
    return zims_installed, path_to_id_map

def rem_libr_xml(zim_id, kiwix_library_xml):
    '''
    Remove a zim from library.xml

    Args:
      zim_id (uuid): Id of the zim to remove
      lib_xml_file (str): Path to file to read. Can be on removable device
    '''

    command = CONST.kiwix_manage + " " + kiwix_library_xml + " remove " + zim_id
    #print command
    args = shlex.split(command)
    try:
        outp = subprocess.check_output(args)
    except subprocess.CalledProcessError as e:
        if e.returncode != 2: # skip bogus file open error in kiwix-manage
            print(outp)

def add_libr_xml(kiwix_library_xml, zim_path, zimname, zimidx):
    '''
    Add a zim to library.xml

    Args:
      kiwix_library_xml (str): Name (path) of library.xml file
      zim_path (str): Path to zim file to add
      zimname (str): Name of zim file to add
      zimidx (str): Path to separate idx directory (obsolete)

    '''
    command = CONST.kiwix_manage + " " + kiwix_library_xml + " add " + zim_path + "/" + zimname
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
    '''Populate the global lang_codes dictionary from CONST.lang_codes_path json file'''

    global lang_codes
    with open(CONST.lang_codes_path, "r") as f:
        reads = f.read()
        #print("menu.json:%s"%reads)
        lang_codes = json.loads(reads)

    # create iso2 index
    for lang in lang_codes:
        lang_iso2_codes[lang_codes[lang]['iso2']  ] = lang

# there is a different algorithm in get_zim_list above
def calc_perma_ref(uri):
    '''Given a path or url return the generic zim name'''
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
    '''Lookup the iso2 equivalent of a zim language code'''
    return lang_codes[zim_lang_code]['iso2']

def human_readable(num):
    '''Convert a number to a human readable string'''
    # return 3 significant digits and unit specifier
    # TFM 7/15/2019 change to factor of 1024, not 1000 to match similar calcs elsewhere
    num = float(num)
    units = ['', 'K', 'M', 'G']
    for i in range(4):
        if num < 10.0:
            return "%.2f%s"%(num, units[i])
        if num < 100.0:
            return "%.1f%s"%(num, units[i])
        if num < 1000.0:
            return "%.0f%s"%(num, units[i])
        num /= 1024.0

# Environment Functions

def get_iiab_env(name):
    ''' read iiab.env file for a value, return "" if does not exist. return all value for *'''
    iiab_env = {}
    iiab_env_var = ''
    try:
        fd = open("/etc/iiab/iiab.env", "r")
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
