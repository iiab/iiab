# Naming Conventions

How map data files are named

## Global map data files:

```
| type                       | date       | depth         | extension (for files)
|---------------------------------------------------------------
| s2maps-sentinel2-2023      . 2025-12-10 . z00-z07       . pmtiles
| naturalearth-openmaptiles  . 2025-12-10 . z00-z08       . pmtiles
| openstreetmap-openmaptiles . 2026-07-01 . z00-z14       . pmtiles
| terrarium                  . 2025-12-10 . z00-z08       . pmtiles
| static-search              . 2026-04-22 . pop-1k-cities . tar.gz (*)
| static-search              . 2026-04-22 . pop-1k-cities
| nominatim                  . 2025-12-10 . basic         . sqlite
```

```
[type].[date].[depth].[extension (for files)]
```

(*) Note that in the case of `.tar.gz` files (currently only static-search), the extension will be in the catalog and on the file server, but when installed locally it will be expanded into a directory with no extension.

## Full Quality Regions:

```
region | ... | type                       | date       | extension (for files)
---------------------------------------------------------------------------
africa . fqr / openstreetmap-openmaptiles . 2026-07-01 . pmtiles
africa . fqr / s2maps-sentinel2-2023      . 2025-12-10 . pmtiles
africa . fqr / terrarium                  . 2025-12-10 . pmtiles
```

```
[region].fqr/[type].[date].[extension (for files)]
```

## Key

* `type` refers to the data source for pmtiles files, or the search engine for search
* `date` refers to the date that the data was generated
* `depth` refers to the zoom level range for pmtiles files, or in the case of search it refers to the type or amount of search data available. Depth should not be named "full-region".
* `region` is the user-defined name of the FQR
* `extension` is a file extension in the case of files, or nothing in the case of directories.

# File Specifications

## Full Quality Regions

Full Quality Regions are stored in directories. They contain data files for that region, as well as `meta.json`. For example:

London:

```
{"bbox": [-0.172187453, 51.477245915, -0.143235226, 51.493348151]}
```

Rabi Island, Fiji (crosses 180 longitude, see below):

```
{"bbox": [179.967638715, -16.54082487, -179.911191897, -16.438722265]}
```

The field `bbox` refers to the bounding box of the region:

```
{"bbox": [<min_lon>, <min_lat>, <max_lon>, <max_lat>]}
```

Latitudes have the following requirements:
* `-90 <= min_lat < max_lat <= 90`

Longitudes have the following requirements:
* `min_lon != max_lon`
* `-180 < min_lon <= 180`
* `-180 < max_lon <= 180`

Note that `max_lon < min_lon` is possible, and implies that the region crosses the 180/-180 longitude (aka the "antimeridian").
