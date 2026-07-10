#!/usr/bin/python3
import requests, jinja2, json, yaml

# TODO - In case we go back to caching in /etc/iiab:
# * We need to use /etc/iiab/ cache for FQRs as well
# * The following message doesn't apply to the cache in /etc/iiab/ copy since that one is actually up to date.
#
# If you are installing or configuring IIAB Maps, *you should ignore `/opt/iiab/iiab/roles/maps/maps-catalog.json`*.
#
# But in case you're curious:
#
# `maps-catalog.json` is a catalog of the latest available IIAB Maps data. Unlike just about everything else in this repository, this file is not used directly by the IIAB Maps installation process. Instead, it is made to requested by IIAB Maps _from Github_ during installation and map upgrades. This way, as soon as a map data update is made available, we can update this file on Github and it can be installed without upgrading all of Maps on your IIAB.

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

maps_dot_black_vector_tiles = dict_with_order({
  # "high res" full osm, including 3d buildings.
  # (TODO does this include colors and topography? Or is it used along with naturalearth6 above in most styles?)
  # maps_vector_zoom = 14
  14: f"{iiab_map_host_url}/openstreetmap-openmaptiles.{maps_vector_data_date}.z00-z14.pmtiles",

  # "medium res" osm, up to zoom level 11 (original file has 14).
  # (TODO does this include colors and topography? Or is it used along with naturalearth6 above in most styles?)
  # maps_vector_zoom = 11
  11: f"{iiab_map_host_url}/openstreetmap-openmaptiles.{maps_vector_data_date}.z00-z11.pmtiles",

  # "low res" - mostly borders, rivers, country names, large roads.
  # maps_vector_zoom = "nat-z8"
  # (nat-z8 = "Natural Earth")
  #
  # NOTE: We will pass this into maps.black as if it's the OpenStreetMap data, even though
  # it's Natural Earth. They're both in the OpenMapTiles schema. The OSM and NE variants of
  # the "Natural" style we use are compatible, with just some zoom range differences (which
  # makes no difference that I notice). This will fail to show "naturalearth" in attributions
  # ("naturalearth6" is separate), even in "generous" attribution mode. However maps.black
  # and the naturalearth website say that crediting authors is unnecessary. It's not worth
  # the time to fix just for consistency.
  "nat-z8": f"{iiab_map_host_url}/naturalearth-openmaptiles.{maps_slow_data_date}.z00-z08.pmtiles",

  # FOR TESTING ONLY
  # "medium res" osm, up to zoom level 1 (original file has 14).
  # maps_vector_zoom = 1
  1: f"{iiab_map_host_url}/openstreetmap-openmaptiles.{maps_vector_data_date}.z00-z01.pmtiles",
}, [1, 11, 14, "nat-z8"])

maps_dot_black_satellite_tiles = dict_with_order({
  # Low quality satellite, up to zoom level 7 (original file has 13)
  # maps_satellite_zoom = 7
  7: f"{iiab_map_host_url}/s2maps-sentinel2-2023.{maps_satellite_data_date}.z00-z07.pmtiles",

  # Moderately high quality satellite, up to zoom level 9 (original file has 13)
  # maps_satellite_zoom = 9
  9: f"{iiab_map_host_url}/s2maps-sentinel2-2023.{maps_satellite_data_date}.z00-z09.pmtiles",

  # Pretty high quality satellite, up to zoom level 11 (original file has 13)
  # maps_satellite_zoom = 11
  11: f"{iiab_map_host_url}/s2maps-sentinel2-2023.{maps_satellite_data_date}.z00-z11.pmtiles",

  # Pretty high quality satellite, up to zoom level 12 (original file has 13)
  # maps_satellite_zoom = 12
  12: f"{iiab_map_host_url}/s2maps-sentinel2-2023.{maps_satellite_data_date}.z00-z12.pmtiles",

  # Highest available quality satellite, up to zoom level 13
  # maps_satellite_zoom = 13
  13: f"{iiab_map_host_url}/s2maps-sentinel2-2023.{maps_satellite_data_date}.z00-z13.pmtiles",

  # FOR TESTING ONLY
  # Super-low quality satellite, up to zoom level 4 (original file has 13)
  # maps_satellite_zoom = 4
  4: f"{iiab_map_host_url}/s2maps-sentinel2-2023.{maps_satellite_data_date}.z00-z04.pmtiles",
}, [4, 7, 9, 11, 12, 13])

maps_dot_black_terrain_tiles = dict_with_order({
  # Low quality terrain, up to zoom level 7 (original file has 10)
  # maps_terrain_zoom = 7
  7: f"{iiab_map_host_url}/terrarium.{maps_slow_data_date}.z00-z07.pmtiles",

  # maps_terrain_zoom = 8
  8: f"{iiab_map_host_url}/terrarium.{maps_slow_data_date}.z00-z08.pmtiles",

  # maps_terrain_zoom = 9
  9: f"{iiab_map_host_url}/terrarium.{maps_slow_data_date}.z00-z09.pmtiles",

  # maps_terrain_zoom = 10
  # (This is the highest quality that maps.black offers in pmtiles format. They
  # offer 11, 12, and 13 in squashfs format, but they are massive files.)
  10: f"{iiab_map_host_url}/terrarium.{maps_slow_data_date}.z00-z10.pmtiles",

  # A "dummy" maxzoom=0 world map terrain file to fill a role that maps.black/maplibre
  # needs if we have FQRs and the user enables terrain.
  "none": f"{iiab_map_host_url}/terrarium-none.pmtiles",
}, [7, 8, 9, 10, "none"])

# Mostly colors, topography, etc.
maps_dot_black_naturalearth6_tiles = dict_with_order({
  # For actual users
  "full": f"{iiab_map_host_url}/naturalearth6-NE2_HR_SR_W_DR-WEBP.{maps_slow_data_date}.z00-z06.pmtiles",

  # FOR TESTING ONLY
  "ci": f"{iiab_map_host_url}/naturalearth6-NE2_HR_SR_W_DR-WEBP.{maps_slow_data_date}.z00-z04.pmtiles",
}, ["full", "ci"])

static_search_data = dict_with_order({
  # Cities-only static database
  # maps_search_static_db = "pop-1k-cities"
  "pop-1k-cities": f"{iiab_map_host_url}/static-search.{maps_static_search_data_date}.pop-1k-cities.tar.gz",

  # Large cities-only static database
  # maps_search_static_db = "pop-100k-cities"
  # FOR TESTING ONLY
  "pop-100k-cities": f"{iiab_map_host_url}/static-search.{maps_static_search_data_date}.pop-100k-cities.tar.gz",
}, ["pop-1k-cities", "pop-100k-cities"])

# Keeping nominatim on maps_slow_data_date until we actually update it again
nominatim_data = dict_with_order({
  # Basic nominatim database
  # maps_search_nominatim_db = "basic"
  "basic": f"{iiab_map_host_url}/nominatim.{maps_slow_data_date}.basic.sqlite",
    # California admin+natural for now. TODO make a small worldwide one. (unless we go to the frontend-only one)
    # TODO - Make a basic small whole-world map, at least as good as previous maps

  # Full nominatim database
  # maps_search_nominatim_db = "full"
  "full": f"{iiab_map_host_url}/nominatim.{maps_slow_data_date}.full.sqlite",
}, ["basic", "full"])

def render(source, data):
    rtemplate = jinja2.Environment(loader=jinja2.BaseLoader).from_string(source)
    return rtemplate.render(**data)

catalog = {
    "README": [
        "If you are installing or configuring",
        "IIAB Maps, you should ignore this file.",
        "See /opt/iiab/iiab/maps/generate-catalog.py",
        "for more info.",
    ],
    "satellite": maps_dot_black_satellite_tiles,
    "terrain": maps_dot_black_terrain_tiles,
    "vector": maps_dot_black_vector_tiles,
    "naturalearth6": maps_dot_black_naturalearth6_tiles,
    "static_search": static_search_data,
    "nominatim": nominatim_data,
}

for maptype, zooms in catalog.items():
    if maptype != "README":
        for zoom, url in zooms.items():
            assert requests.head(url).status_code == 200, "Error with URL: " + url

open("maps-catalog.json", "w").write(json.dumps(catalog, indent=4))
