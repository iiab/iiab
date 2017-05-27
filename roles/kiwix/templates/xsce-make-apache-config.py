#!/usr/bin/python
# write out proxy definitions for zim currently loaded

import os, sys, syslog

xsce_zim_path = "/library/zims"
kiwix_apache_config = "/etc/apache2/sites-available/kiwix.conf"

def main ():
    content = xsce_zim_path + "/content/"
    index = xsce_zim_path + "/index/"

    # remove existing file
    try:
        os.remove(kiwix_apache_config)
    except:
        pass

    with open(kiwix_apache_config, 'w') as fp:
       fp.write("RewriteEngine on\n")
       fp.write("ProxyPreserveHost on\n")
       for filename in os.listdir(content):
          zimpos = filename.find(".zim")
          if zimpos != -1:
	     filename = filename[:zimpos]
          fp.write("ProxyPass /%s/ http://localhost:3000/%s/\n" % (filename,filename))
          fp.write("ProxyPassReverse /%s/ http://localhost:3000/%s/\n" % (filename,filename))




if __name__ == "__main__":

    # Run the main routine
    main()

# vim: tabstop=3 shiftwidth=3 expandtab softtabstop=3
