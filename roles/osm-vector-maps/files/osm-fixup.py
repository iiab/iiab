#!/usr/bin/python3 
# -*- coding: UTF-8 -*- import sys, os import time import argparse

import iiab.iiab_lib as iiab

try:
    import iiab.adm_lib as adm
    import iiab.adm_const as CONST
    adm_cons_installed = True
except:
    adm_cons_installed = False
    pass

import argparse
import sys, os
import json
import glob
import shutil
import json

# GLOBALS
viewer_path = '/library/www/osm-vector-maps/viewer'
catalog_path = '/etc/iiab'

if len(sys.argv) != 3:
   print("Argument 1=map_url, 2=<location or cmdsrv.conf>")
   sys.exit(1)

def parse_args():
    parser = argparse.ArgumentParser(description="Assemble Resources for Maps.")
    parser.add_argument("map_url", help="The 'detail_url' field in mapcatalog.json.")
    parser.add_argument("configdir", help="Place to look for cmdsrv.conf")
    return parser.parse_args()

def main():
    global map_catalog
    args = parse_args()
    map_catalog = adm.get_map_catalog()
    catalog = map_catalog['maps']
    found_map = catalog.get(args.map_url,'')
    if found_map == '':
        print('Download URL not found in map-catalog.json: %s'%args.map_url)
        sys.exit(1)

    osm_tile = CONST.maps_working_dir + str(os.path.basename(CONST.maps_osm_url))
    sat_tile = CONST.maps_working_dir + str(os.path.basename(CONST.maps_sat_url))
    for found in glob.glob(CONST.maps_working_dir + '/*'):
        if found == osm_tile:
            if os.path.isfile(CONST.maps_downloads_dir + os.path.basename(osm_tile)):
               os.remove(CONST.maps_downloads_dir + os.path.basename(osm_tile))
            shutil.move(osm_tile,CONST.maps_downloads_dir)
        elif found == sat_tile:
            if os.path.isfile(CONST.maps_downloads_dir + os.path.basename(sat_tile)):
                os.remove(CONST.maps_downloads_dir + os.path.basename(sat_tile))
            shutil.move(sat_tile,CONST.maps_downloads_dir)
        else:
            if os.path.isfile(CONST.maps_viewer_dir + 'tiles/' + os.path.basename(found)):
                os.remove(CONST.maps_viewer_dir + 'tiles/' + os.path.basename(found))
            shutil.move(found,CONST.maps_viewer_dir + 'tiles')


    # create init.json which sets initial coords and zoom
    init = {}
    map = catalog[args.map_url]
    init['region'] = map['region']
    init['zoom'] = map['zoom'] 
    init['center_lon'] = map['center_lon'] 
    init['center_lat'] = map['center_lat'] 
    init_fn = viewer_path + '/init.json'
    with open(init_fn,'w') as init_fp:
        init_fp.write(json.dumps(init,indent=2))

    adm.get_map_catalog()
    map_menu_def_list = adm.get_map_menu_defs()
    previous_idx = adm.read_vector_map_idx()

    installed_tiles = adm.get_installed_tiles()

    adm.write_vector_map_idx(installed_tiles)

    # For installed regions, check that a menu def exists, and it's on home page
    for map in installed_tiles:
        '''
        if region == 'maplist': # it is the splash page, display only if no others
            menu_item_name = 'en-map_test'
            map_item = { "perma_ref" : menu_item_name }
            if len(installed_maps) == 1:
                adm.update_menu_json(menu_item_name)
                return
        elif region not in adm.map_catalog['maps']:
        '''
        if map not in adm.map_catalog['maps'].keys():
            print("Skipping unknown map " + map)
            continue
        else:
            map_item = adm.map_catalog['maps'][map]
            menu_item_name = map_item['perma_ref']

            if not (menu_item_name in map_menu_def_list):
                print('Creating menu def for %s'%menu_item_name)
                adm.create_map_menu_def(map, menu_item_name, map_item)
        # if autoupdate allowed and this is a new region then add to home menu
        if adm.fetch_menu_json_value('autoupdate_menu') and menu_item_name not in previous_idx:
            print('Auto-update of menu items is enabled. Adding %s'%map )
            adm.update_menu_json(menu_item_name)
            # redirect from box/maps to an installed map rather than test page
            with open(adm.CONST.map_doc_root + '/index.html','w') as fp:
                outstr = """<head> \n<meta http-equiv="refresh" content="0; URL=/osm-vector-maps/en-osm-omt_%s " />\n</head>"""%fname
                fp.write(outstr)

if __name__ == '__main__':
   if adm_cons_installed:
      main()
