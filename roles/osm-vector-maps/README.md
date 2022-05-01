## What's New with IIAB Maps?

1. If you install [IIAB 8.0+](https://github.com/iiab/iiab/wiki/IIAB-8.0-Release-Notes) (a pre-release is fine!) with [IIAB Maps](https://github.com/iiab/iiab/wiki/IIAB-Maps) an **Install IIAB Maps** page is available (http://box/osm-vector-maps/installer/) with [instructions](https://github.com/iiab/iiab/wiki/IIAB-Maps#how-do-i-install-map-packs-and-satellite-photo-regions-on-iiab-80-), separate from IIAB's Admin Console:
   1. This [very visual page](https://user-images.githubusercontent.com/2458907/94740848-46c4eb00-0341-11eb-93ea-e3e4758dce48.png) facilitates selecting/downloading/installing of Map Pack(s) for your favorite "continent(s)".  (SEE 2. BELOW)
   2. You can then use this same page to select/download/install Hi-Res Satellite Photo Region(s) for your local communities.  (SEE 3. BELOW)
   3. All these downloads can now happen 10X to 100X faster, thanks to PR's [iiab/maps#38](https://github.com/iiab/maps/pull/38), [iiab/maps#58](https://github.com/iiab/maps/pull/58) and [iiab/iiab-admin-console#478](https://github.com/iiab/iiab-admin-console/pull/478) !
   4. _When installing OpenStreetMap "continents" (a.k.a. regions), consider either the command-line ([/usr/bin/iiab-install-map-region](https://github.com/iiab/maps/blob/master/osm-source/pages/viewer/scripts/iiab-install-map-region)) or the visual alternative provided by IIAB's Admin Console: http://box.lan/admin > Install Content > Get Map Regions._

2. **Map Packs** no longer bundle both data and program in a .zip file.  All Map Packs are really now just a collection of 3 .mbtiles files:
   1. The main focus of a Map Pack remains Hi-Res Vector Map data from OpenStreetMap, for your selected "continent" — but Lo-Res vector map tiles (2.0 GB .mbtiles) and Lo-Res satellite photos (1.2 GB .mbtiles) are also included for the entire planet.  Read more at: https://github.com/iiab/iiab/wiki/IIAB-Maps
   2. Every Map Pack's OSM vector tile data (originally from 2017, and then September 2019) was updated to [November 2020](https://archive.org/details/osm-vector-mbtiles).
   3. The world view (planetwide OSM vector maps included with all Map Packs) increased zoom levels from 0-9 to 0-10 (2.0 GB osm-planet_z0-z10_2020.mbtiles) so that city search is successful more of the time.
   4. Multiple Map Packs can be downloaded/installed (one "continent" at a time).  However this can waste disk space with duplicate data, and potentially cause rendering slowness in areas where Map Packs overlap ("continent" bounding boxes have been designed to overlap on purpose, so multiple Map Packs are rarely necessary!)

3. **Hi-Res Satellite Photos** can be downloaded/installed for any 100 x 100 km, 300 x 300 km, or 1000 x 1000 km square region (around any map point that you click!)
   1. These new Hi-Res Satellite Photo Regions are "squares" with 4 additional levels of satellite photo zoom (i.e. zoom levels 10-13) giving you 16X the resolution (i.e. 19 x 19 m pixels) and 256X more photographic information density.
   2. As compared to Lo-Res Satellite Photos i.e. zoom levels 0-9 (305 x 305 m pixels) everywhere else on the planet (1.2 GB satellite_z0-z9_2020.mbtiles is included with all Map Packs).  (SEE 2. ABOVE)
   3. Multiple Hi-Res Satellite Photo Regions can be downloaded/installed (one "square" region at a time, thankfully duplicate disk space is avoided when such "squares" overlap!)

4. Some variables have newer meanings:
   1. `osm_vector_maps_install` in [/etc/iiab/local_vars.yml](https://wiki.iiab.io/go/FAQ#What_is_local_vars.yml_and_how_do_I_customize_it.3F) means install the map program and 7 basic levels of zoom (48MB for OSM + 25 MB for satellite photos).
   2. `osm_vector_maps_enabled` in [/etc/iiab/local_vars.yml](https://wiki.iiab.io/go/FAQ#What_is_local_vars.yml_and_how_do_I_customize_it.3F) is once again standardized, solving #2484 install delays.
   3. `osm_vector_maps_installed` in `/etc/iiab/iiab_state.yml` means a functioning world map with 7 levels of zoom (z0-z6) has been installed — i.e. a preview of IIAB's mapping system that helps you select Maps Pack(s) and Hi-Res Satellite Photo Region(s) to download and install on your IIAB.  (SEE 1. ABOVE)

5. **Drag-and-Drop Map Overlays** — try this by dragging and dropping any relevant GeoJSON file onto the IIAB Maps (http://box/maps) in your browser!  For example try this GeoJSON file, to explore the shape of gerrymandered US Congressional districts: https://eric.clst.org/assets/wiki/uploads/Stuff/gz_2010_us_500_11_20m.json


#### Please also see the IIAB Maps doc: https://github.com/iiab/iiab/wiki/IIAB-Maps

#### How to (wipe and) upgrade IIAB Maps
<!-- Notes on upgrading from a maps 7.2 to maps 7.3 -->

In April 2022, IIAB revised `/etc/iiab/map-catalog.json`, `/library/www/html/common/assets/adm-map-catalog.json`, associated programs, and OSM continent/region `.mbtiles` files.

_It's best to start fresh with a new install of IIAB if you want the latest maps!_

Or, if you absolutely must attempt an upgrade (ENTIRELY AT YOUR OWN RISK) run the following &mdash; to attempt to delete your existing maps &mdash; and then add new IIAB Maps:

 ```
 sudo rm -rf /library/www/osm-vector-maps
 cd /opt/iiab/iiab
 sudo git pull
 sudo ./runrole --reinstall osm-vector-maps
 sudo iiab-install-map-region <CONTINENT>.mbtiles
 ```

Where `<CONTINENT>.mbtiles` is one of the major region files (with "2020" in its filename) that you choose from: http://timmoody.com/iiab-files/maps/

<!--
cd /library/www/
rm -rf osm-vector-maps/
nano /etc/iiab/iiab_state.yml    # Delete line 'osm_vector_maps_installed: True'
git remote add ghunt git@github.com:/georgejhunt/iiab
git fetch --all
git checkout -b maps7.3 ghunt/maps7.3
./runroles osm-vector-maps
-->
