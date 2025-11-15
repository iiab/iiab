#!/usr/bin/python3

"""

   Creates temp library.xml file for kiwix from contents of /zims/content and index
   Updated to handle incremental additions and deletions

   Author: Tim Moody <tim(at)timmoody(dot)com>
   Contributors: Jerry Vonau <jvonau3(at)gmail.com>

"""

import os, sys, syslog
import pwd, grp
import argparse
import iiab.iiab_lib as iiab

try:
    import iiab.adm_lib as adm
    adm_cons_installed = True
except:
    adm_cons_installed = False
    pass

def main():
    zim_path = iiab.CONST.zim_path
    zim_version_idx_dir = ""
    if adm_cons_installed:
        zim_version_idx_dir = adm.CONST.zim_version_idx_dir

    args = parse_args()
    # args.device is either value or None
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
        zims_installed, path_to_id_map = iiab.read_library_xml(kiwix_library_xml)

    zim_files, zim_versions = iiab.get_zim_list(zim_path)

    # Remove zims not in file system from library.xml
    # remove_list_str = ""
    try:
        for item in path_to_id_map:
            if item not in zim_files:
                iiab.rem_libr_xml(path_to_id_map[item], kiwix_library_xml)
    except:
        print("Failed to remove missing zims from library.xml")
        print("As a workaround, try running with -f to force rebuild of library.xml")
        sys.exit(1)

    # Add zims from file system that are not in library.xml
    for item in zim_files:
        if item not in path_to_id_map:
            iiab.add_libr_xml(kiwix_library_xml, zim_path, item, zim_files[item])

    # Create zim_versions_idx if Admin Console installed
    if adm_cons_installed:
        print("Writing zim_versions_idx")
        iiab.read_lang_codes() # needed by following
        zim_menu_defs = adm.get_zim_menu_defs() # read all menu defs
        try:
            adm.write_zim_versions_idx(zim_versions, kiwix_library_xml, zim_version_idx_dir, zim_menu_defs)
        except:
            print("Failed to write zim_version_idx.json")
            sys.exit(1)
    sys.exit()

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
