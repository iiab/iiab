# How do I try IIAB's new maps as of 2025-12-20?

To configure your map, set the following variables (for the option your choose!) in [/etc/iiab/local_vars.yml](https://wiki.iiab.io/go/FAQ#What_is_local_vars.yml_and_how_do_I_customize_it?) before installing IIAB software:

1. If you want **~170 MB** = 85 MB vector (Lower detail, up to zoom 8, from naturalearth) + 85 MB satellite (up to zoom 7), 

   ```
   osm_vector_maps_install: False
   osm_vector_maps_enabled: False

   maps_install: True
   maps_enabled: True

   maps_vector_quality: ne
   maps_sat_zoom: 7
   ```

2. Or if you want **~3.1 GB** = 1.9 GB vector (Higher detail, up to zoom 9, from openstreetmap) + 1.2 GB satellite (up to zoom 9), include:

   ```
   maps_vector_quality: osm-z9
   maps_sat_zoom: 9
   ```

3. Or if you want **~168 GB** = 78 GB vector (Higher detail, up to zoom 14, including 3d buildings, from openstreetmap) + 80 GB satellite (up to zoom 12), include:

   ```
   maps_vector_quality: osm-full
   maps_sat_zoom: 12
   ```

# Installation Tips

For these large file downloads:

* If there is an interruption and you need to run it again, it should resume where it left off.
* If you want to see download progress, read the ansible output for instructions.

# Further options & detail:

* https://github.com/iiab/iiab/blob/master/roles/maps/defaults/main.yml
* [PR #4120](https://github.com/iiab/iiab/pull/4120)
* Map data files as of 2025-12-10: https://iiab.switnet.org/maps/1/
* IIAB integration thanks to [Dan Krol](https://github.com/orblivion)

# Extra attributions:

* UI
  * https://github.com/maps-black/maps.black#readme
  * https://github.com/maplibre/maplibre-gl-js
  * https://github.com/maplibre/maplibre-gl-geocoder?tab=ISC-1-ov-file#readme
* Search (for now): https://github.com/osm-search/Nominatim?tab=GPL-3.0-1-ov-file#readme
* Other credits: https://github.com/iiab/iiab/blob/master/roles/www_base/files/html/html/credits.html
