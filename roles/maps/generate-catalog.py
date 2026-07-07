#!/usr/bin/python3
import requests, jinja2, json, yaml

# TODO - this message doesn't apply to the copy of this file that gets cached
# in /etc/iiab/ copy since that one is actually up to date
# If you are installing or configuring IIAB Maps, *you should ignore `/opt/iiab/iiab/roles/maps/maps-catalog.json`*.
#
# But in case you're curious:
#
# `maps-catalog.json` is a catalog of the latest available IIAB Maps data. Unlike just about everything else in this repository, this file is not used directly by the IIAB Maps installation process. Instead, it is made to requested by IIAB Maps _from Github_ during installation and map upgrades. This way, as soon as a map data update is made available, we can update this file on Github and it can be installed without upgrading all of Maps on your IIAB.

# TODO put dates etc directly into this file, not in main.yml
mail_yml = yaml.safe_load(open("defaults/main.yml").read())

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
def set_key_order(tiles, ordered_keys):
    assert set(tiles.keys()) == set(ordered_keys), (tiles.keys(), ordered_keys)
    return {key: tiles[key] for key in ordered_keys}

maps_dot_black_vector_tiles = {
  # "high res" full osm, including 3d buildings.
  # (TODO does this include colors and topography? Or is it used along with naturalearth6 above in most styles?)
  # maps_vector_quality = "osm-z14"
  14: f"{iiab_map_host_url}/openstreetmap-openmaptiles.{maps_vector_data_date}.z00-z14.pmtiles",

  # "medium res" osm, up to zoom level 11 (original file has 14).
  # (TODO does this include colors and topography? Or is it used along with naturalearth6 above in most styles?)
  # maps_vector_quality = "osm-z11"
  11: f"{iiab_map_host_url}/openstreetmap-openmaptiles.{maps_vector_data_date}.z00-z11.pmtiles",

  # "low res" - mostly borders, rivers, country names, large roads.
  # maps_vector_quality = "nat-z8"
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
  # maps_vector_quality = "osm-z1"
  1: f"{iiab_map_host_url}/openstreetmap-openmaptiles.{maps_vector_data_date}.z00-z01.pmtiles",
}
maps_dot_black_vector_tiles = set_key_order(maps_dot_black_vector_tiles, [1, 11, 14, "nat-z8"])

maps_dot_black_satellite_tiles = {
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
}
maps_dot_black_satellite_tiles = set_key_order(maps_dot_black_satellite_tiles, [4, 7, 9, 11, 12, 13])

maps_dot_black_terrain_tiles = {
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
}
maps_dot_black_terrain_tiles = set_key_order(maps_dot_black_terrain_tiles, [7, 8, 9, 10, "none"])

def render(source, data):
    rtemplate = jinja2.Environment(loader=jinja2.BaseLoader).from_string(source)
    return rtemplate.render(**data)

catalog = {
    "_README": [
        "If you are installing or configuring",
        "IIAB Maps, you should ignore this file.",
        "See /opt/iiab/iiab/maps/generate-catalog.py",
        "for more info.",
    ],
    "satellite": maps_dot_black_satellite_tiles,
    "terrain": maps_dot_black_terrain_tiles,
    "vector": maps_dot_black_vector_tiles,
}

for maptype, zooms in catalog.items():
    if maptype != "_README":
        for zoom, url in zooms.items():
            assert requests.head(url).status_code == 200, "Error with URL: " + url

open("maps-catalog.json", "w").write(json.dumps(catalog, indent=4))
