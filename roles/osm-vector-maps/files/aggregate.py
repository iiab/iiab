#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# Assemble an output mbtiles database from multiple input sources (perhaps from openmaptiles.org)

# help from https://github.com/TimSC/pyMbTiles/blob/master/MBTiles.py

import sqlite3
import sys, os
import argparse
#import curses
#import urllib3
import wget
#import certifi
#import tools
import subprocess
import json
#import math
import uuid
import shutil
#from multiprocessing import Process, Lock
import time
import hashlib
import glob

# GLOBALS
args = object
mbTiles = object
viewer_path = '/library/www/osm-vector-maps/viewer'
input_dir_path = '/library/working/maps'
base_file = 'osm.mbtiles'
base_filename = 'osm-planet_z0-z10_2017.mbtiles'
sat_file = 'satellite.mbtiles'
sat_filename = 'satellite_z0-z9_v3.mbtiles'
internetarchive_url = 'http://10.10.123.13/internetarchive'
region_path = '/etc/iiab'
regions_json = {}
init = {}

class MBTiles():
   def __init__(self, filename):
      self.conn = sqlite3.connect(filename)
      self.conn.row_factory = sqlite3.Row
      self.conn.text_factory = str
      self.c = self.conn.cursor()

   def __del__(self):
      self.conn.commit()
      self.c.close()
      del self.conn

   def GetTile(self, zoomLevel, tileColumn, tileRow):
      rows = self.c.execute("SELECT tile_data FROM tiles WHERE zoom_level = ? AND tile_column = ? AND tile_row = ?", 
         (zoomLevel, tileColumn, tileRow))
      rows = list(rows)
      if len(rows) == 0:
         raise RuntimeError("Tile not found")
      row = rows[0]
      return row[0]

   def GetAllMetaData(self):
      rows = self.c.execute("SELECT name, value FROM metadata")
      out = {}
      for row in rows:
         out[row[0]] = row[1]
      return out

   def SetMetaData(self, name, value):
      self.c.execute("UPDATE metadata SET value=? WHERE name=?", (value, name))
      if self.c.rowcount == 0:
         self.c.execute("INSERT INTO metadata (name, value) VALUES (?, ?);", (name, value))

      self.conn.commit()

   def DeleteMetaData(self, name):
      self.c.execute("DELETE FROM metadata WHERE name = ?", (name,))
      self.conn.commit()
      if self.c.rowcount == 0:
         raise RuntimeError("Metadata name not found")

   def SetTile(self, zoomLevel, tileColumn, tileRow, data):
      tile_id = self.TileExists(zoomLevel, tileColumn, tileRow)
      if tile_id: 
         tile_id = uuid.uuid4().hex
         operation = 'update images'
         self.c.execute("DELETE FROM images  WHERE tile_id = ?;", ([tile_id]))
         self.c.execute("INSERT INTO images (tile_data,tile_id) VALUES ( ?, ?);", (sqlite3.Binary(data),tile_id))
         if self.c.rowcount != 1:
            raise RuntimeError("Failure %s RowCount:%s"%(operation,self.c.rowcount))
         self.c.execute("""UPDATE map SET tile_id=? where zoom_level = ? AND 
               tile_column = ? AND tile_row = ?;""", 
            (tile_id, zoomLevel, tileColumn, tileRow))
         if self.c.rowcount != 1:
            raise RuntimeError("Failure %s RowCount:%s"%(operation,self.c.rowcount))
         self.conn.commit()
         return
      else: # this is not an update
         tile_id = uuid.uuid4().hex
         self.c.execute("INSERT INTO images ( tile_data,tile_id) VALUES ( ?, ?);", (sqlite3.Binary(data),tile_id))
         if self.c.rowcount != 1:
            raise RuntimeError("Insert image failure")
         operation = 'insert into map'
         self.c.execute("INSERT INTO map (zoom_level, tile_column, tile_row, tile_id) VALUES (?, ?, ?, ?);", 
            (zoomLevel, tileColumn, tileRow, tile_id))
      if self.c.rowcount != 1:
         raise RuntimeError("Failure %s RowCount:%s"%(operation,self.c.rowcount))
      self.conn.commit()
   

   def DeleteTile(self, zoomLevel, tileColumn, tileRow):
      tile_id = self.TileExists(zoomLevel, tileColumn, tileRow)
      if not tile_id:
         return
      try:
         self.c.execute("DELETE FROM images WHERE tile_id = ?;",(tile_id,)) 
      except:
         pass
      try:
         self.c.execute("DELETE FROM map WHERE tile_id = ?;",(tile_id,)) 
      except:
         pass
      self.conn.commit()

   def TileExists(self, zoomLevel, tileColumn, tileRow):
      sql = 'select tile_id from map where zoom_level = ? and tile_column = ? and tile_row = ?'
      self.c.execute(sql,(zoomLevel, tileColumn, tileRow))
      row = self.c.fetchall()
      if len(row) == 0:
         return None
      return str(row[0][0])

   def DownloadTile(self, zoomLevel, tileColumn, tileRow, lock):
      # if the tile already exists, do nothing
      tile_id = self.TileExists(zoomLevel, tileColumn, tileRow)
      if tile_id:
         print('tile already exists -- skipping')
         return 
      try:
         #wmts_row = int(2 ** zoomLevel - tileRow - 1)
         r = src.get(zoomLevel,tileColumn,tileRow)
      except Exception as e:
         raise RuntimeError("Source data failure;%s"%e)
         
      if r.status == 200:
         lock.acquire()
         self.SetTile(zoomLevel, tileColumn, tileRow, r.data)
         self.conn.commit()
         lock.release()
      else:
         print('Sat data error, returned:%s'%r.status)

   def Commit(self):
      self.conn.commit()


def get_url_to_disk(src,dest):
   if os.path.isfile(dest):
      # We might want to check md5 for possible change
      return
   try:
      print("Downloading %s"%src)
      wget.download(src,dest)
   except Exception as e:
      print('failed to open %s. Error: %s'%(src,e,))
      sys.exit(1)

def parse_args():
    parser = argparse.ArgumentParser(description="Assemble Resources for Maps.")
    parser.add_argument("region", help="Looked up in regions.json")
    parser.add_argument("-m", "--mbtiles", help="mbtiles filename.")
    parser.add_argument('-r',"--remove", help="Tiles below this zoom from MBTILES", type=int)
    return parser.parse_args()

def chop_zoom_and_below(max_to_chop):
   # chop a copied database
   if not args.mbtiles:
      print("Pliease specify sqlite database to chop with -m option")
      sys.exit(1)
   if not os.path.isfile(args.mbtiles):
      print("Failed to open %s"%args.mbtiles)
      sys.exit(1)
   dbname = './work/%s'%os.path.basename(args.mbtiles)
   shutil.copy(args.mbtiles,dbname)
   # open the database  
   db = MBTiles(dbname)
   sql = 'select * from map where zoom_level < ?'
   db.c.execute(sql,(max_to_chop,))
   rows = db.c.fetchall()
   for row in rows:
      try:
         db.DeleteTile(row['zoom_level'],row['tile_column'],row['tile_row'])
      except Exception as e:
         print('DeleteTile in chop_xoom error:%s'%e)
         sys.exit(1)
   print('vacumming database')
   db.c.execute('vacuum')
   db.Commit()
   
def get_regions():
   global regions_json
   # error out if environment is missing

   REGION_INFO = '%s/regions.json'%region_path
   with open(REGION_INFO,'r') as region_fp:
      try:
         data = json.loads(region_fp.read())
         regions_json = data['regions']
      except:
         print("regions.json parse error")
         sys.exit(1)
   
def sec2hms(n):
    days = n // (24 * 3600) 
  
    n = n % (24 * 3600) 
    hours = n // 3600
  
    n %= 3600
    minutes = n // 60
  
    n %= 60
    seconds = n 
    return '%s days, %s hours, %s minutes %2.1f seconds'%(days,hours,minutes,seconds)

def copy_if_new(src,dest):
   src_db = MBTiles(src)
   dest_db = MBTiles(dest)
   #for zoom in range(0,14):
   for zoom in range(0,3):
      sql = "SELECT * from tiles where zoom_level = ?"
      src_db.c = src_db.c.execute(sql,(zoom,))
      while True:
         rows = src_db.c.fetchmany(100)
         if not rows: break
         for row in rows:
            dest_db.SetTile(row['zoom_level'],row['tile_column'],\
               row['tile_row'],row['tile_data'])
  
def get_src_list(selected):
   get_regions()
   file_list = [base_filename]
   file_list.append(regions[selected]['url'])
   file_list.append(regions[selected]['sat_url'])
   return(file_list)

 
def init_dest(dest_path):
   if not os.path.isfile(dest_path):
      subprocess.run('./create_empty_mbtiles.sh {}'.format(dest_path),shell=True)
input_list = ['/library/working/maps/osm_z0-z5.mbtiles']

def main():
   global args
   global mbTiles
   global start_time
   start_time = time.time()
   if not os.path.isdir('./work'):
      os.mkdir('./work')
   
   args = parse_args()
   # The --remove option uses MBTiles class to truncate bottom of tile pyramid.
   if args.remove:
      print("removing below %s"%args.remove)
      chop_zoom_and_below(args.remove)
      sys.exit(1)

   # Fetch the files required for all maps
   src = os.path.join(internetarchive_url,base_filename)
   dest = os.path.join(viewer_path,base_filename)
   print(repr(src), repr(dest))
   get_url_to_disk(src,dest)

   src = os.path.join(internetarchive_url,sat_filename)
   dest = os.path.join(viewer_path,sat_filename)
   get_url_to_disk(src,dest)

   src = '%s/%s'%(viewer_path,base_filename)
   dest = '%s/%s'%(viewer_path,'base.mbtiles')
   if os.path.islink(dest):
      os.unlink(dest)
   os.symlink(src,dest)
   src = '%s/%s'%(viewer_path,sat_filename)
   dest = '%s/%s'%(viewer_path,'satellite.mbtiles')
   if os.path.islink(dest):
      os.unlink(dest)
   os.symlink(src,dest)
   
   get_regions()
   if not args.region in regions_json.keys():
      print('Region not found: %s'%args.region)
      sys.exit(1)

   src = os.path.join(internetarchive_url,regions_json[args.region]['detail_url'])
   dest = os.path.join(viewer_path,regions_json[args.region]['detail_url'])
   get_url_to_disk(src,dest)

   src = '%s/%s'%(viewer_path,regions_json[args.region]['detail_url'])
   dest = '%s/%s'%(viewer_path,'detail.mbtiles')
   if os.path.islink(dest):
      os.unlink(dest)
   os.symlink(src,dest)

   # now see if satellite needs updating
   #dest = viewer_path + '/' + sat_file
   #init_dest(dest)
   time.sleep(2)
   elapsed = time.time() - start_time
   print(sec2hms(elapsed))
   
if __name__ == "__main__":
    # Run the main routine
   main()
