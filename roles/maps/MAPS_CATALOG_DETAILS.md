
This guide is for [`maps-catalog.json`](https://github.com/iiab/iiab/blob/master/roles/maps/maps-catalog.json),
which is the catalog of the latest data available for IIAB Maps. The only truly valid version of this
guide is is [here](https://github.com/iiab/iiab/blob/master/roles/maps/MAPS_CATALOG_DETAILS.md).
ASSUME ALL OTHER COPIES (INCLUDING THE ONE ON YOUR IIAB) ARE STALE (OUT OF DATE!)

* [IIAB Maps Documentation](https://github.com/iiab/iiab/blob/master/roles/maps/README.md)
* [Raw file listing](https://iiab.switnet.org/maps/2/)


# satellite

## `maps_satellite_zoom: none`

Disable satellite. There is no URL associated with this option because it doesn't download anything.

NOTE: This will not necessarily delete any satellite files you have downloaded previously.

## `maps_satellite_zoom: 4-ci` (2.0 MB)

FOR TESTING ONLY

Super-low quality satellite, up to zoom level 4 (original file has 13)

## `maps_satellite_zoom: 7` (88.8 MB)

Low quality satellite, up to zoom level 7 (original file has 13)

## `maps_satellite_zoom: 9` (1.2 GB)

Moderately high quality satellite, up to zoom level 9 (original file has 13)

## `maps_satellite_zoom: 11` (22.3 GB)

Pretty high quality satellite, up to zoom level 11 (original file has 13)

## `maps_satellite_zoom: 12` (85.7 GB)

Pretty high quality satellite, up to zoom level 12 (original file has 13)

## `maps_satellite_zoom: 13` (290.3 GB)

Highest available quality satellite, up to zoom level 13

# terrain

## `maps_terrain_zoom: 0-none` (107.2 kB)

A 'dummy' maxzoom=0 world map terrain file to fill a role that maps.black/maplibre needs if we have FQRs and the user enables terrain.

## `maps_terrain_zoom: 7` (978.2 MB)

Low quality terrain, up to zoom level 7 (original file has 10)

## `maps_terrain_zoom: 8` (6.4 GB)



## `maps_terrain_zoom: 9` (28.6 GB)



## `maps_terrain_zoom: 10` (106.2 GB)

(This is the highest quality that maps.black offers in pmtiles format. They offer 11, 12, and 13 in squashfs format, but they are massive files.)

# vector

## `maps_vector_zoom: 1-ci` (1.2 MB)

FOR TESTING OR FALLBACK ONLY

'skeleton' osm, up to zoom level 1 (original file has 14).

## `maps_vector_zoom: nat-z8` (89.4 MB)

'low res' - mostly borders, rivers, country names, large roads. (Uses Natural Earth instead of OpenStreetMap)

## `maps_vector_zoom: 11` (9.0 GB)

'medium res' osm, up to zoom level 11 (original file has 14).

## `maps_vector_zoom: 14` (87.4 GB)

'high res' aka 'full quality' osm, including 3d buildings.

# naturalearth6

## `maps_ne6_zoom: 4-ci` (7.0 MB)

FOR TESTING ONLY

## `maps_ne6_zoom: 6` (60.4 MB)

Normal, default value

# static_search

## `maps_search_static_db: pop-1k-cities` (16.1 MB)

Cities-only static database

## `maps_search_static_db: pop-100k-cities` (926.0 kB)

FOR TESTING ONLY

Large cities-only static database

# nominatim

## `maps_search_nominatim_db: basic` (639.8 MB)

Basic nominatim database. (California admin+natural for now.)

## `maps_search_nominatim_db: full` (67.0 GB)

Full nominatim database

