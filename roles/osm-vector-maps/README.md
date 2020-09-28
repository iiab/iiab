## What's Changed in Maps for the IIAB 7.2 Release?

1. Two variables have new meanings:
    1. `osm_vector_maps_install` in `/etc/iiab/local_vars.yml` means install the map program (about 40MB).
    2. `osm_vector_maps_installed` in `/etc/iiab/iiab_state.yml` means it's been installed [no longer means "install a functioning world map to zoom 10 (about 2.8GB)" right?].
2. There is a new installer page (http://box/osm-vector-maps/installer/) separate from the Admin Console, with installs regions and downloads higher resolution satellite imagery from zoom 11 [10?] to zoom 13 (16 times [5x5 km to 5x5 m pixels implies 1000X ?] the resolution provided by zoom 10 [9?]).
3. Multiple vector OpenStreetMap regions may be installed, and viewed on the same map.
4. Multiple regions of satellite improvements can be added to the same map.
5. The region size for satellite downloads can be adjusted to 100x100 km, 300x300 km, or 1000x1000 km around a selected map point.
6. More recent OSM data is used in the vector tiles (2017 => 2019) [is this included in all 12 Map Packs?].
7. Increase the base install (world view) from zoom 9 to 10, so that city search is successful more of the time [is this included in all 12 Map Packs?].
8. There is a new drag-and-drop feature which permits the student to add descriptions and pictures about local points of interest, and then save and restore them using their local browser [how does one do this?].
