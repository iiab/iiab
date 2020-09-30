## What's Changed in Maps for the IIAB 7.2 Release?

1. Some variables have newer meanings:
    1. `osm_vector_maps_install` in [/etc/iiab/local_vars.yml](http://wiki.laptop.org/go/IIAB/FAQ#What_is_local_vars.yml_and_how_do_I_customize_it.3F) means install the map program (about 40MB).
    2. `osm_vector_maps_enabled` in [/etc/iiab/local_vars.yml](http://wiki.laptop.org/go/IIAB/FAQ#What_is_local_vars.yml_and_how_do_I_customize_it.3F) is once again standardized, solving #2484 install delays.
    3. `osm_vector_maps_installed` in `/etc/iiab/iiab_state.yml` means a functioning world map with 7 levels of zoom (z0-z6) has been installed — i.e. a preview of IIAB's mapping system that helps you select Maps Pack(s) and Satellite Photo Region(s) to download and install on your IIAB.

2. There's a new "Install IIAB Maps" page (http://box/osm-vector-maps/installer/, PR [iiab/maps#29](https://github.com/iiab/maps/pull/29)) separate from IIAB's Admin Console, to facilitate this selecting/downloading/installing of Map Pack(s) for your favorite continents — and then likewise for Hi-Res Satellite Photo Regions serving your local communities.
    1. The new Hi-Res Satellite Photo Regions are 'squares' with 4 more levels of satellite photo zoom (i.e. zoom levels 10-13) giving you 16X the resolution (i.e. 19 x 19 m pixels) and 256X more photographic information density.
    2. As compared to Lo-Res Satellite Photos i.e. zooms level 0-9 (305 x 305 m pixels) everywhere else on the planet.

3. Map Packs no longer bundle both data and program in a .zip file.  All Map Packs are now a collection of 3 .mbtiles files.  The main focus of a Map Pack remains Hi-Res Vector Map data from OpenStreetMap, for your selected "continent," but read more at: https://github.com/iiab/iiab/wiki/IIAB-Maps
4. Multiple Map Packs can be downloaded/installed (one "continent" at a time!)
5. Hi-Res Satellite Photos can be downloaded/installed for any 100 x 100 km, 300 x 300 km, or 1000 x 1000 km square region (around the map point that you click).
6. Hi-Res Satellite Photos: multiple regions can be downloaded/installed (one "square" region at a time, even if they overlap!)
7. Map Packs' OSM vector tile data (from 2017) was updated to data from [September 2019](https://archive.org/details/osm-vector-mbtiles).
8. The world view (planetwide OSM vector maps included with all Map Packs) increases zoom levels from 0-9 to 0-10 (1.8GB osm-planet_z0-z10_2019.mbtiles) so that city search is successful more of the time.
9. There is a new **drag-and-drop** feature that instantly displays map overlays — try to drag any relevant GeoJSON file onto the IIAB Maps (http://box/maps) shown in your browser!  For example try this GeoJSON file, to explore gerrymandered US Congressional districts: https://eric.clst.org/assets/wiki/uploads/Stuff/gz_2010_us_500_11_20m.json
10. Separately: Students can **right-click** on the map to add points, descriptions and photos of local points of interest — and then save and restore them using their local browser!  [CAN ANYBODY SUGGEST TEACHER TIPS AND/OR STUDENT HINTS AS TO HOW THIS WORKS?]

#### Please also see our IIAB Maps doc: https://github.com/iiab/iiab/wiki/IIAB-Maps
