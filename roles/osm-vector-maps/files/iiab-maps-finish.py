#!/usr/bin/python3 
# -*- coding: UTF-8 -*-

import iiab.iiab_lib as iiab


import argparse
import sys, os
import json
import glob
import shutil
import json

# GLOBALS
viewer_path = '/library/www/osm-vector-maps/viewer'
vector_map_idx_dir = '/library/www/html/common/assets'
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

def write_vector_map_idx(installed_maps):
    # copied from adm_lib
    map_dict = {}
    idx_dict = {}
    for fname in installed_maps:
        map_dict = map_catalog['maps'].get(fname, '')
        if map_dict == '': continue

        # Create the idx file in format required bo js-menu system
        item = map_dict['perma_ref']
        idx_dict[item] = {}
        idx_dict[item]['file_name'] = os.path.basename(map_dict['detail_url'])
        idx_dict[item]['menu_item'] = map_dict['perma_ref']
        idx_dict[item]['size'] = map_dict['size']
        idx_dict[item]['date'] = map_dict['date']
        idx_dict[item]['region'] = map_dict['region']
        idx_dict[item]['language'] = map_dict['perma_ref'][:2]

    with open(vector_map_idx_dir + '/vector-map-idx.json', 'w') as idx:
        idx.write(json.dumps(idx_dict, indent=2))

def get_installed_tiles():
    installed_maps = []
    tile_list = glob.glob(viewer_path + '/tiles/*')
    for index in range(len(tile_list)):
       if tile_list[index].startswith('sat'): continue
       if tile_list[index].startswith('osm-planet_z0'): continue
       installed_maps.append(os.path.basename(tile_list[index]))
    return installed_maps

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

    installed_maps = get_installed_tiles()
    print('installed_maps')
    print(repr(installed_maps))
    write_vector_map_idx(installed_maps)

if __name__ == '__main__':
   main()
