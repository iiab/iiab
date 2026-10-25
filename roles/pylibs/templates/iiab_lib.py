'''
Common functions for IIAB
Admin Console functions are in adm_lib.py
'''
import json
import os
import re
import shlex
import subprocess
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
# OPDS entry element names that match the classic book attribute for the same
# ZIM property
KIWIX_OPDS_SAME_NAME_PROPS = ['title', 'language', 'name', 'flavour', 'category', 'tags', 'articleCount', 'mediaCount']

def xml_local_tag(tag):
    '''Strip any XML namespace off an element tag, e.g. {http://www.w3.org/2005/Atom}entry -> entry'''
    return tag.split('}')[-1]

def opds_sub_element_text(element, sub_name):
    '''Return the text of the first child of element with the given namespace-free name, '' if none'''
    for child in element:
        if isinstance(child.tag, str) and xml_local_tag(child.tag) == sub_name:
            return (child.text or '').strip()
    return ''

def opds_link_to_book_attrs(link, attributes):
    '''Record the ZIM property carried by an OPDS link in attributes, if any'''
    rel = link.attrib.get('rel', '')
    href = link.attrib.get('href', '')
    if rel == KIWIX_OPDS_ACQUISITION_REL:
        if '://' in href: # URI scheme (e.g. http, https, file); the same test libkiwix makes for a remote copy of the ZIM
            attributes['url'] = href
        else:
            attributes['path'] = href # the ZIM on this box, relative to the library file
        length = link.attrib.get('length', '')
        if length.isdigit():
            attributes['size'] = str(int(length) >> 10) # OPDS is bytes, classic book records are KiB
    elif rel == KIWIX_OPDS_THUMBNAIL_REL:
        # Prefer the inline base64 favicon over a URL, and never mix fields
        # if an entry should carry more than one thumbnail link
        if href.startswith('data:') and 'base64,' in href:
            attributes['favicon'] = href.split('base64,', 1)[1] # same bare base64 as classic book records
            attributes.pop('faviconUrl', None)
            attributes['faviconMimeType'] = link.attrib.get('type', '').split(';')[0]
        elif 'favicon' not in attributes:
            attributes['faviconUrl'] = href
            attributes['faviconMimeType'] = link.attrib.get('type', '').split(';')[0]

def opds_entry_to_book_attrs(entry):
    '''
    Convert an OPDS entry to the dict of ZIM properties kiwix-manage would have
    written as the attributes of a classic book record, so that callers need
    not know which of the two library file formats they are reading
    '''
    attributes = {}
    for child in entry:
        if not isinstance(child.tag, str): # XML comments and processing instructions aren't elements
            continue
        name = xml_local_tag(child.tag)
        text = (child.text or '').strip()
        if name == 'id':
            attributes['id'] = text.removeprefix('urn:uuid:')
        elif name == 'summary':
            attributes['description'] = text
        elif name in KIWIX_OPDS_SAME_NAME_PROPS:
            attributes[name] = text
        elif name == 'author':
            attributes['creator'] = opds_sub_element_text(child, 'name')
        elif name == 'publisher':
            attributes['publisher'] = opds_sub_element_text(child, 'name')
        elif name == 'issued': # dc:issued, the ZIM publication date; only present when the ZIM has one
            attributes['date'] = text[:10]
        elif name == 'link':
            opds_link_to_book_attrs(child, attributes)
    # classic book records omit empty properties, and so do we
    return {prop: value for prop, value in attributes.items() if value != ''}

def normalize_kiwix_lib_path(path, lib_xml_file):
    '''
    Return a local ZIM path the way read_library_xml()'s callers expect it,
    i.e. relative to the directory of the library file (e.g. content/<name>.zim),
    or '' if the path is not a local ZIM inside the library directory.
    The OPDS writer emits local acquisition hrefs already relative to the
    library file, but also tolerate ./ and .. forms and absolute paths.
    Paths that resolve outside the library directory (e.g. a tampered href
    such as /etc/passwd) are rejected, not escaped past with '..'.
    '''
    lib_dir = os.path.dirname(os.path.abspath(lib_xml_file))
    norm = os.path.normpath(path)
    if os.path.isabs(norm):
        norm = os.path.relpath(norm, lib_dir)
    abs_norm = os.path.abspath(os.path.join(lib_dir, norm))
    try:
        common = os.path.commonpath([abs_norm, lib_dir])
    except ValueError: # different drives/volumes (never on IIAB, but be safe)
        return ''
    if common != lib_dir:
        return ''
    return norm

def read_library_xml(lib_xml_file, kiwix_exclude_attr=["favicon"]): # duplicated from iiab-cmdsrv but changed
    '''
    Read ZIM properties from a Kiwix library file
    Returns dict of library records and map of ZIM id to ZIM file name (under <dev>/library/zims)

    Handles both library file formats:
      classic  <library><book id=".." path=".." title=".." .../></library>
      OPDS     <feed><entry><id>urn:uuid:..</id><title>..</title>...</entry></feed>
    kiwix-tools 14 supports only classic XML; the kiwix-tools 15 beta supports
    only OPDS.  This is a clean break with no migration path between formats.

    Args:
      lib_xml_file (str): Path to file to read. Can be on removable device
      kiwix_exclude_attr (list): ZIM properties to exclude from return

    Returns:
      zims_installed (dict): A dictionary holding all installed ZIMs and their attributes
      path_to_id_map (dict): A dictionary that translates ZIM ids to physical names
    '''

    excluded_attr = {'id'} # use a set and never include the key
    excluded_attr.update(kiwix_exclude_attr)
    zims_installed = {}
    path_to_id_map = {}
    try:
        tree = ET.parse(lib_xml_file)
        root = tree.getroot()
        for child in root:
            if not isinstance(child.tag, str): # XML comments and processing instructions aren't elements
                continue
            if 'id' in child.attrib: # classic book record, all properties are attributes
                zim_id = child.attrib['id']
                attributes = {}
                for attr in child.attrib:
                    if attr not in excluded_attr:
                        attributes[attr] = child.attrib[attr] # copy if not id or in exclusion list
            elif xml_local_tag(child.tag) == 'entry': # OPDS entry, properties are child elements
                attributes = opds_entry_to_book_attrs(child)
                zim_id = attributes.get('id', '')
                if zim_id == '': # without an id it can neither be shown nor removed
                    print("Skipping OPDS entry with no id in " + str(lib_xml_file))
                    continue
                for attr in excluded_attr:
                    attributes.pop(attr, None)
            else: # OPDS feed-level metadata, e.g. <title>, <updated> and <link>, not a ZIM
                continue
            zims_installed[zim_id] = attributes
            path = attributes.get('path', '')
            if path != '': # remote-only ZIMs have no local path
                path = normalize_kiwix_lib_path(path, lib_xml_file)
                if path == '': # not a local ZIM inside the library dir, e.g. a tampered href
                    attributes.pop('path', None)
                else:
                    attributes['path'] = path
                    path_to_id_map[path] = zim_id
    except OSError: # not there yet, which is normal the first time round
        return zims_installed, path_to_id_map
    except ET.ParseError as e:
        print("Cannot parse Kiwix library file " + str(lib_xml_file) + " (" + str(e) + ")")
        return zims_installed, path_to_id_map
    except Exception as e:
        # Degrade to "no ZIMs" rather than crash the caller on an unexpected
        # error (a malformed entry, an exotic path, ...), as the previous
        # reader did.
        print("Cannot read Kiwix library file " + str(lib_xml_file) + " (" + str(e) + ")")
        return zims_installed, path_to_id_map
    return zims_installed, path_to_id_map

def read_library(lib_path=None, catalog_db=None, kiwix_exclude_attr=("favicon",)):
    '''
    Read installed ZIM metadata, preferring the SQLite catalog cache.

    The ZIM directory is the source of truth; catalog.sqlite is a disposable
    cache maintained by iiab-make-kiwix-lib.py.  When the cache is unavailable
    (or lib_path is not the internal library, e.g. a USB stick), fall back to
    parsing the OPDS/XML library file with read_library_xml().

    Returns the same (zims_installed, path_to_id_map) tuple as
    read_library_xml().
    '''
    default_lib = getattr(CONST, 'kiwix_library_path',
                          getattr(CONST, 'kiwix_library_xml', ''))
    if lib_path is None:
        lib_path = default_lib
    if catalog_db is None:
        catalog_db = getattr(CONST, 'zim_catalog_db', '')

    internal = (lib_path and default_lib and
                os.path.abspath(lib_path) == os.path.abspath(default_lib))
    if internal and catalog_db and os.path.exists(catalog_db):
        try:
            from iiab.iiab_zim_catalog import read_catalog
            zims_installed, path_to_id_map = read_catalog(
                catalog_db, kiwix_exclude_attr)
            # An empty cache (e.g. after a schema bump) is not authoritative:
            # fall back to the library file when it still has content.
            if zims_installed or not os.path.exists(lib_path):
                return zims_installed, path_to_id_map
        except Exception as e:
            print("Cannot read catalog cache " + str(catalog_db) + " (" +
                  str(e) + "); falling back to " + str(lib_path))

    return read_library_xml(lib_path, list(kiwix_exclude_attr))

def rem_libr_xml(zim_id, kiwix_library_xml):
    '''
    Deprecated: IIAB's catalog builder no longer uses kiwix-manage.
    Kept for external scripts that still manipulate a Kiwix library file.

    Remove a ZIM from a Kiwix library file

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
    Deprecated: IIAB's catalog builder no longer uses kiwix-manage.
    Kept for external scripts that still manipulate a Kiwix library file.

    Add a zim to a Kiwix library file

    Args:
      kiwix_library_xml (str): Name (path) of library file
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
