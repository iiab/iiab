#!/usr/bin/python3
import requests, jinja2, json, yaml

mail_yml = yaml.safe_load(open("../defaults/main.yml").read())

def render(source, data):
    rtemplate = jinja2.Environment(loader=jinja2.BaseLoader).from_string(source)
    return rtemplate.render(**data)

catalog = {
    "vector": mail_yml['iiab_map_host_url'] + '/' + render(mail_yml['maps_dot_black_vector_tiles']['osm-z14'], mail_yml),
    "satellite": mail_yml['iiab_map_host_url'] + '/' + render(mail_yml['maps_dot_black_satellite_tiles'][13], mail_yml),
    "terrain": mail_yml['iiab_map_host_url'] + '/' + render(mail_yml['maps_dot_black_terrain_tiles'][10], mail_yml),
}

for url in catalog.values():
    assert requests.head(url).status_code == 200, "Error with URL: " + url

open("catalog.json", "w").write(json.dumps(catalog))
