#!/usr/bin/python3
import requests, jinja2, json, yaml

# TODO - this message doesn't apply to the copy of this file that gets cached
# in /etc/iiab/ copy since that one is actually up to date
# If you are installing or configuring IIAB Maps, *you should ignore `/opt/iiab/iiab/roles/maps/maps-catalog.json`*.
#
# But in case you're curious:
#
# `maps-catalog.json` is a catalog of the latest available IIAB Maps data. Unlike just about everything else in this repository, this file is not used directly by the IIAB Maps installation process. Instead, it is made to requested by IIAB Maps _from Github_ during installation and map upgrades. This way, as soon as a map data update is made available, we can update this file on Github and it can be installed without upgrading all of Maps on your IIAB.

# TODO put dates etc directly into this file, not in main.yml
mail_yml = yaml.safe_load(open("defaults/main.yml").read())

def render(source, data):
    rtemplate = jinja2.Environment(loader=jinja2.BaseLoader).from_string(source)
    return rtemplate.render(**data)

catalog = {
    "_README": [
        "If you are installing or configuring",
        "IIAB Maps, you should ignore this file.",
        "See /opt/iiab/iiab/maps/generate-catalog.py",
        "for more info.",
    ],
    "vector": {
        "14":     mail_yml['iiab_map_host_url'] + '/' + render(mail_yml['maps_dot_black_vector_tiles']['osm-z14'], mail_yml),
        "11":     mail_yml['iiab_map_host_url'] + '/' + render(mail_yml['maps_dot_black_vector_tiles']['osm-z11'], mail_yml),
        "nat-z8": mail_yml['iiab_map_host_url'] + '/' + render(mail_yml['maps_dot_black_vector_tiles']['nat-z8'], mail_yml),

        "1":      mail_yml['iiab_map_host_url'] + '/' + render(mail_yml['maps_dot_black_vector_tiles']['osm-z1'], mail_yml),
    },
    "satellite": {
       "7":       mail_yml['iiab_map_host_url'] + '/' + render(mail_yml['maps_dot_black_satellite_tiles'][7], mail_yml),
       "9":       mail_yml['iiab_map_host_url'] + '/' + render(mail_yml['maps_dot_black_satellite_tiles'][9], mail_yml),
       "11":      mail_yml['iiab_map_host_url'] + '/' + render(mail_yml['maps_dot_black_satellite_tiles'][11], mail_yml),
       "12":      mail_yml['iiab_map_host_url'] + '/' + render(mail_yml['maps_dot_black_satellite_tiles'][12], mail_yml),
       "13":      mail_yml['iiab_map_host_url'] + '/' + render(mail_yml['maps_dot_black_satellite_tiles'][13], mail_yml),

       "4":       mail_yml['iiab_map_host_url'] + '/' + render(mail_yml['maps_dot_black_satellite_tiles'][4], mail_yml),
    },
    "terrain": {
        "7":      mail_yml['iiab_map_host_url'] + '/' + render(mail_yml['maps_dot_black_terrain_tiles'][7], mail_yml),
        "8":      mail_yml['iiab_map_host_url'] + '/' + render(mail_yml['maps_dot_black_terrain_tiles'][8], mail_yml),
        "9":      mail_yml['iiab_map_host_url'] + '/' + render(mail_yml['maps_dot_black_terrain_tiles'][9], mail_yml),
        "10":     mail_yml['iiab_map_host_url'] + '/' + render(mail_yml['maps_dot_black_terrain_tiles'][10], mail_yml),
        "none":   mail_yml['iiab_map_host_url'] + '/' + "terrarium-none.pmtiles",
    },
}

for maptype, zooms in catalog.items():
    if maptype != "_README":
        for zoom, url in zooms.items():
            assert requests.head(url).status_code == 200, "Error with URL: " + url

open("maps-catalog.json", "w").write(json.dumps(catalog, sort_keys=True, indent=4))
