#!/opt/iiab/bittorrent_venv/bin/python3
####!{{ transmission_venv }}/bin/python3
# Get a map from InternetArchive using bittorrent

import os,sys
sys.path.append('/usr/local/lib/python2.7/dist-packages')
import json
import internetarchive
import re
import time
from datetime import datetime
from transmission_rpc import Client,Torrent
import transmission_rpc
import requests
import argparse
#import pdb; pdb.set_trace()

BITTORRENT_USER = 'Admin'
BITTORRENT_PASSWORD = 'changeme'
DOWNLOAD_URL = 'https://archive.org/download'
MAP_CATALOG_URL = 'http://d.iiab.io/content/OSM/vector-tiles/map-catalog.json'
MAP_PREFIX = '/library/www/osm-vector-maps/viewer/tiles/'
bt_client = object
local_torrents = object
files_info = object
catalog = object

def get_catalog():
   catalog = {}
   #r = requests.get(MAP_CATALOG_URL)
   #if r.status_code == 200:
   with open('/etc/iiab/map-catalog.json','r') as filedesc:
      data= json.loads(filedesc.read())
      catalog.update(data['maps'])
      catalog.update(data['base'])
      return catalog
   return {}

def enough_space(key):
   total_size = catalog[key]['size']
   free_space = bt_client.free_space('/library')
   bytes,units = transmission_rpc.utils.format_size(free_space)
   required,req_units = transmission_rpc.utils.format_size(total_size + 500000000)
   if total_size > free_space + 500000000:
      print('Total free space on destination: %5.1f %s'%(bytes,units))
      print('Required free space on destination: %5.1f %s'%(required,req_units))
      print('There is not enough space to download %s maps'%key)
      sys.exit(1)
   
def get_local_torrent_files():
   global bt_client
   global local_torrents
   global files_info
   local_bts = []
   bt_client = Client(username=BITTORRENT_USER,password=BITTORRENT_PASSWORD)
   if not bt_client:
      print('Failed to connect to local transmission bittorrent kj daemon')
      sys.exit(1)
   local_torrents = bt_client.get_torrents()
   files_info = bt_client.get_files()
   '''
   for item in files_info.keys():
      print(str(item),str(files_info[item][0].name))
      #print('index: %2s  status: %8s file: %s'%(item,local_torrents[item-1].status,files_info[item][0].name.split('/')[0] ))
      pass
   
   for index in range(len(local_torrents)):
      tor = local_torrents[index]
      print('%s %s'%(tor.name,index))
   '''

def get_bittorrent_sizes(tor):
   files = tor.files()
   bytesCompleted = files[0].completed
   length = files[0].size
   return (bytesCompleted, length)

def get_torrent_index(key):
   torrent_index = -1
   for index in range(len(local_torrents)):
      fn = local_torrents[index].files()[0].name
      #print('local:%s  key: %s'%(fn,key))
      if fn.find(key) != -1: 
         torrent_index = index
   return torrent_index

def get_filelist_index_from_catalog_key(key):
   # returns -1 or id into files_info and local_torrents
   found_file_num = -1
   archive_name = '%s/%s'%(key,key)
   for file_num in files_info:
      if files_info[file_num][0].name == archive_name:
         found_file_num = file_num
   return found_file_num

def start_download(key):
   torrent_id = get_torrent_index(key)
   print('start download key:%s torrent_id:%s'%(key,torrent_id))
   if torrent_id == -1:
      print("Starting torrent for %s"%catalog[key]['detail_url'])
      bt_client.add_torrent(catalog[key]['bittorrent_url'],timeout=120)
   else:
      print('torrent_id: %s'%torrent_id)
      status = local_torrents[torrent_id].status
      print('Torrent for %s exists. Status:%s'%(key,status))
      if status == 'stopped'or status == 'paused':
         local_torrents[torrent_id].start()
         print("Status:%s Retarting torrent for %s"%(status,catalog[key]['detail_url']))

def show_download_progress():
   global local_torrents
   local_torrents = bt_client.get_torrents()
   PERIOD = 10
   last_bytes = {}
   #torrent_id = get_torrent_index(key)
   downloading = True
   start_period = time.time() - PERIOD
   while downloading:
      downloading = False
      for seq,key,title in map_key_list:
         torrent_index = get_torrent_index(key)
         tor = local_torrents[torrent_index]
         tor.update()
         if tor.progress == 100.0:
            continue 
         if tor.status == 'stopped' or tor.status == 'paused':
            continue
         downloading = True
         percent = tor.progress
         bytes_completed,bytes_total = get_bittorrent_sizes(tor)
         completed,units = transmission_rpc.utils.format_size(bytes_completed)
         total,tot_units = transmission_rpc.utils.format_size(bytes_total)
         eta = tor.format_eta()
         bytes_this_period = bytes_completed - last_bytes.get(tor.name,0)
         this_period = time.time() - start_period
         bytes_per_second = bytes_this_period / this_period
         bpsec,bpsec_units = transmission_rpc.utils.format_size(int(bytes_per_second))
         print('%4.0f%%  %4.1f%s/%3.1f%s  %4.1f%s/sec  %s %s'%(percent,completed,units,total,tot_units,bpsec,bpsec_units,eta,tor.name))
         if completed == total:
            print('%3.0f%% %3.1f %s/%3.1f %s   %s %s'%(percent,completed,units,total,tot_units,eta,tor.name))
            continue
         last_bytes[tor.name] = bytes_completed
         start_period = time.time()
         time.sleep(PERIOD)
   print('All active torrents are downloaded')

def parse_args():
    parser = argparse.ArgumentParser(description="Download OSM Bittorrent files.")
    parser.add_argument("-a","--all", help='Start downloading all Archive.org  maps.',action='store_true')
    parser.add_argument("-c","--catalog", help='List Map Catalog Index numbers and torrent info.',action='store_true')
    parser.add_argument("-g","--get", help='Download Map via Catalog key (MapID).')
    parser.add_argument("-i","--idx", help='Download Map via Index number from -c option above.')
    parser.add_argument("-l","--link", help='Make bittorrent files available to maps.',action='store_true')
    parser.add_argument("-p","--progress", help='Show progress of current bitTorrent downloads.',action='store_true')
    parser.add_argument("-t","--torrents", help='List status of local torrents.',action='store_true')
    parser.add_argument("-u","--upld", help='Max upload speed in KB. Set to 0 to disable uploading.')
    return parser.parse_args()

############# Action ##############
args = parse_args()
catalog = get_catalog()
get_local_torrent_files()

map_key_list = []
for key in catalog.keys():
   map_key_list.append((catalog[key]['seq'],key,catalog[key]['title']))
map_key_list = sorted(map_key_list)

if args.catalog:
   for seq,key,title in map_key_list:
      size = catalog[key]['size']
      cat_size,cat_units = transmission_rpc.utils.format_size(size)
      found_file_num = get_filelist_index_from_catalog_key(key)
      if found_file_num == -1:
         status = 'absent'
         file_name = catalog[key]['title']
         percent = 0.0
         num = 0
         units = ''
      else: 
         tor = None
         for torrent in local_torrents:
            if torrent.name == key:
               tor = torrent
         if tor:
            status = tor.status
            percent = tor.progress
            files = tor.files()
            bytesCompleted = files[0].completed
            length = tor._fields['totalSize'].value
            name = files[0].name.split('/')[0]
            num,units = transmission_rpc.utils.format_size(length)
         else:
            status = 'absent'
            percent = 0
            num = 0
            units = ''
         file_name = catalog[key]['title']
      print('Index: %2s  %4.1f %3s %3.0d%%  %4.1f %3s %8s Region: %s'%(seq,num,units,percent,cat_size,cat_units,status,file_name ))
      #print(catalog[key]['title'],catalog[key]['seq'])
   sys.exit(1)

   get_url = catalog[map_key_list[num]].get('bittorrent_url','')
   print('getting %s'%get_url)
   
if args.torrents:
   for tor in local_torrents:
      files = tor.files()
      #print(str(files))
      bytesCompleted = files[0].completed
      length = tor._fields['totalSize'].value
      name = files[0].name.split('/')[0]
      num,units = transmission_rpc.utils.format_size(length)
      print('%3.0f%% %5.1f %s %s'%(tor.progress,num,units,name))
   
if args.link:
   for tor in local_torrents:
      files = tor.files()
      #print(str(files))
      key = os.path.basename(files[0].name)
      filename = catalog.get(key,'')
      if filename == '':
         continue
      dest = MAP_PREFIX + key
      if os.path.exists(dest):
         continue
      src = '/library/transmission/' + key + '/' + key
      os.symlink(src,dest)      
      sys.exit(0)
   
if args.all:
   total_size = 0
   for map in catalog.keys():
      torrent_index = get_torrent_index(map)
      if torrent_index != -1:
         continue
      total_size += catalog[map]['size']
      free_space = bt_client.free_space('/library')
      bytes,units = transmission_rpc.utils.format_size(free_space)
      print('Total free space on destination: %5.1f %s'%(bytes,units))
   if total_size > free_space + 500000000:
      print('There is not enough space to download all maps')
      sys.exit(1)
   for key in catalog.keys():
      torrent_index = get_torrent_index(key)
      if torrent_index != -1:
         status = local_torrents[torrent_index].status
         #print(status)
         if status == 'stopped'or status == 'paused':
            local_torrents[torrent_index].start()
            print("Status:%s Retarting torrent for %s"%(status,catalog[key]['detail_url']))
         elif status == 'seeding':
            #print("torrent for %s is seeding"%key)
            pass
         elif status == 'downloading':
            #print("torrent for %s is dowloading"%key)
            pass
      else:
          print("Starting torrent for %s"%catalog[key]['bittorrent_url'])
          try:
               bt_client.add_torrent(catalog[key]['detail_url'],timeout=120)
          except:
               print('Failed to start %s'%catalog[key]['bittorrent_url'])

if args.idx:
   key = None
   for map in catalog.keys():   
      if args.idx == str(catalog[map]['seq']):
         key = map
   if key == None:
      print('The idx %s was not found. Did you use the index dispayed with the -c option?'%args.idx)
      sys.exit(1)
   enough_space(key)
   start_download(key)
   time.sleep(15)
   show_download_progress()
         
if args.get:
   key = catalog.get(args.get,'')
   if key == '':
      print('The catalog key %s was not found.'%args.get)
      print('See catelog source at http://download.iiab.io/content/OSM/vector-tiles/map-catalog.json')
      sys.exit(1)
   start_download(key)
   time.sleep(15)
   show_download_progress()
       
if args.progress:   
   show_download_progress()

if args.upld:
   bt_client.set_session(speed_limit_up=args.upld,speed_limit_up_enabled=True)
   # wait for transmission-daemon to process request
   #time.sleep(3)
   session = bt_client.get_session()
   speed_limit_up = session._fields['speed_limit_up'].value
   speed_limit_up_enabled = session._fields['speed_limit_up_enabled'].value
   print('\nUpload speed limit: %s KB. Limit enabled:%s\n'%(speed_limit_up, speed_limit_up_enabled,)) 
