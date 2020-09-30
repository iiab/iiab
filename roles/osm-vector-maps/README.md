## What's Changed in Maps for the IIAB 7.2 Release?

1. Some variables have newer meanings:
    1. `osm_vector_maps_install` in [/etc/iiab/local_vars.yml](http://wiki.laptop.org/go/IIAB/FAQ#What_is_local_vars.yml_and_how_do_I_customize_it.3F) means install the map program (about 40MB).
    2. `osm_vector_maps_enabled` in [/etc/iiab/local_vars.yml](http://wiki.laptop.org/go/IIAB/FAQ#What_is_local_vars.yml_and_how_do_I_customize_it.3F) was not in use.  [CAN WE SPELL OUT WHY?  SEE tasks/nginx.yml AND TKTS BELOW]
    3. `osm_vector_maps_installed` in [/etc/iiab/local_vars.yml](http://wiki.laptop.org/go/IIAB/FAQ#What_is_local_vars.yml_and_how_do_I_customize_it.3F) means a functioning world map to with 7 levels of zoom (z0-z6) has been installed.  [LIKELY EXPLANATION: THE HOURLONG WAIT FOR 2.8 GB TO DOWNLOAD 10 ZOOM LEVELS WAS REDUCED, TO A PREVIEW OF 7 ZOOM LEVELS, PER #2484, PR #2486, PR #2487 ETC]
2. There's an "Install IIAB Maps" page (http://box/osm-vector-maps/installer/) separate from the Admin Console, to help you download Map Pack(s) for your favorite continents, and Hi-Res Satellite Photo Regions serving local communities.
    1. Hi-Res Satellite Photo Regions are 'squares' with 4 more levels of satellite photo zoom (i.e. zoom levels 10-13) giving you 16X the resolution (i.e. 19 x 19 m pixels) and 256X more photographic information density.
    2. As compared to Lo-Res Satellite Photos i.e. zooms level 0-9 (305 x 305 m pixels) everywhere else on the planet.
3. OpenStreetMap Vector Maps: multiple Map Packs can be installed (one "continent" at a time).
4. Hi-Res Satellite Photos: multiple local regions can be installed (one "square" at a time).
5. Hi-Res Satellite Photos can be downloaded for any 100 x 100 km, 300 x 300 km, or 1000 x 1000 km square region (around a selected map point).
6. Map Packs' OSM vector tile data (from 2017) was updated to 2019 data.  [WHO GENERATED THE 2019 VECTOR TILES?  WHEN IN 2019?]
7. The base install (world view) increases zoom levels from 0-9 to 0-10, so that city search is successful more of the time.
8. There is a new drag-and-drop feature which permits the student to add descriptions and pictures about local points of interest, and then save and restore them using their local browser.  [BY RIGHT CLICKING?  ANY TEACHER TIPS AND/OR HINTS AS TO HOW THIS WORKS?]

#### Please also see our IIAB Maps doc: https://github.com/iiab/iiab/wiki/IIAB-Maps
