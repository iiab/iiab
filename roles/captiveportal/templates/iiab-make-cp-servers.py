#!/usr/bin/env python3
# read list of online portal checkers, make nginx server blocks 

import os
outstr = ''

os.chdir('{{ iiab_dir }}/roles/captiveportal/templates')
with open('checkurls','r') as urls:
   for line in urls:
      line = line.replace('*','.*')
      outstr += 'server {\n'
      outstr += '    listen 80;\n'
      outstr += '    server_name {};\n'.format(line.strip())
      outstr += '    location / {\n'
      outstr += '        proxy_set_header   X-Forwarded-For $remote_addr;\n'
      outstr += '        proxy_set_header   Host $http_host;\n'
      outstr += '        proxy_pass         "http://127.0.0.1:9090";\n'
      outstr += '    }\n' 
      outstr += '}\n'
#print(outstr)
with open('/etc/nginx/sites-available/capture.conf','w') as config:
   config.write(outstr)

