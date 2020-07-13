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

import argparse
import sys, os
import json
import glob
import shutil
import json

# GLOBALS
viewer_path = '/library/www/osm-vector-maps/viewer'
catalog_path = '/etc/iiab'
map_catalog = {}

if len(sys.argv) != 2:
   print("Argument 1=map_url")
   sys.exit(1)

def get_map_catalog():
    global map_catalog
    input_json = '/etc/iiab/map-catalog.json'
    with open(input_json, 'r') as regions:
        reg_str = regions.read()
        map_catalog = json.loads(reg_str)
    #print(json.dumps(map_catalog, indent=2))
    return map_catalog

def subproc_cmd(cmdstr, shell=False):
    args = shlex.split(cmdstr)
    outp = subproc_check_output(args, shell=shell)
    return (outp)

def parse_args():
    parser = argparse.ArgumentParser(description="Create init.json for a tile URL.")
    parser.add_argument("map_url", help="The 'detail_url' field in mapcatalog.json.")
    return parser.parse_args()

def main():
    global map_catalog
    args = parse_args()
    map_catalog = get_map_catalog()
    catalog = map_catalog['maps']
    #for k in catalog.keys():
      #print(k)
    map   = catalog.get(args.map_url,{})
    if  len(map) == 0:
        print('Download URL not found in map-catalog.json: %s'%args.map_url)
        sys.exit(1)

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

if __name__ == '__main__':
   if adm_cons_installed:
      main()
