#!/usr/bin/python
# write out proxy definitions for zim currently loaded

import os, sys, syslog

iiab_zim_path = "{{ iiab_zim_path }}"
kiwix_apache_config = "/etc/{{ apache_config_dir }}/kiwix.conf"

def main ():
    content = iiab_zim_path + "/content/"
    index = iiab_zim_path + "/index/"

    # remove existing file
    try:
        os.remove(kiwix_apache_config)
    except:
        pass

    with open(kiwix_apache_config, 'w') as fp:
       fp.write("RewriteEngine on\n")
       fp.write("ProxyPreserveHost on\n")
       fp.write("ProxyPass /kiwix  http://127.0.0.1:3000\n")
       fp.write("ProxyPassReverse /kiwix  http://127.0.0.1:3000\n")

       for filename in os.listdir(content):
          zimpos = filename.find(".zim")
          if zimpos != -1:
	     filename = filename[:zimpos]
          fp.write("RewriteRule %s(.*)  http://127.0.0.1:3000/%s$1 [P]\n"% (filename,filename))
          fp.write("ProxyPassReverse %s$1 http://localhost:3000/%s$1\n" % (filename,filename))




if __name__ == "__main__":

    # Run the main routine
    main()

# vim: tabstop=3 shiftwidth=3 expandtab softtabstop=3
