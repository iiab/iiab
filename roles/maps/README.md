# How do I try IIAB's new maps as of 2025-11-14?

1. If you want **~170 MB** = 85 MB vector + 85 MB satellite, set these variables in [/etc/iiab/local_vars.yml](https://wiki.iiab.io/go/FAQ#What_is_local_vars.yml_and_how_do_I_customize_it?) before installing IIAB software:

   ```
   osm_vector_maps_install: False
   osm_vector_maps_enabled: False

   maps_install: True
   maps_enabled: True

   maps_vector_quality: ne
   maps_sat_zoom: 7
   ```

2. Or if you want **~3.1 GB** = 1.9 GB vector + 1.2 GB satellite, include:

   ```
   maps_vector_quality: osm-z9
   maps_sat_zoom: 9
   ```

3. Or if you want **~168 GB** = 78 GB vector + 80 GB satellite, include:

   ```
   maps_vector_quality: osm-full
   maps_sat_zoom: 12
   ```

# Further options & detail:

* https://github.com/iiab/iiab/blob/master/roles/maps/defaults/main.yml
* [PR #4120](https://github.com/iiab/iiab/pull/4120)
* IIAB integration thanks to [Dan Krol](https://github.com/orblivion)

# Extra attributions:

* UI
  * https://github.com/maps-black/maps.black?tab=MIT-1-ov-file#readme
  * https://github.com/maplibre/maplibre-gl-js
  * https://github.com/maplibre/maplibre-gl-geocoder?tab=ISC-1-ov-file#readme
* Search (for now): https://github.com/osm-search/Nominatim?tab=GPL-3.0-1-ov-file#readme
* Other credits: https://github.com/iiab/iiab/blob/master/roles/www_base/files/html/html/credits.html
