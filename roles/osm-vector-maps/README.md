## What's Changed in Maps for the IIAB 7.2 Release?

1. Some variables have newer meanings:
    1. `osm_vector_maps_install` in `/etc/iiab/local_vars.yml` means install the map program (about 40MB).
    2. `osm_vector_maps_enabled` in `/etc/iiab/local_vars.yml` is not currently in use.  [why if so?]
    3. `osm_vector_maps_installed` in `/etc/iiab/iiab_state.yml` means it's been installed.  [no longer means "install a functioning world map to zoom 10 (about 2.8GB)" right?]
2. There's an "Install IIAB Maps" page (http://box/osm-vector-maps/installer/) separate from the Admin Console, to help you download Map Pack(s) for your favorite continents, and Hi-Res Satellite Photo Imagery for (square) local regions.  This lets you to add satellite photos with 4 more levels of zoom (i.e. zoom level 10-13) to get 16X the resolution (i.e. 19 x 19 m pixels) &mdash; as compared to zoom level 9 (i.e. 306 x 306 m pixels) everywhere else.
3. OpenStreetMap Vector Maps: multiple Map Packs can be installed (one "continent" at a time).
4. Hi-Res Satellite Photos: multiple local regions can be installed (one "square" at a time).
5. Hi-Res Satellite Photos can be downloaded for any 100 x 100 km, 300 x 300 km, or 1000 x 1000 km square region (around a selected map point).
6. More recent OSM data is used in the vector tiles (2017 => 2019).  [is this included in all 12 Map Packs? who did the 2019 updates?]
7. The base install (world view) increases zoom levels from 0-9 to 0-10, so that city search is successful more of the time.  [is this included in all 12 Map Packs?]
8. There is a new drag-and-drop feature which permits the student to add descriptions and pictures about local points of interest, and then save and restore them using their local browser.  [by right clicking? any teacher tips and/or hints as to how this works?]

#### Please also see our IIAB Maps doc: https://github.com/iiab/iiab/wiki/IIAB-Maps
