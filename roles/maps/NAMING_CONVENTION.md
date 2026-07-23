# Naming Convention

How map data files are named

## Global map data files:

```
type                       | date       | depth         | extension (for files)
---------------------------------------------------------------------------
s2maps-sentinel2-2023      . 2025-12-10 . z00-z07       . pmtiles
naturalearth-openmaptiles  . 2025-12-10 . z00-z08       . pmtiles
openstreetmap-openmaptiles . 2026-07-01 . z00-z14       . pmtiles
static-search              . 2026-04-22 . pop-1k-cities
nominatim                  . 2025-12-10 . basic         . sqlite
```

```
[type].[date].[depth].[extension (for files)]
```

## Full Quality Regions:

```
type                       | date       | region | ...         | extension (for files)
---------------------------------------------------------------------------
openstreetmap-openmaptiles . 2026-07-01 . africa . full-region . pmtiles
```

```
[type].[date].full-region.[region].[extension (for files)]
```

# Key

* `type` refers to the data source for pmtiles files, or the search engine for search
* `date` refers to the date that the data was generated
* `depth` refers to the zoom level range for pmtiles files, or in the case of search it refers to the type or amount of search data available. Depth should not be named "full-region".
* `region` is the user-defined name of the FQR
* `extension` is a file extension in the case of files, or nothing in the case of directories
