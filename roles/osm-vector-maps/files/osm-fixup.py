#!/usr/bin/python3 
# -*- coding: UTF-8 -*- import sys, os import time import argparse

import argparse
import sys, os
import json
import glob
import shutil

# GLOBALS
viewer_path = '/library/www/osm-vector-maps/viewer'
region_path = '/etc/iiab'
regions_json = {}
config = {}

if len(sys.argv) != 3:
   print("Argument 1=region, 2=<location or cmdsrv.conf>")
   sys.exit(1)

def parse_args():
    parser = argparse.ArgumentParser(description="Assemble Resources for Maps.")
    parser.add_argument("region", help="Looked up in regions.json.")
    parser.add_argument("configdir", help="Place to look for cmdsrv.conf")
    return parser.parse_args()

def get_regions():
   global regions_json
   # error out if environment is missing

   REGION_INFO = '%s/regions.json'%region_path
   if not os.path.isfile(REGION_INFO):
      print("no such file: %s"%REGION_INFO)
      sys.exit(1)
   with open(REGION_INFO,'r') as region_fp:
      try:
         data = json.loads(region_fp.read())
         regions_json = data['regions']
      except:
         print("regions.json parse error")
         sys.exit(1)
   
def main():
   global config
   args = parse_args()
   configfile = args.configdir + '/cmdsrv.conf'
   with open(configfile,'r') as conf_fp:
      try:
         inp = json.loads(conf_fp.read())
      except Exception as e:
         print("cmdsrv.json parse error:%s"%e)
         sys.exit(1)
   config = inp['cmdsrv_conf']      
   get_regions()
   if not args.region in regions_json.keys():
      print('Region not found: %s'%args.region)
      sys.exit(1)

   osm_tile = config['maps_working_dir'] + str(os.path.basename(config['maps_osm_url']))
   sat_tile = config['maps_working_dir'] + str(os.path.basename(config['maps_sat_url']))
   for found in glob.glob(config['maps_working_dir'] + '/*'):
      if found == osm_tile:
         if os.path.isfile(config['maps_viewer_dir'] + os.path.basename(osm_tile)):
            os.remove(config['maps_viewer_dir'] + os.path.basename(osm_tile))
         shutil.move(osm_tile,config['maps_viewer_dir'])
         src = '%s/%s'%(viewer_path,os.path.basename(osm_tile))
         dest = '%s/%s'%(viewer_path,'osm_planet.mbtiles')
         if os.path.islink(dest):
            os.unlink(dest)
         os.symlink(src,dest)
      elif found == sat_tile:
         if os.path.isfile(config['maps_viewer_dir'] + os.path.basename(sat_tile)):
            os.remove(config['maps_viewer_dir'] + os.path.basename(sat_tile))
         shutil.move(sat_tile,config['maps_viewer_dir'])
         src = '%s/%s'%(viewer_path,os.path.basename(sat_tile))
         dest = '%s/%s'%(viewer_path,'satellite.mbtiles')
         if os.path.islink(dest):
            os.unlink(dest)
         os.symlink(src,dest)
      else:
         if os.path.isfile(config['maps_viewer_dir'] + 'tiles/' + os.path.basename(found)):
            os.remove(config['maps_viewer_dir'] + 'tiles/' + os.path.basename(found))
         shutil.move(found,config['maps_viewer_dir'] + 'tiles')

   src = '%s/tiles/%s'%(viewer_path,os.path.basename(regions_json[args.region]['detail_url']))
   dest = '%s/%s'%(viewer_path,'detail.mbtiles')
   if os.path.islink(dest):
      os.unlink(dest)
   os.symlink(src,dest)

   # create init.json which sets initial coords and zoom
   init = {}
   init['region'] = args.region
   init['zoom'] = regions_json[args.region]['zoom'] 
   init['center_lon'] = regions_json[args.region]['center_lon'] 
   init['center_lat'] = regions_json[args.region]['center_lat'] 
   init_fn = viewer_path + '/init.json'
   with open(init_fn,'w') as init_fp:
      init_fp.write(json.dumps(init,indent=2))

if __name__ == "__main__":
    # Run the main routine
   main()
