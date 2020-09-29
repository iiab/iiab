## What's Changed in Maps for the IIAB 7.2 Release?

1. Some variables have newer meanings:
    1. `osm_vector_maps_install` in `/etc/iiab/local_vars.yml` means install the map program (about 40MB).
    2. `osm_vector_maps_enabled` in `/etc/iiab/local_vars.yml` is not currently in use [why if so?].
    3. `osm_vector_maps_installed` in `/etc/iiab/iiab_state.yml` means it's been installed [no longer means "install a functioning world map to zoom 10 (about 2.8GB)" right?].
2. There's an "Install IIAB Maps" page (http://box/osm-vector-maps/installer/) separate from the Admin Console, to help you download both Map Pack(s) for your favorite continents, and Hi-Res Satellite Imagery for (square) local regions.  That means 4 more levels of satellite zoom (i.e. zoom level 10 to 13) which means 16 times the resolution [5x5 km to 5x5 m pixels implies 1000X the resolution ?] as compared to zoom level 9).
3. OpenStreetMap Vector Maps: multiple Map Packs can be installed, one "continent" at a time.
4. Hi-Res Satellite Photos: multiple (square) local regions can be installed, one at a time.
5. Hi-Res Satellite Photos can be downloaded for any 100x100 km, 300x300 km, or 1000x1000 km region, around a selected map point.
6. More recent OSM data is used in the vector tiles (2017 => 2019) [is this included in all 12 Map Packs?].
7. The base install (world view) increases zoom levels from 0-9 to 0-10, so that city search is successful more of the time [is this included in all 12 Map Packs?].
8. There is a new drag-and-drop feature which permits the student to add descriptions and pictures about local points of interest, and then save and restore them using their local browser [how does one do this?].

#### Please also see our IIAB Maps doc: https://github.com/iiab/iiab/wiki/IIAB-Maps
