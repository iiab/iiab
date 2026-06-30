#!/usr/bin/python3
import requests, jinja2, json, yaml

# If you are installing or configuring IIAB Maps, *you should ignore `/opt/iiab/iiab/maps-catalog.json`*.
#
# But in case you're curious:
#
# `maps-catalog.json` is a catalog of the latest available IIAB Maps data. Unlike just about everything else in this repository, this file is not used directly by the IIAB Maps installation process. Instead, it is made to requested by IIAB Maps _from Github_ during installation and map upgrades. This way, as soon as a map data update is made available, we can update this file on Github and it can be installed without upgrading all of Maps on your IIAB.

# TODO mirrros

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
    "vector": mail_yml['iiab_map_host_url'] + '/' + render(mail_yml['maps_dot_black_vector_tiles']['osm-z14'], mail_yml),
    "satellite": mail_yml['iiab_map_host_url'] + '/' + render(mail_yml['maps_dot_black_satellite_tiles'][13], mail_yml),
    "terrain": mail_yml['iiab_map_host_url'] + '/' + render(mail_yml['maps_dot_black_terrain_tiles'][10], mail_yml),
}

for key, url in catalog.items():
    if key != "_README":
        assert requests.head(url).status_code == 200, "Error with URL: " + url

open("../maps-catalog.json", "w").write(json.dumps(catalog, sort_keys=True, indent=4))
