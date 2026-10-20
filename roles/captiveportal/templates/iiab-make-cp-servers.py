#!/usr/bin/env python3
# read list of online portal checkers, make nginx server blocks 

import os
outstr = ''

# Read the deployed list so role reruns use the same checkurls file as
# iiab-divert-to-nginx.
os.chdir('/opt/iiab/captiveportal')
with open('checkurls','r') as urls:
   for line in urls:
      line = line.replace('*','.*')
      outstr += 'server {\n'
      outstr += '    listen 80;\n'
      outstr += '    server_name {};\n'.format(line.strip())
      outstr += '    location / {\n'
      outstr += '        include uwsgi_params;\n'
      outstr += '        uwsgi_param HTTP_HOST $http_host;\n'
      outstr += '        uwsgi_param SERVER_NAME $server_name;\n'
      outstr += '        uwsgi_param HTTP_X_FORWARDED_FOR $remote_addr;\n'
      outstr += '        uwsgi_pass unix:///run/uwsgi/captiveportal.socket;\n'
      outstr += '    }\n' 
      outstr += '}\n'
#print(outstr)
with open('/etc/nginx/sites-available/capture.conf','w') as config:
   config.write(outstr)
