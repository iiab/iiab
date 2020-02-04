#!/usr/bin/python3 
# -*- coding: UTF-8 -*-

import iiab.iiab_lib as iiab

try:
    import iiab.adm_lib as adm
    import iiab.adm_const as CONST
    adm_cons_installed = True
except:
    adm_cons_installed = False
    pass

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
    for present in glob.glob(CONST.maps_working_dir + '/*'):
        if present == osm_tile:
            if os.path.isfile(CONST.maps_downloads_dir + os.path.basename(osm_tile)):
               os.remove(CONST.maps_downloads_dir + os.path.basename(osm_tile))
            shutil.move(osm_tile,CONST.maps_downloads_dir)
        elif present == sat_tile:
            if os.path.isfile(CONST.maps_downloads_dir + os.path.basename(sat_tile)):
                os.remove(CONST.maps_downloads_dir + os.path.basename(sat_tile))
            shutil.move(sat_tile,CONST.maps_downloads_dir)
        else:
            if os.path.isfile(CONST.maps_viewer_dir + 'tiles/' + os.path.basename(present)):
                os.remove(CONST.maps_viewer_dir + 'tiles/' + os.path.basename(present))
            shutil.move(present,CONST.maps_viewer_dir + 'tiles')


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

    try:
      adm.subproc_run("iiab-update-map", shell=True)
    except:
      print('iiab-updatee-map ERROR')

if __name__ == '__main__':
   if adm_cons_installed:
      main()
