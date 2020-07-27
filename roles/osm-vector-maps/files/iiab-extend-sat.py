#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# This instance of python_mbtiles/tile-dl.py was made specific to expand satellite
#  coverage -- with the mbtile class incorporated, rather than imported

# started from https://github.com/TimSC/pyMbTiles/blob/master/MBTiles.py

import sqlite3
import sys, os
import argparse
import certifi
import urllib3
import math
from geojson import Feature, Point, FeatureCollection, Polygon
import geojson
import shutil
import json
import time
import uuid
import io
import datetime
from PIL import Image
#import pdb; pdb.set_trace()

# GLOBALS
mbTiles = object
args = object
bounds = object
earth_circum = 40075.0 # in km
bbox_limits = {} # set by sat_bbox_limits, read by download
src = object
config = {}
config_fn = 'config.json'
total_tiles = 0
bad_ref = 0
sat_mbtile_fname = 'satellite_z0-z9_v3.mbtiles'
bound_string = ''

ATTRIBUTION = os.environ.get('METADATA_ATTRIBUTION', '<a href="http://openmaptiles.org/" target="_blank">&copy; OpenMapTiles</a> <a href="http://www.openstreetmap.org/about/" target="_blank">&copy; OpenStreetMap contributors</a>')
VERSION = os.environ.get('METADATA_VERSION', '3.3')

work_dir = '/library/working/maps'
osm_dir = '/library/www/osm-vector-maps/maplist/assets'
sat_dir = '/library/www/osm-vector-maps/viewer/tiles'

# Translates between lat/long and the slippy-map tile numbering scheme
# 
# http://wiki.openstreetmap.org/index.php/Slippy_map_tilenames
# https://svn.openstreetmap.org/applications/routing/pyroute/tilenames.py
# 
# Written by Oliver White, 2007
# This file is public-domain
#-------------------------------------------------------
from math import *

class Tools(object):
   def numTiles(self,z):
     return(pow(2,z))

   def sec(self,x):
     return(1/cos(x))

   def latlon2relativeXY(self,lat,lon):
     x = (lon + 180) / 360
     y = (1 - log(tan(radians(lat)) + self.sec(radians(lat))) / pi) / 2
     return(x,y)

   def latlon2xy(self,lat,lon,z):
     n = self.numTiles(z)
     x,y = self.latlon2relativeXY(lat,lon)
     return(n*x, n*y)
     
   def tileXY(self,lat, lon, z):
     x,y = self.latlon2xy(lat,lon,z)
     return(int(x),int(y))

   def xy2latlon(self,x,y,z):
     n = self.numTiles(z)
     relY = y / n
     lat = self.mercatorToLat(pi * (1 - 2 * relY))
     lon = -180.0 + 360.0 * x / n
     return(lat,lon)
     
   def latEdges(self,y,z):
     n = numTiles(z)
     unit = 1 / n
     relY1 = y * unit
     relY2 = relY1 + unit
     lat1 = self.mercatorToLat(pi * (1 - 2 * relY1))
     lat2 = self.mercatorToLat(pi * (1 - 2 * relY2))
     return(lat1,lat2)

   def lonEdges(self,x,z):
     n = numTiles(z)
     unit = 360 / n
     lon1 = -180 + x * unit
     lon2 = lon1 + unit
     return(lon1,lon2)
     
   def tileEdges(self,x,y,z):
     lat1,lat2 = latEdges(y,z)
     lon1,lon2 = lonEdges(x,z)
     return((lat2, lon1, lat1, lon2)) # S,W,N,E

   def mercatorToLat(self,mercatorY):
     return(degrees(atan(sinh(mercatorY))))

   def tileSizePixels(self):
     return(256)

   def tileLayerExt(self,layer):
     if(layer in ('oam')):
       return('jpg')
     return('png')

   def tileLayerBase(self,layer):
     layers = { \
       "tah": "http://cassini.toolserver.org:8080/http://a.tile.openstreetmap.org/+http://toolserver.org/~cmarqu/hill/",
      #"tah": "http://tah.openstreetmap.org/Tiles/tile/",
       "oam": "http://oam1.hypercube.telascience.org/tiles/1.0.0/openaerialmap-900913/",
       "mapnik": "http://tile.openstreetmap.org/mapnik/"
       }
     return(layers[layer])
     
   def tileURL(self,x,y,z,layer):
     return "%s%d/%d/%d.%s" % (self.tileLayerBase(layer),z,x,y,self.tileLayerExt(layer))

class MBTiles():
   def __init__(self, filename):
      self.conn = sqlite3.connect(filename)
      self.conn.row_factory = sqlite3.Row
      self.conn.text_factory = str
      self.c = self.conn.cursor()
      self.schemaReady = False
      self.bounds = {}

   def __del__(self):
      self.conn.commit()
      self.c.close()
      del self.conn

   def ListTiles(self):
      rows = self.c.execute("SELECT zoom_level, tile_column, tile_row FROM tiles")
      out = []
      for row in rows:
         out.append((row[0], row[1], row[2]))
      return out

   def GetTile(self, zoomLevel, tileColumn, tileRow):
      rows = self.c.execute("SELECT tile_data FROM tiles WHERE zoom_level = ? AND tile_column = ? AND tile_row = ?", 
         (zoomLevel, tileColumn, tileRow))
      rows = list(rows)
      if len(rows) == 0:
         raise RuntimeError("Tile not found")
      row = rows[0]
      return row[0]

   def CheckSchema(self):     
      sql = 'CREATE TABLE IF NOT EXISTS map (zoom_level INTEGER,tile_column INTEGER,tile_row INTEGER,tile_id TEXT,grid_id TEXT)'
      self.c.execute(sql)

      sql = 'CREATE TABLE IF NOT EXISTS images (tile_data blob,tile_id text)'
      self.c.execute(sql)

      sql = 'CREATE TABLE IF NOT EXISTS satdata (zoom_level INTEGER,name text,value text)'
      self.c.execute(sql)

      sql = 'CREATE VIEW IF NOT EXISTS tiles AS SELECT map.zoom_level AS zoom_level, map.tile_column AS tile_column, map.tile_row AS tile_row, images.tile_data AS tile_data FROM map JOIN images ON images.tile_id = map.tile_id'
      self.c.execute(sql)

      self.schemaReady = True

   def GetAllMetaData(self):
      rows = self.c.execute("SELECT name, value FROM metadata")
      out = {}
      for row in rows:
         out[row[0]] = row[1]
      return out

   def SetMetaData(self, name, value):
      if not self.schemaReady:
         self.CheckSchema()

      self.c.execute("UPDATE metadata SET value=? WHERE name=?", (value, name))
      if self.c.rowcount == 0:
         self.c.execute("INSERT INTO metadata (name, value) VALUES (?, ?);", (name, value))

      self.conn.commit()

   def DeleteMetaData(self, name):
      if not self.schemaReady:
         self.CheckSchema()

      self.c.execute("DELETE FROM metadata WHERE name = ?", (name,))
      self.conn.commit()
      if self.c.rowcount == 0:
         raise RuntimeError("Metadata name not found")

   def SetSatMetaData(self, zoomLevel, name, value):
      if not self.schemaReady:
         self.CheckSchema()

      self.c.execute("UPDATE satdata SET value=? WHERE zoom_level=? AND name = ?", (value, zoomLevel, name))
      if self.c.rowcount == 0:
         self.c.execute("INSERT INTO satdata (zoom_level, name, value) VALUES (?, ?, ?);", (zoomLevel, name, value))

      self.conn.commit()

   def GetSatMetaData(self,zoomLevel):
      rows = self.c.execute("SELECT name, value FROM satdata WHERE zoom_level = ?",(str(zoomLevel),))
      out = {}
      for row in rows:
         out[row[0]] = row[1]
      return out

   def DeleteSatData(self, zoomLevel, name):
      if not self.schemaReady:
         self.CheckSchema()

      self.c.execute("DELETE FROM satdata WHERE name = ? AND zoom_level = ?", (zoomLevel, name,))
      self.conn.commit()
      if self.c.rowcount == 0:
         raise RuntimeError("SatData name %s not found"%name)

   def SetTile(self, zoomLevel, tileColumn, tileRow, data):
      if not self.schemaReady:
         self.CheckSchema()

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
      if not self.schemaReady:
         self.CheckSchema()

      tile_id = self.TileExists(zoomLevel, tileColumn, tileRow)
      if not tile_id:
         raise RuntimeError("Tile not found")

      self.c.execute("DELETE FROM images WHERE tile_id = ?;",tile_id) 
      self.c.execute("DELETE FROM map WHERE tile_id = ?;",tile_id) 
      self.conn.commit()

   def TileExists(self, zoomLevel, tileColumn, tileRow):
      if not self.schemaReady:
         self.CheckSchema()

      sql = 'select tile_id from map where zoom_level = ? and tile_column = ? and tile_row = ?'
      self.c.execute(sql,(zoomLevel, tileColumn, tileRow))
      row = self.c.fetchall()
      if len(row) == 0:
         return None
      return str(row[0][0])

   def DownloadTile(self, zoomLevel, tileColumn, tileRow, lock):
      # if the tile already exists, do nothing
      lock.acquire()
      tile_id = self.TileExists(zoomLevel, tileColumn, tileRow)
      lock.release()
      if tile_id:
         #print('tile already exists -- skipping')
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

   def get_bounds(self):
     sql = 'select zoom_level, min(tile_column),max(tile_column),min(tile_row),max(tile_row), count(zoom_level) from tiles group by zoom_level;'
     resp = self.c.execute(sql)
     rows = resp.fetchall()
     for row in rows:
         self.bounds[row['zoom_level']] = { 'minX': row['min(tile_column)'],\
                                  'maxX': row['max(tile_column)'],\
                                  'minY': row['min(tile_row)'],\
                                  'maxY': row['max(tile_row)'],\
                                  'count': row['count(zoom_level)'],\
                                 }
     outstr = json.dumps(self.bounds,indent=2)
     # diagnostic info
     with open('/tmp/bounds.json','w') as bounds_fp:
        bounds_fp.write(outstr)
     return self.bounds

   def summarize(self):
     sql = 'select zoom_level, min(tile_column),max(tile_column),min(tile_row),max(tile_row), count(zoom_level) from tiles group by zoom_level;'
     self.c.execute(sql)
     rows = self.c.fetchall()
     print('Zoom Levels Found:%s'%len(rows))
     for row in rows:
       if row[2] != None and row[1] != None and row[3] != None and row[4] != None:
         print('%s %s %s %s %s %s %s'%(row[0],row[1],row[2],row[3],row[4],\
              row[5], (row[2]-row[1]+1) * ( row[4]-row[3]+1)))
         self.SetSatMetaData(row[0],'minX',row[1])
         self.SetSatMetaData(row[0],'maxX',row[2])
         self.SetSatMetaData(row[0],'minY',row[3])
         self.SetSatMetaData(row[0],'maxY',row[4])
         self.SetSatMetaData(row[0],'count',row[5])
         
         
  
   def CountTiles(self,zoom):
      self.c.execute("select tile_data from tiles where zoom_level = ?",(zoom,))
      num = 0
      while self.c.fetchone():
         num += 1 
      return num

   def execute_script(self,script):
      self.c.executescript(script)

   def copy_zoom(self,zoom,src):
      sql = 'ATTACH DATABASE "%s" as src'%src
      self.c.execute(sql)
      sql = 'INSERT INTO map SELECT * from src.map where src.map.zoom_level=?'
      self.c.execute(sql,[zoom])
      sql = 'INSERT OR IGNORE INTO images SELECT src.images.tile_data, src.images.tile_id from src.images JOIN src.map ON src.map.tile_id = src.images.tile_id where map.zoom_level=?'
      self.c.execute(sql,[zoom])
      sql = 'DETACH DATABASE src'
      self.c.execute(sql)

   def copy_mbtile(self,src):
      sql = 'ATTACH DATABASE "%s" as src'%src
      self.c.execute(sql)
      sql = 'INSERT INTO map SELECT * from src.map where true'
      self.c.execute(sql,[zoom])
      sql = 'INSERT OR IGNORE INTO images SELECT src.images.tile_data, src.images.tile_id from src.images JOIN src.map ON src.map.tile_id = src.images.tile_id where true'
      self.c.execute(sql,[zoom])
      sql = 'DETACH DATABASE src'
      self.c.execute(sql)

   def delete_zoom(self,zoom):
      sql = 'DELETE FROM images where tile_id in (SELECT tile_id from map WHERE map.zoom_level=?)'
      self.c.execute(sql,[zoom])
      sql = 'DELETE FROM map where zoom_level=?'
      self.c.execute(sql,[zoom])
      sql = "vacuum"
      self.c.execute(sql)
      self.Commit()

   def create_sat_info(self):
      sql = '''CREATE TABLE IF NOT EXISTS satellite_info (
               perma_ref TEXT, bounds TEXT, coordinates TEXT,
               date_downloaded TEXT, tiles_downloaded INTEGER,
               command_line TEXT, magic_number INTEGER,
               min_zoom INTEGER, max_zoom INTEGER
      )''' 
      self.c.execute(sql)
      self.Commit()

   def insert_sat_info(self,perma_ref,bounds,coordinates,date_downloaded,
                       tiles_downloaded,command_line,magic_number,
                       min_zoom,max_zoom):
      sql = '''insert into satellite_info (perma_ref,bounds,coordinates,
               date_downloaded,tiles_downloaded,command_line,
               magic_number,min_zoom,max_zoom) values (?,?,?,?,?,?,?,?,?)'''
      self.c.execute(sql,(perma_ref,bounds,coordinates,date_downloaded,
                     tiles_downloaded,command_line,magic_number,min_zoom,max_zoom,))
      self.Commit()

class WMTS(object):

   def __init__(self, template):
      self.template = template
      self.http = urllib3.PoolManager(cert_reqs='CERT_REQUIRED',\
           ca_certs=certifi.where())

   def get(self,z,x,y):
      srcurl = "%s"%self.template
      srcurl = srcurl.replace('{z}',str(z))
      srcurl = srcurl.replace('{x}',str(x))
      srcurl = srcurl.replace('{y}',str(y))
      #print(srcurl[-50:])
      resp = (self.http.request("GET",srcurl,retries=10))
      return(resp)
      
def parse_args():
    parser = argparse.ArgumentParser(description="Download WMTS tiles arount a point.")
    parser.add_argument('-z',"--zoom", help="zoom level", type=int)
    parser.add_argument("-m", "--mbtiles", help="mbtiles filename.")
    parser.add_argument("-v", "--verify", help="verify mbtiles.",action='store_true')
    parser.add_argument("-f", "--fix", help="fix invalid tiles.",action='store_true')
    parser.add_argument("-n", "--name", help="Output filename.")
    parser.add_argument("--lat", help="Latitude degrees.",type=float)
    parser.add_argument("--lon", help="Longitude degrees.",type=float)
    parser.add_argument("-r","--radius", help="Download within this radius(km).",type=float)
    parser.add_argument("-g", "--get", help='get WMTS tiles from this URL(Default: Sentinel Cloudless).')
    parser.add_argument("-s", "--summarize", help="Data about each zoom level.",action="store_true")
    return parser.parse_args()

class Extract(object):

    def __init__(self, extract, country, city, top, left, bottom, right,
                 min_zoom=0, max_zoom=14, center_zoom=10):
        self.extract = extract
        self.country = country
        self.city = city

        self.min_lon = left
        self.min_lat = bottom
        self.max_lon = right
        self.max_lat = top

        self.min_zoom = min_zoom
        self.max_zoom = max_zoom
        self.center_zoom = center_zoom

    def bounds(self):
        return '{},{},{},{}'.format(self.min_lon, self.min_lat,
                                    self.max_lon, self.max_lat)

    def center(self):
        center_lon = (self.min_lon + self.max_lon) / 2.0
        center_lat = (self.min_lat + self.max_lat) / 2.0
        return '{},{},{}'.format(center_lon, center_lat, self.center_zoom)

    def metadata(self, extract_file):
        return {
            "type": os.environ.get('METADATA_TYPE', 'baselayer'),
            "attribution": ATTRIBUTION,
            "version": VERSION,
            "minzoom": self.min_zoom,
            "maxzoom": self.max_zoom,
            "name": os.environ.get('METADATA_NAME', 'OpenMapTiles'),
            "id": os.environ.get('METADATA_ID', 'openmaptiles'),
            "description": os.environ.get('METADATA_DESC', "Extract from http://openmaptiles.org"),
            "bounds": self.bounds(),
            "center": self.center(),
            "basename": os.path.basename(extract_file),
            "filesize": os.path.getsize(extract_file)
        }

def dhms_from_seconds(s):
   """ translate seconds into days, hour, minutes """
   days, remainder = divmod(s, 86400)
   hours, remainder = divmod(remainder, 3600)
   minutes, remainder = divmod(remainder, 60)
   seconds, remainder = divmod(remainder, 60)
   return (days, hours, minutes, seconds)

def debug_one_tile():
   if not args.x:
      args.x = 3
      args.y = 0
      args.zoom = 2
   
   global src # the opened url for satellite images
   try:
      src = WMTS(url)
   except:
      print('failed to open source')
      sys.exit(1)
   response = src.get(args.zoom,args.x,args.y)
   print(response.status) 
   print(len(response.data))
   print(response.data)
      
      
   
def put_config():
   global config
   with open(config_fn,'w') as cf:
     cf.write(json.dumps(config,indent=2))
 
def get_config():
   global config
   if not os.path.exists(config_fn):
      put_config()

   with open(config_fn,'r') as cf:
     config = json.loads(cf.read())
    
def human_readable(num):
    # return 3 significant digits and unit specifier
    num = float(num)
    units = [ '','K','M','G']
    for i in range(4):
        if num<10.0:
            return "%.2f%s"%(num,units[i])
        if num<100.0:
            return "%.1f%s"%(num,units[i])
        if num < 1000.0:
            return "%.0f%s"%(num,units[i])
        num /= 1000.0

def get_bounds(lat_deg,lon_deg,radius_km,zoom=13):
   n = 2.0 ** zoom
   tile_kmeters = earth_circum / n
   #print('tile dim(km):%s'%tile_kmeters)
   per_pixel = tile_kmeters / 256 * 1000
   #print('%s meters per pixel'%per_pixel)
   tileX,tileY = coordinates2WmtsTilesNumbers(lat_deg,lon_deg,zoom)
   tile_radius = radius_km / tile_kmeters
   minX = int(tileX - tile_radius) 
   maxX = int(tileX + tile_radius + 1) 
   minY = int(tileY - tile_radius) 
   maxY = int(tileY + tile_radius + 1) 
   return (minX,maxX,minY,maxY)

def record_bbox_debug_info():
   global bbox_limits
   cur_box = regions[region]
   for zoom in range(bbox_zoom_start-1,14):
      xmin,xmax,ymin,ymax = bbox_tile_limits(cur_box['west'],cur_box['south'],\
            cur_box['east'],cur_box['north'],zoom)
      #print(xmin,xmax,ymin,ymax,zoom)
      tot_tiles = mbTiles.CountTiles(zoom)
      bbox_limits[zoom] = { 'minX': xmin,'maxX':xmax,'minY':ymin,'maxY':ymax,                              'count':tot_tiles}
   with open('/tmp/bbox_limits','w') as fp:
      fp.write(json.dumps(bbox_limits,indent=2))

def get_degree_extent(lat_deg,lon_deg,radius_km,zoom=13):
   (minX,maxX,minY,maxY) = get_bounds(lat_deg,lon_deg,radius_km,zoom)
   print('minX:%s,maxX:%s,minY:%s,maxY:%s'%(minX,maxX,minY,maxY))
   # following function returns (y,x)
   north_west_point = xytools.xy2latlon(minX,minY,zoom)
   south_east_point = xytools.xy2latlon(maxX+1,maxY+1,zoom)
   print('north_west:%s south_east:%s'%(north_west_point, south_east_point))
   # returns (west, south, east, north)
   return (north_west_point[1],south_east_point[0],south_east_point[1],north_west_point[0])
  

def coordinates2WmtsTilesNumbers(lat_deg, lon_deg, zoom):
  lat_rad = math.radians(lat_deg)
  n = 2.0 ** zoom
  xtile = int((lon_deg + 180.0) / 360.0 * n)
  ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
  return (xtile, ytile)

def sat_bboxes(lat_deg,lon_deg,zoom,radius):
   global bound_string,poly,magic_number
   # Adds a bounding box for the current location, radius
   magic_number = int(lat_deg * lon_deg * radius)
   bboxes = osm_dir + "/bboxes.geojson"
   with open(bboxes,"r") as bounding_geojson:
      data = geojson.load(bounding_geojson)
      #feature_collection = FeatureCollection(data['features'])
      magic_number_found = False
      for feature in data['features']:
         if feature['properties'].get('magic_number') == magic_number:
            magic_number_found = True
   features = [] 
   (west, south, east, north) = get_degree_extent(lat_deg,lon_deg,radius,zoom)
   print('west:%s, south:%s, east:%s, north:%s'%(west, south, east, north))
   west=float(west)
   south=float(south)
   east=float(east)
   north=float(north)
   bound_string = "%s,%s,%s,%s"%(west,south,east,north)
   poly = Polygon([[[west,south],[east,south],[east,north],[west,north],[west,south]]])
   if not magic_number_found:
      data['features'].append(Feature(geometry=poly,properties={"name":'satellite',\
                           "magic_number":magic_number}))

   collection = FeatureCollection(data['features'])
   bboxes = osm_dir + "/bboxes.geojson"
   with open(bboxes,"w") as bounding_geojson:
      outstr = geojson.dumps(collection, indent=2)
      bounding_geojson.write(outstr)

def create_clone():
   global mbTiles
   global bad_ref
   global src
   # Open a WMTS source
   try:
      src = WMTS(url)
   except:
      print('failed to open WMTS source in scan_verify')
      sys.exit(1)
   
   # copy the source into a work directory, then do in place substitution
   set_up_target_db('fix_try')
   bad_ref = open('/tmp/bad_tiles','w')


def scan_verify():
   global src # the opened url for satellite images
   if args.fix:
      create_clone()
   replaced = bad = ok = empty = html = unfixable = 0
   mbTiles = MBTiles(args.mbtiles)
   print('Opening database %s'%args.mbtiles)
   for zoom in sorted(bounds.keys()):
      #if zoom == 5: sys.exit()
      bad = ok = empty = html = 0
      for tileY in range(bounds[zoom]['minY'],bounds[zoom]['maxY'] + 1):
         #print("New Y:%s on zoom:%s"%(tileY,zoom))
         for tileX in range(bounds[zoom]['minX'],bounds[zoom]['maxX'] + 1):
               #print('tileX:%s'%tileX)
               replace = False
               raw = mbTiles.GetTile(zoom, tileX, tileY)
               try:
                  image = Image.open(io.StringIO(raw))
                  ok += 1
                  if len(raw) < 800: 
                     replace=True
                  else:
                     continue
               except Exception as e:
                  bad += 1
                  replace = True
                  line = bytearray(raw)
                  if line.find("DOCTYPE") != -1:
                     html +=1
                  if args.fix and replace:
                        success = replace_tile(src,zoom,tileX,tileY)
                        if success:
                           bad_ref.write('%s,%s,%s\n'%(zoom,tileX,tileY))
                           replaced += 1
                        else:
                           bad_ref.write('%s,%s,%s\n'%(zoom,tileX,tileY))
                           unfixable += 1
                        if tileY % 20 == 0:
                           print('replaced:%s  ok:%s'%(replaced,ok))
      print( 'bad',bad,'ok',ok, 'empty',empty,'html',html, 'unfixable',unfixable,'zoom',zoom,'replaced',replaced)
   print ('bad',bad,'ok',ok, 'empty',empty,'html',html, 'unfixable',unfixable)
   if args.fix:
      bad_ref.close()
   
def replace_tile(src,zoom,tileX,tileY):
   global total_tiles
   try:
      r = src.get(zoom,tileX,tileY)
   except Exception as e:
      print(str(e))
      sys.exit(1)
   if r.status == 200:
      raw = r.data
      line = bytearray(raw)
      if line.find(b"DOCTYPE") != -1:
         print('Sentinel Cloudless returned text rather than an image ')
         return False
      else:
         try:
            #image = Image.open(io.StringIO(raw))
            image = Image.open(io.BytesIO(raw))
            total_tiles += 1
            #image.show(io.StringIO(raw))
         except Exception as e:
            print('exception:%s'%e)
            sys.exit()
         #raw_input("PRESS ENTER")
         mbTiles.SetTile(zoom, tileX, tileY, r.data)
         returned = mbTiles.GetTile(zoom, tileX, tileY)
         if bytearray(returned) != r.data:
            print('read verify in replace_tile failed')
            return False
         return True
   else:
      print('get url in replace_tile returned:%s'%r.status)
      return False

def download_tiles(src,lat_deg,lon_deg,zoom,radius):
   global mbTiles, ok
   global total_tiles
   global start
   tileX_min,tileX_max,tileY_min,tileY_max = get_bounds(lat_deg,lon_deg,radius,zoom)
   for tileX in range(tileX_min,tileX_max+1):
      for tileY in range(tileY_min,tileY_max+1):
         if (start - time.time()) % 10 == 0:
            print('tileX:%s tileY:%s zoom:%s added:%s'%(tileX,tileY,zoom,total_tiles))
         tile_exists =  mbTiles.TileExists(zoom,tileX,tileY)
         if tile_exists:
            raw = mbTiles.GetTile(zoom, tileX, tileY)
            try:
               image = Image.open(io.StringIO(raw))
               ok += 1
               if len(raw) > 800: 
                  continue
            except Exception as e:
               pass
         replace_tile(src,zoom,tileX,tileY)

def set_up_target_db(name='sentinel'):
   global mbTiles
   global work_dir
   mbTiles = None

   # attach to the correct output database
   dbname = sat_mbtile_fname
   if not os.path.isdir(work_dir):
      #os.mkdir('./work')
      work_dir = '/tmp'
   dbpath = '%s/%s'%(work_dir,dbname)
   if not os.path.exists(dbpath):
   #if True:
      shutil.copyfile('%s/%s'%(sat_dir,sat_mbtile_fname),dbpath) 
   mbTiles = MBTiles(dbpath)
   mbTiles.CheckSchema()
   mbTiles.get_bounds()
   config['last_db'] = dbpath
   put_config()
   print("Destination Database opened successfully:%s"%dbpath)

def record_satellite_info():
   sat_bboxes(args.lat,args.lon,args.zoom,args.radius)
   mbTiles.create_sat_info()
   perma_ref = 'satellite_z0'
   coordinates = str(poly)
   tiles_downloaded = int(total_tiles)
   min_zoom = args.zoom
   max_zoom = 13
   command_line = ''
   date_downloaded = str(datetime.date.today())
   for nibble in sys.argv:
      command_line += nibble + ' '
   bounds_string = str(bounds)
   mbTiles.insert_sat_info(perma_ref,bounds_string,coordinates,date_downloaded,
                       tiles_downloaded,command_line,magic_number,
                       min_zoom,max_zoom)

def do_downloads():
   # Open a WMTS source
   global src # the opened url for satellite images
   global start, bound_string
   global total_tiles
   try:
      src = WMTS(url)
   except:
      print('failed to open source')
      sys.exit(1)
   set_up_target_db(args.name)
   start = time.time()
   for zoom in range(args.zoom,14):
      print("new zoom level:%s"%zoom)
      download_tiles(src,args.lat,args.lon,zoom,args.radius)
   seconds =(time.time()-start)
   d,h,m,s = dhms_from_seconds(seconds)
   print('Total time:%2.0f hrs:%2.0f min:%2.0f sec Duplicates:%s Total_tiles Added:%s'%(h,m,s,ok,total_tiles))
   record_satellite_info()

def main():
   global args
   global mbTiles
   global url
   global bounds
   global xytools
   xytools = Tools()
   args = parse_args()
   # Default to standard source
   if not os.path.isdir('./work'):
      os.mkdir('./work')
   if not args.mbtiles:
      args.mbtiles = sat_dir +'/' + sat_mbtile_fname
   print('mbtiles SOURCE filename:%s'%args.mbtiles)
   if os.path.isfile(args.mbtiles):
      mbTiles  = MBTiles(args.mbtiles)
      bounds = mbTiles.get_bounds()
   else:
      print('Failed to open %s -- Quitting'%args.mbtiles)
      sys.exit()
   if  args.get != None:
      print('get specified')
      url = args.get
   else:
      url =  "https://tiles.maps.eox.at/wmts?layer=s2cloudless-2018_3857&style=default&tilematrixset=g&Service=WMTS&Request=GetTile&Version=1.0.0&Format=image%2Fjpeg&TileMatrix={z}&TileCol={x}&TileRow={y}"
   if args.summarize:
      mbTiles.summarize()
      sys.exit(0)
   if args.verify:
      scan_verify()
      sys.exit(0)
   if not args.lon and not args.lat:
      args.lon = -122.14 
      args.lat = 37.46
   if not args.zoom:
      args.zoom = 10
   if not args.radius:
      args.radius = 15
   if not args.name:
      args.name = 'avni'
   if not args.lon and not args.lat:
      args.lon = -122.14 
      args.lat = 37.46
   #print('inputs to tileXY: lat:%s lon:%s zoom:%s'%(args.lat,args.lon,args.zoom))
   args.x,args.y = xytools.tileXY(args.lat,args.lon,args.zoom)

   do_downloads() 

   # save input for debugging in /tmp
   shutil.copy('%s/%s'%(sat_dir,sat_mbtile_fname),'/tmp/%s'%(sat_mbtile_fname)) 
   os.replace('%s/%s'%(work_dir,sat_mbtile_fname),'%s/%s'%(sat_dir,sat_mbtile_fname)) 

if __name__ == "__main__":
    # Run the main routine
   main()
