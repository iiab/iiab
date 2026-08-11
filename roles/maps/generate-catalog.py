#!/usr/bin/python3
import requests, jinja2, json, yaml

import os
os.chdir(os.path.dirname(__file__))

iiab_map_host_url = "https://iiab.switnet.org/maps/2"

# "data dates" refer to how recent a certain type of data is

maps_vector_data_date = "2026-07-01"
maps_satellite_data_date = "2025-12-10"
maps_static_search_data_date = "2026-04-22"

# `maps_slow_data_date` is for data that changes rarely if ever
# naturalearth, naturalearth6, terrain, nominatim search [for now!]
maps_slow_data_date = "2025-12-10"

# The order that makes sense for explanation in this file may not make as much
# sense in the generated file. So here, we can reorder it before it gets generated.
def dict_with_order(d, ordered_keys):
    assert set(d.keys()) == set(ordered_keys), (d.keys(), ordered_keys)
    return {key: d[key] for key in ordered_keys}

def json_comment(s):
    "Take a multi-line string and return a list of strings that is formatted nicely for json."

    assert '"' not in s, f"remove the double quotation mark (escaping it looks ugly) from:\n\n{s}"

    lines = [line.strip() for line in s.strip().split('\n')]
    longest_line = max(len(line) for line in lines)
    return [
        # Space before the line, and enough spaces after the line to make all
        # of them uniform, with a space after the longest line.

        " " + line + " " * (longest_line + 1 - len(line))
        for line in lines
    ]

maps_dot_black_vector_tiles = dict_with_order({
  14: {
    "url": f"{iiab_map_host_url}/openstreetmap-openmaptiles.{maps_vector_data_date}.z00-z14.pmtiles",
    "DETAILS": json_comment("""
      maps_vector_zoom: 14

      'high res' aka 'full quality' osm, including 3d buildings.
    """)
  },

  11: {
    "url": f"{iiab_map_host_url}/openstreetmap-openmaptiles.{maps_vector_data_date}.z00-z11.pmtiles",
    "DETAILS": json_comment("""
      maps_vector_zoom: 11

      'medium res' osm, up to zoom level 11 (original file has 14).
    """)
  },

  # NOTE: We will pass this into maps.black as if it's the OpenStreetMap data, even though
  # it's Natural Earth. They're both in the OpenMapTiles schema. The OSM and NE variants of
  # the "Natural" style we use are compatible, with just some zoom range differences (which
  # makes no difference that I notice). This will fail to show "naturalearth" in attributions
  # ("naturalearth6" is separate), even in "generous" attribution mode. However maps.black
  # and the naturalearth website say that crediting authors is unnecessary. It's not worth
  # the time to fix just for consistency.
  "nat-z8": {
    "url": f"{iiab_map_host_url}/naturalearth-openmaptiles.{maps_slow_data_date}.z00-z08.pmtiles",
    "DETAILS": json_comment("""
      maps_vector_zoom: nat-z8

      'low res' - mostly borders, rivers, country names, large roads.
      (Uses Natural Earth instead of OpenStreetMap)
    """)
  },

  "1-ci": {
    "url": f"{iiab_map_host_url}/openstreetmap-openmaptiles.{maps_vector_data_date}.z00-z01.pmtiles",
    "DETAILS": json_comment("""
      maps_vector_zoom: 1

      FOR TESTING OR FALLBACK ONLY

      'skeleton' osm, up to zoom level 1 (original file has 14).
    """)
  },
}, ["1-ci", "nat-z8", 11, 14])

maps_dot_black_satellite_tiles = dict_with_order({
  7: {
    "url": f"{iiab_map_host_url}/s2maps-sentinel2-2023.{maps_satellite_data_date}.z00-z07.pmtiles",
    "DETAILS": json_comment("""
      maps_satellite_zoom: 7

      Low quality satellite, up to zoom level 7 (original file has 13)
    """)
  },

  9: {
    "url": f"{iiab_map_host_url}/s2maps-sentinel2-2023.{maps_satellite_data_date}.z00-z09.pmtiles",
    "DETAILS": json_comment("""
      maps_satellite_zoom: 9

      Moderately high quality satellite, up to zoom level 9 (original file has 13)
    """)
  },

  11: {
    "url": f"{iiab_map_host_url}/s2maps-sentinel2-2023.{maps_satellite_data_date}.z00-z11.pmtiles",
    "DETAILS": json_comment("""
      maps_satellite_zoom: 11

      Pretty high quality satellite, up to zoom level 11 (original file has 13)
    """)
  },

  12: {
    "url": f"{iiab_map_host_url}/s2maps-sentinel2-2023.{maps_satellite_data_date}.z00-z12.pmtiles",
    "DETAILS": json_comment("""
      maps_satellite_zoom: 12

      Pretty high quality satellite, up to zoom level 12 (original file has 13)
    """)
  },

  13: {
    "url": f"{iiab_map_host_url}/s2maps-sentinel2-2023.{maps_satellite_data_date}.z00-z13.pmtiles",
    "DETAILS": json_comment("""
      maps_satellite_zoom: 13

      Highest available quality satellite, up to zoom level 13
    """)
  },

  "none": {
    "DETAILS": json_comment("""
      maps_satellite_zoom: none

      Disable satellite. There is no URL associated with this option because it
      doesn't download anything. However it will NOT delete satellite files
      you have downloaded previously.
    """)
  },

  "4-ci": {
    "url": f"{iiab_map_host_url}/s2maps-sentinel2-2023.{maps_satellite_data_date}.z00-z04.pmtiles",
    "DETAILS": json_comment("""
      maps_satellite_zoom: 4

      FOR TESTING ONLY

      Super-low quality satellite, up to zoom level 4 (original file has 13)
    """)
  },
}, ["none", "4-ci", 7, 9, 11, 12, 13])

maps_dot_black_terrain_tiles = dict_with_order({
  7: {
    "url": f"{iiab_map_host_url}/terrarium.{maps_slow_data_date}.z00-z07.pmtiles",
    "DETAILS": json_comment("""
      maps_terrain_zoom: 7

      Low quality terrain, up to zoom level 7 (original file has 10)
    """)
  },

  8: {
    "url": f"{iiab_map_host_url}/terrarium.{maps_slow_data_date}.z00-z08.pmtiles",
    "DETAILS": json_comment("""
      maps_terrain_zoom: 8
    """)
  },

  9: {
    "url": f"{iiab_map_host_url}/terrarium.{maps_slow_data_date}.z00-z09.pmtiles",
    "DETAILS": json_comment("""
      maps_terrain_zoom: 9
    """)
  },

  10: {
    "url": f"{iiab_map_host_url}/terrarium.{maps_slow_data_date}.z00-z10.pmtiles",
    "DETAILS": json_comment("""
      maps_terrain_zoom: 10

      (This is the highest quality that maps.black offers in pmtiles format. They
      offer 11, 12, and 13 in squashfs format, but they are massive files.)
    """)
  },

  "0-none": {
    "url": f"{iiab_map_host_url}/terrarium-none.pmtiles",
    "DETAILS": json_comment("""
      maps_terrain_zoom: 0-none

      A 'dummy' maxzoom=0 world map terrain file to fill a role that maps.black/maplibre
      needs if we have FQRs and the user enables terrain.
    """)
  },
}, ["0-none", 7, 8, 9, 10])

# Mostly colors, topography (as an image, not an elevation map), etc.
maps_dot_black_naturalearth6_tiles = dict_with_order({
  6: {
    "url": f"{iiab_map_host_url}/naturalearth6-NE2_HR_SR_W_DR-WEBP.{maps_slow_data_date}.z00-z06.pmtiles",
    "DETAILS": json_comment("""
      Normal, default value
    """)
  },

  "4-ci": {
    "url": f"{iiab_map_host_url}/naturalearth6-NE2_HR_SR_W_DR-WEBP.{maps_slow_data_date}.z00-z04.pmtiles",
    "DETAILS": json_comment("""
      FOR TESTING ONLY
    """)
  },
}, ["4-ci", 6])

static_search_data = dict_with_order({
  "pop-1k-cities": {
    "url": f"{iiab_map_host_url}/static-search.{maps_static_search_data_date}.pop-1k-cities.tar.gz",
    "DETAILS": json_comment("""
      maps_search_static_db: pop-1k-cities

      Cities-only static database
    """)
  },

  "pop-100k-cities": {
    "url": f"{iiab_map_host_url}/static-search.{maps_static_search_data_date}.pop-100k-cities.tar.gz",
    "DETAILS": json_comment("""
      maps_search_static_db: pop-100k-cities

      FOR TESTING ONLY

      Large cities-only static database
    """)
  },
}, ["pop-1k-cities", "pop-100k-cities"])

# Keeping nominatim on maps_slow_data_date until we actually update it again
nominatim_data = dict_with_order({
  # TODO - Make a basic small whole-world map
  "basic": {
    "url": f"{iiab_map_host_url}/nominatim.{maps_slow_data_date}.basic.sqlite",
    "DETAILS": json_comment("""
      maps_search_nominatim_db: basic

      Basic nominatim database. (California admin+natural for now.)
    """)
  },
  "full": {
    "url": f"{iiab_map_host_url}/nominatim.{maps_slow_data_date}.full.sqlite",
    "DETAILS": json_comment("""
      maps_search_nominatim_db: full

      Full nominatim database
    """)
  },
}, ["basic", "full"])

README = json_comment("""
This is a catalog of the latest data available for IIAB Maps.

IMPORTANT: The copy of this file found at /opt/iiab/iiab/roles/maps/maps-catalog.json
may not be the version that your IIAB will use for downloading map data. It may be
out of date, and any changes made here will have no effect.

Instead, for map installation and upgrades, your IIAB will always use the latest
version found here:
https://github.com/iiab/iiab/blob/master/roles/maps/maps-catalog.json

This way, you can always the latest map data without upgrading your IIAB software.

To see the data that is stored: https://iiab.switnet.org/maps/2/

For info on how to use this file see:
https://github.com/iiab/iiab/blob/master/roles/maps/README.md
""")

catalog = {
    "README": README,
    "satellite": maps_dot_black_satellite_tiles,
    "terrain": maps_dot_black_terrain_tiles,
    "vector": maps_dot_black_vector_tiles,
    "naturalearth6": maps_dot_black_naturalearth6_tiles,
    "static_search": static_search_data,
    "nominatim": nominatim_data,
}

# Make sure all of the URLs are valid
for maptype, zooms in catalog.items():
    if maptype != "README":
        for zoom, file in zooms.items():
            if 'url' in file:
                assert requests.head(file["url"]).status_code == 200, "Error with URL: " + url

open("maps-catalog.json", "w").write(json.dumps(catalog, indent=4))
