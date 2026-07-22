Global file examples:

```
type                       | date       | depth         | extension
---------------------------------------------------------------------------
s2maps-sentinel2-2023      . 2025-12-10 . z00-z07       . pmtiles
naturalearth-openmaptiles  . 2025-12-10 . z00-z08       . pmtiles
openstreetmap-openmaptiles . 2026-07-01 . z00-z14       . pmtiles
static-search              . 2026-04-22 . pop-1k-cities
nominatim                  . 2025-12-10 . basic         . sqlite
```

Full Quality Region examples:

```
type                       | date       | region | ...         | extension
---------------------------------------------------------------------------
openstreetmap-openmaptiles . 2026-07-01 . africa . full-region . pmtiles
```

For global files:

```
[type].[date].[depth].[extension (for files)]
```

For Full Quality Region (FQR) files:

```
[type].[date].full-region.[region].[extension (for files)]
```

* `type` refers to the data source for pmtiles files, or the search engine for search
* `date` refers to the date that the data was generated
* `depth` refers to the zoom level range for pmtiles files, or in the case of search it refers to the type or amount of search data available. Depth should not be named "full-region".
* `region` is the user-defined name of the FQR
* `extension` is a file extension in the case of files, or nothing in the case of directories
