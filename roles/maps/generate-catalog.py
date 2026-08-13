#!/usr/bin/python3
import humanize, requests, json

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

def fix_multiline_spacing(s):
    return '\n'.join([line.strip() for line in s.strip().split('\n')])

def json_comment(s):
    assert '"' not in s, f"remove the double quotation mark (escaping it looks ugly) from:\n\n{s}"
    return fix_multiline_spacing(s).split('\n')

def url_only(tiles):
    return {
        zoom: file["url"]
        for (zoom, file)
        in tiles.items()
        if "url" in file
    }

def add_file_sizes(tiles):
    for (zoom, file) in tiles.items():
        if "url" in file:
            url = file["url"]
            response = requests.head(url)

            # Make the URLs are valid while we're at it
            assert response.status_code == 200, "Error with URL: " + url

            file["size"] = humanize.naturalsize(response.headers["Content-Length"])

vector_tiles = dict_with_order({
  14: {
    "url": f"{iiab_map_host_url}/openstreetmap-openmaptiles.{maps_vector_data_date}.z00-z14.pmtiles",
    "details": fix_multiline_spacing("""
      'high res' aka 'full quality' osm, including 3d buildings.
    """)
  },

  11: {
    "url": f"{iiab_map_host_url}/openstreetmap-openmaptiles.{maps_vector_data_date}.z00-z11.pmtiles",
    "details": fix_multiline_spacing("""
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
    "details": fix_multiline_spacing("""
      'low res' - mostly borders, rivers, country names, large roads. (Uses Natural Earth instead of OpenStreetMap)
    """)
  },

  "1-ci": {
    "url": f"{iiab_map_host_url}/openstreetmap-openmaptiles.{maps_vector_data_date}.z00-z01.pmtiles",
    "details": fix_multiline_spacing("""
      FOR TESTING OR FALLBACK ONLY

      'skeleton' osm, up to zoom level 1 (original file has 14).
    """)
  },
}, ["1-ci", "nat-z8", 11, 14])

satellite_tiles = dict_with_order({
  7: {
    "url": f"{iiab_map_host_url}/s2maps-sentinel2-2023.{maps_satellite_data_date}.z00-z07.pmtiles",
    "details": fix_multiline_spacing("""
      Low quality satellite, up to zoom level 7 (original file has 13)
    """)
  },

  9: {
    "url": f"{iiab_map_host_url}/s2maps-sentinel2-2023.{maps_satellite_data_date}.z00-z09.pmtiles",
    "details": fix_multiline_spacing("""
      Moderately high quality satellite, up to zoom level 9 (original file has 13)
    """)
  },

  11: {
    "url": f"{iiab_map_host_url}/s2maps-sentinel2-2023.{maps_satellite_data_date}.z00-z11.pmtiles",
    "details": fix_multiline_spacing("""
      Pretty high quality satellite, up to zoom level 11 (original file has 13)
    """)
  },

  12: {
    "url": f"{iiab_map_host_url}/s2maps-sentinel2-2023.{maps_satellite_data_date}.z00-z12.pmtiles",
    "details": fix_multiline_spacing("""
      Pretty high quality satellite, up to zoom level 12 (original file has 13)
    """)
  },

  13: {
    "url": f"{iiab_map_host_url}/s2maps-sentinel2-2023.{maps_satellite_data_date}.z00-z13.pmtiles",
    "details": fix_multiline_spacing("""
      Highest available quality satellite, up to zoom level 13
    """)
  },

  "none": {
    "details": fix_multiline_spacing("""
      Disable satellite. There is no URL associated with this option because it doesn't download anything.

      NOTE: This will not necessarily delete any satellite files you have downloaded previously.
    """)
  },

  "4-ci": {
    "url": f"{iiab_map_host_url}/s2maps-sentinel2-2023.{maps_satellite_data_date}.z00-z04.pmtiles",
    "details": fix_multiline_spacing("""
      FOR TESTING ONLY

      Super-low quality satellite, up to zoom level 4 (original file has 13)
    """)
  },
}, ["none", "4-ci", 7, 9, 11, 12, 13])

terrain_tiles = dict_with_order({
  7: {
    "url": f"{iiab_map_host_url}/terrarium.{maps_slow_data_date}.z00-z07.pmtiles",
    "details": fix_multiline_spacing("""
      Low quality terrain, up to zoom level 7 (original file has 10)
    """)
  },

  8: {
    "url": f"{iiab_map_host_url}/terrarium.{maps_slow_data_date}.z00-z08.pmtiles",
    "details": fix_multiline_spacing("""
    """)
  },

  9: {
    "url": f"{iiab_map_host_url}/terrarium.{maps_slow_data_date}.z00-z09.pmtiles",
    "details": fix_multiline_spacing("""
    """)
  },

  10: {
    "url": f"{iiab_map_host_url}/terrarium.{maps_slow_data_date}.z00-z10.pmtiles",
    "details": fix_multiline_spacing("""
      (This is the highest quality that maps.black offers in pmtiles format. They offer 11, 12, and 13 in squashfs format, but they are massive files.)
    """)
  },

  "0-none": {
    "url": f"{iiab_map_host_url}/terrarium-none.pmtiles",
    "details": fix_multiline_spacing("""
      A 'dummy' maxzoom=0 world map terrain file to fill a role that maps.black/maplibre needs if we have FQRs and the user enables terrain.
    """)
  },
}, ["0-none", 7, 8, 9, 10])

# Mostly colors, topography (as an image, not an elevation map), etc.
naturalearth6_tiles = dict_with_order({
  6: {
    "url": f"{iiab_map_host_url}/naturalearth6-NE2_HR_SR_W_DR-WEBP.{maps_slow_data_date}.z00-z06.pmtiles",
    "details": fix_multiline_spacing("""
      Normal, default value
    """)
  },

  "4-ci": {
    "url": f"{iiab_map_host_url}/naturalearth6-NE2_HR_SR_W_DR-WEBP.{maps_slow_data_date}.z00-z04.pmtiles",
    "details": fix_multiline_spacing("""
      FOR TESTING ONLY
    """)
  },
}, ["4-ci", 6])

static_search_data = dict_with_order({
  "pop-1k-cities": {
    "url": f"{iiab_map_host_url}/static-search.{maps_static_search_data_date}.pop-1k-cities.tar.gz",
    "details": fix_multiline_spacing("""
      Cities-only static database
    """)
  },

  "pop-100k-cities": {
    "url": f"{iiab_map_host_url}/static-search.{maps_static_search_data_date}.pop-100k-cities.tar.gz",
    "details": fix_multiline_spacing("""
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
    "details": fix_multiline_spacing("""
      Basic nominatim database. (California admin+natural for now.)
    """)
  },
  "full": {
    "url": f"{iiab_map_host_url}/nominatim.{maps_slow_data_date}.full.sqlite",
    "details": fix_multiline_spacing("""
      Full nominatim database
    """)
  },
}, ["basic", "full"])

JSON_README = """
Catalog of the latest available IIAB Maps data:
https://github.com/iiab/iiab/blob/master/roles/maps/maps-catalog.json
ASSUME ALL OTHER COPIES of maps-catalog.json (INCLUDING THE ONE ON YOUR IIAB) ARE STALE AND OUT OF DATE!
Catalog Guide: https://github.com/iiab/iiab/blob/master/roles/maps/MAPS_CATALOG_DETAILS.md
Full Documentation: https://github.com/iiab/iiab/blob/master/roles/maps/README.md
Raw file listing: https://iiab.switnet.org/maps/2/
""".strip()

MAPS_CATALOG_DETAILS_README = """
This guide is for [`maps-catalog.json`](https://github.com/iiab/iiab/blob/master/roles/maps/maps-catalog.json),
which is the catalog of the latest data available for IIAB Maps. The only truly valid version of this
guide is is [here](https://github.com/iiab/iiab/blob/master/roles/maps/MAPS_CATALOG_DETAILS.md).
ASSUME ALL OTHER COPIES (INCLUDING THE ONE ON YOUR IIAB) ARE STALE (OUT OF DATE!)

* [IIAB Maps Documentation](https://github.com/iiab/iiab/blob/master/roles/maps/README.md)
* [Raw file listing](https://iiab.switnet.org/maps/2/)
"""

catalog = {
    "satellite": satellite_tiles,
    "terrain": terrain_tiles,
    "vector": vector_tiles,
    "naturalearth6": naturalearth6_tiles,
    "static_search": static_search_data,
    "nominatim": nominatim_data,
}

for map_type, tiles in catalog.items():
    add_file_sizes(tiles)

setting_name = {
    "satellite": "maps_satellite_zoom",
    "terrain": "maps_terrain_zoom",
    "vector": "maps_vector_zoom",
    "naturalearth6": "maps_ne6_zoom",
    "static_search": "maps_search_static_db",
    "nominatim": "maps_search_nominatim_db",
}

open("maps-catalog.json", "w").write(json.dumps(
    {
        "README": json_comment(JSON_README),
        "data": {
            map_type: url_only(tiles)
            for (map_type, tiles)
            in catalog.items()
        }
    }
, indent=4))

with open("MAPS_CATALOG_DETAILS.md", "w") as f:
    f.write(MAPS_CATALOG_DETAILS_README + "\n\n")
    for map_type, tiles in catalog.items():
        f.write(f"# {map_type}\n\n")
        for zoom, file in tiles.items():
            file_size = f" ({file['size']})" if 'size' in file else ""
            f.write(f"## `{setting_name[map_type]}: {zoom}`{file_size}\n\n{file['details']}\n\n")
