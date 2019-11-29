#!/usr/bin/env python3
# Scan the osm-vector-maps directory, update the osm-vector-maps-idx.json, add menu-defs

import json

import iiab.iiab_lib as iiab

try:
    import iiab.adm_lib as adm
    adm_cons_installed = True
except:
    adm_cons_installed = False
    pass

def main():
    adm.get_map_catalog()
    #print(json.dumps(map_catalog,indent=2))

    map_menu_def_list = adm.get_map_menu_defs()
    #print((json.dumps(map_menu_def_list,indent=2)))

    previous_idx = adm.read_vector_map_idx()

    installed_maps = adm.get_installed_regions()
    print(installed_maps)

    adm.write_vector_map_idx(installed_maps)

    # For installed regions, check that a menu def exists, and it's on home page
    for fname in installed_maps:
        region = adm.extract_region_from_filename(fname)
        if region == 'maplist': # it is the splash page, display only if no others
            menu_ref = 'en-map_test'
            item = { "perma_ref" : "en-map_test" }
            if len(installed_maps) == 1:
                adm.update_menu_json(menu_ref)
                return
        elif region not in adm.map_catalog['regions']:
            print("Skipping unknown map " + fname)
            continue
        else:
            item = adm.map_catalog['regions'][region]
            menu_ref = item['perma_ref']
            if not (menu_ref in map_menu_def_list):
                print(('creating menu def for %s'%item['perma_ref']))
                adm.create_map_menu_def(region,item['perma_ref'] + '.json')
        # if autoupdate allowed and this is a new region then add to home menu
        if adm.fetch_menu_json_value('autoupdate_menu') and item['perma_ref'] not in previous_idx:
            print(('autoudate of menu items is enabled:%s. Adding %s'%(\
                       adm.fetch_menu_json_value('autoupdate_menu'),region,)))
            adm.update_menu_json(menu_ref)
            # redirect from box/maps to an installed map rather than test page
            with open(adm.CONST.map_doc_root + '/index.html','w') as fp:
                outstr = """<head> \n<meta http-equiv="refresh" content="0; URL=/osm-vector-maps/en-osm-omt_%s " />\n</head>"""%fname
                fp.write(outstr)

if __name__ == '__main__':
   if adm_cons_installed:
      main()