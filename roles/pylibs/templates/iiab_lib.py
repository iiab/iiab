'''
Common functions for IIAB
Admin Console functions are in adm_lib.py
'''
import os
import json
import subprocess
import shlex
import re
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
                perma_ref = calc_zim_perma_ref(zimname)
                zim_info['file_name'] = filename
                zim_versions[perma_ref] = zim_info # if there are multiples, last should win
    return files_processed, zim_versions

KIWIX_OPDS_ACQUISITION_REL = 'http://opds-spec.org/acquisition/open-access'
KIWIX_OPDS_THUMBNAIL_REL = 'http://opds-spec.org/image/thumbnail'
# OPDS entry elements named after the classic book attribute holding the same zim property
KIWIX_OPDS_SAME_NAME_PROPS = ['title', 'language', 'name', 'flavour', 'category', 'tags', 'articleCount', 'mediaCount']

def xml_local_tag(tag):
    '''Strip any XML namespace off an element tag, eg. {http://www.w3.org/2005/Atom}entry -> entry'''
    return tag.split('}')[-1]

def opds_sub_element_text(element, sub_name):
    '''Return the text of the first child of element with the given namespace free name, '' if none'''
    for child in element:
        if xml_local_tag(child.tag) == sub_name:
            return (child.text or '').strip()
    return ''

def opds_link_to_book_attrs(link, attributes):
    '''Record the zim property carried by an OPDS link, if any, in attributes'''
    rel = link.attrib.get('rel', '')
    href = link.attrib.get('href', '')
    if rel == KIWIX_OPDS_ACQUISITION_REL:
        if href.startswith('http://') or href.startswith('https://'):
            attributes['url'] = href # a remote copy of the zim
        else:
            attributes['path'] = href # the zim on this box, relative to the library file
        length = link.attrib.get('length', '')
        if length.isdigit():
            attributes['size'] = str(int(length) >> 10) # OPDS is bytes, classic book records are KiB
    elif rel == KIWIX_OPDS_THUMBNAIL_REL:
        attributes['faviconMimeType'] = link.attrib.get('type', '').split(';')[0]
        if href.startswith('data:') and 'base64,' in href:
            attributes['favicon'] = href.split('base64,', 1)[1] # same bare base64 as classic book records
        else:
            attributes['faviconUrl'] = href

def opds_entry_to_book_attrs(entry):
    '''
    Convert an OPDS entry to the dict of zim properties kiwix-manage would have
    written as the attributes of a classic book record, so that callers need
    not know which of the 2 library.xml formats they are reading
    '''
    attributes = {}
    issued_date = ''
    updated_date = ''
    for child in entry:
        name = xml_local_tag(child.tag)
        text = (child.text or '').strip()
        if name == 'id':
            attributes['id'] = text[len('urn:uuid:'):] if text.startswith('urn:uuid:') else text
        elif name == 'summary':
            attributes['description'] = text
        elif name in KIWIX_OPDS_SAME_NAME_PROPS:
            attributes[name] = text
        elif name == 'author':
            attributes['creator'] = opds_sub_element_text(child, 'name')
        elif name == 'publisher':
            attributes['publisher'] = opds_sub_element_text(child, 'name')
        elif name == 'issued': # dc:issued, the zim date, kiwix dumps the same date in updated
            issued_date = text[:10]
        elif name == 'updated':
            updated_date = text[:10]
        elif name == 'link':
            opds_link_to_book_attrs(child, attributes)
    date = issued_date or updated_date
    if date != '':
        attributes['date'] = date
    # classic book records omit empty properties, and so do we
    return {prop: value for prop, value in attributes.items() if value != ''}

def read_library_xml(lib_xml_file, kiwix_exclude_attr=["favicon"]): # duplicated from iiab-cmdsrv but changed
    '''
    Read zim properties from library.xml
    Returns dict of library.xml and map of zim id to zim file name (under <dev>/library/zims)

    Handles both library.xml formats:
      classic  <library><book id=".." path=".." title=".." .../></library>
      OPDS     <feed><entry><id>urn:uuid:..</id><title>..</title>...</entry></feed>
    Recent kiwix-tools (nightly builds of 2026-09 onwards) create a NEW library
    file in OPDS format, and rewrite an existing one in the format it found it.

    Args:
      lib_xml_file (str): Path to file to read. Can be on removable device
      kiwix_exclude_attr (list): Zim properties to exclude from return

    Returns:
      zims_installed (dict): A dictionary holding all installed zims and their attributes
      path_to_id_map (dict): A dictionary that translates zim ids to physical names
    '''

    excluded_attr = {'id'} # use a set and never include the key
    excluded_attr.update(kiwix_exclude_attr)
    zims_installed = {}
    path_to_id_map = {}
    try:
        tree = ET.parse(lib_xml_file)
    except OSError: # not there yet, which is normal the first time round
        return zims_installed, path_to_id_map
    except ET.ParseError as e:
        print("Cannot parse Kiwix library file " + str(lib_xml_file) + " (" + str(e) + ")")
        return zims_installed, path_to_id_map
    root = tree.getroot()
    for child in root:
        if 'id' in child.attrib: # classic book record, all properties are attributes
            zim_id = child.attrib['id']
            attributes = {}
            for attr in child.attrib:
                if attr not in excluded_attr:
                    attributes[attr] = child.attrib[attr] # copy if not id or in exclusion list
        else: # OPDS entry, properties are child elements
            attributes = opds_entry_to_book_attrs(child)
            zim_id = attributes.get('id', '')
            if zim_id == '': # without an id it can neither be shown nor removed
                print("Skipping " + xml_local_tag(child.tag) + " record with no id in " + str(lib_xml_file))
                continue
            for attr in excluded_attr:
                attributes.pop(attr, None)
        zims_installed[zim_id] = attributes
        path = attributes.get('path', '')
        if path != '': # remote only zims have no local path
            path_to_id_map[path] = zim_id
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

def add_libr_xml(kiwix_library_xml, zim_path, zimname, zimidx=None):
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

def calc_perma_ref(uri): # preserve name for backwards compatibility
    return calc_zim_perma_ref(uri)

def calc_zim_perma_ref(uri):
    '''Given a path with a zim filename return the generic zim name'''
    url_slash = uri.split('/')
    url_end = url_slash[-1] # last element
    zim_filename = url_end.split('.zim')[0] # true for both internal and external index
    if zim_filename in CONST.old_zim_map: # handle old names that don't parse
        perma_ref = CONST.old_zim_map[zim_filename]
    else:
        # handle various zim name patterns:
        # 1. canonical zim ending in _YYYY-MM
        # as of 10/16/2024 it looks like all Kiwix zims fit this pattern
        # 2. otherwise assume no versioning and perma_ref = filename
        #match = re.search("_[0-5][0-9][0-5][0-9]-[0-5][0-9]$", zim_filename) # good until 2060
        match = re.search(r'_20[0-9]{2}-(0[1-9]|1[0-2])$',zim_filename) # more robust regex for date pattern for this century
        if match:
            perma_ref = zim_filename[: match.span()[0]]
        else:
            perma_ref = zim_filename
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
