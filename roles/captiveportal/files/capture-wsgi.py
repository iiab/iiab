#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# using Python's bundled WSGI server

from wsgiref.simple_server import make_server
import subprocess
from dateutil.tz import *
import datetime
import logging
from logging.handlers import RotatingFileHandler
import os
import sys
from jinja2 import Environment, FileSystemLoader
import sqlite3
import re

# Notes on timeout strategy
# every client timestamp is recorded into current_ts
# When splash page is clicked , return 204 timeout starts (via ajax call),
# Return 204 is android (may be different for different versions)
# captive portal redirect is triggered after inactivity timeout, 
# which needs to be longer than period of normal connecetivity checks by OS
# 

# Create the jinja2 environment.
CAPTIVE_PORTAL_BASE = "/opt/iiab/captiveportal"
j2_env = Environment(loader=FileSystemLoader(CAPTIVE_PORTAL_BASE),trim_blocks=True)

# Define time outs
INACTIVITY_TO = 30
PORTAL_TO = 20 # delay after triggered by ajax upon click of link to home page
# I had hoped that returning 204 status after some delay 
#  would dispense with android's "sign-in to network" (no work)


# Get the IIAB variables
sys.path.append('/etc/iiab/')
from iiab_env import get_iiab_env
doc_root = get_iiab_env("WWWROOT")
fully_qualified_domain_name = get_iiab_env("FQDN")


loggingLevel = "DEBUG"
# set up some logging -- selectable for diagnostics
logging.basicConfig(filename='/var/log/apache2/portal.log',format='%(asctime)s.%(msecs)03d:%(name)s:%(message)s', datefmt='%M:%S',level=loggingLevel)
logger = logging.getLogger('/var/log/apache2/portal.log')
handler = RotatingFileHandler("/var/log/apache2/portal.log", maxBytes=100000, backupCount=2)
logger.addHandler(handler)

#PORT={{ captiveportal_port }}
PORT=9090


# Define globals
ANDROID_TRIGGERED=False

logger.debug("")
logger.debug('##########################################')
# what language are we speaking?
lang = os.environ['LANG'][0:2]
logger.debug('speaking: {}'.format(lang))

def tstamp(dtime):
    '''return a UNIX style seconds since 1970 for datetime input'''
    epoch = datetime.datetime(1970, 1, 1,tzinfo=tzutc())
    newdtime = dtime.astimezone(tzutc())
    since_epoch_delta = newdtime - epoch
    return since_epoch_delta.total_seconds()

# ##########database operations ##############
# Use a sqlite database to store per client information
user_db = os.path.join(CAPTIVE_PORTAL_BASE,"users.sqlite")
conn = sqlite3.connect(user_db)
if not os.path.exists(user_db):
    conn.close()
    conn = sqlite3.connect(user_db)
c = conn.cursor()
c.row_factory = sqlite3.Row
c.execute( """create table IF NOT EXISTS users 
            (ip text PRIMARY KEY, mac text, current_ts integer,
            lasttimestamp integer, send204after integer,
            os text, os_version text,
            ymd text)""")

def update_user(ip, mac, system, system_version, ymd):
    sql = "SELECT * FROM users WHERE ip = ?"
    c.execute(sql,(ip,))
    row = c.fetchone()
    if row == None:
        sql = "INSERT INTO users (ip,mac,os,os_version,ymd) VALUES (?,?,?,?,?)" 
        c.execute(sql,(ip, mac, system, system_version, ymd ))
    else:
        sql = "UPDATE users SET  (mac,os,os_version,ymd) = ( ?, ?, ?, ? ) WHERE ip = ?"
        c.execute(sql,(mac, system, system_version, ymd, ip,))
    conn.commit()

def platform_info(ip):
    sql = "select * FROM users WHERE ip = ?"
    c.execute(sql,(ip,))
    row = c.fetchone()
    if row is None: return ('','',)
    return (row['os'],row['os_version'])
        
def timeout_info(ip):
    sql = "select * FROM users WHERE ip = ?"
    c.execute(sql,(ip,))
    row = c.fetchone()
    if row is None: return (0,0,0,)
    return [row['current_ts'],row['lasttimestamp'],row['send204after']]
        
def is_inactive(ip):
    ts=tstamp(datetime.datetime.now(tzutc()))
    current_ts, last_ts, send204after = timeout_info(ip) 
    logger.debug("In is_inactive. current_ts:{}. last_ts:{}. send204after:{}".format(current_ts,last_ts,send204after,))
    if not last_ts:
        return True
    if ts - int(last_ts) > INACTIVITY_TO:
        return True
    else:
        return False

def is_after204_timeout(ip):
    ts=tstamp(datetime.datetime.now(tzutc()))
    current_ts, last_ts, send204after = timeout_info(ip) 
    if send204after == 0: return False
    logger.debug("function: is_after204_timeout send204after:{} current: {}".format(send204after,ts,))
    if not send204after:
        return False
    if ts - int(send204after) > 0:
        return True
    else:
        return False

def set_204after(ip,value):
    global ANDROID_TRIGGERED
    ts=tstamp(datetime.datetime.now(tzutc()))
    sql = 'UPDATE users SET send204after = ?  where ip = ?'
    c.execute(sql,(ts + value,ip,))
    conn.commit()
    ANDROID_TRIGGERED = False

def set_lasttimestamp(ip):
    ts=tstamp(datetime.datetime.now(tzutc()))
    sql = 'UPDATE users SET lasttimestamp = ?  where ip = ?'
    c.execute(sql,(ts,ip,))
    conn.commit()

#  ###################  Action routines based on OS  ################3
def microsoft(environ,start_response):
    print('in microsoft')
    # firefox -- seems both mac and Windows use it
    agent = environ.get('HTTP_USER_AGENT','default_agent')
    if agent.startswith('Mozilla'):
       return home(environ, start_response) 
    logger.debug("sending microsoft redirect")
    response_body = b""
    status = '302 Moved Temporarily'
    response_headers = [('Location','http://box.lan/home'),
            ('Content-type','text/html'),
            ('Content-Length',str(len(response_body)))]
    start_response(status, response_headers)
    return [response_body]

def home(environ,start_response):
    logger.debug("sending direct to home")
    response_body = b""
    status = '302 Moved Temporarily'
    response_headers = [('Location','http://' + fully_qualified_domain_name + '/home'),
            ('Content-type','text/html'),
            ('Content-Length',str(len(response_body)))]
    start_response(status, response_headers)
    return [response_body]

def android(environ, start_response):
    global ANDROID_TRIGGERED
    if  environ.get('HTTP_X_FORWARDED_FOR'):
        ip = environ['HTTP_X_FORWARDED_FOR'].strip()
    else: 
        ip = environ['REMOTE_ADDR'].strip()
    system,system_version = platform_info(ip)
    if system_version is None:
       return  put_302(environ, start_response)
    if system_version[0:1] < '6':
        logger.debug("system < 6:{}".format(system_version))
        location = '/android_splash'
        set_204after(ip,0)
    elif system_version[:1] >= '7':
        location = "http://" + fully_qualified_domain_name + "/home"
    else:
        #set_204after(ip,20)
        location = '/android_https'
    agent = environ.get('HTTP_USER_AGENT','default_agent')
    response_body = b"hello"
    status = '302 Moved Temporarily'
    response_headers = [('Location',location)]
    start_response(status, response_headers)
    return [response_body]

def android_splash(environ, start_response):
    en_txt={ 'message':"Click on the button to go to the IIAB home page",\
            'btn1':"GO TO IIAB HOME PAGE", \
            "FQDN": fully_qualified_domain_name, \
            'doc_root':get_iiab_env("WWWROOT") }
    es_txt={ 'message':"Haga clic en el botón para ir a la página de inicio de IIAB",\
            "FQDN": fully_qualified_domain_name, \
            'btn1':"IIAB",'doc_root':get_iiab_env("WWWROOT")}
    txt = en_txt
    if lang == "en":
        txt = en_txt
    elif lang == "es":
        txt = es_txt
    response_body = str(j2_env.get_template("simple.template").render(**txt))
    response_body = response_body.encode()
    status = '200 OK'
    response_headers = [('Content-type','text/html'),
            ('Content-Length',str(len(response_body)))]
    start_response(status, response_headers)
    return [response_body]

def android_https(environ, start_response):
    en_txt={ 'message':"""Please ignore the SECURITY warning which appears after clicking the first button""",\
             'btn2':'Click this first Go to the browser we need',\
             'btn1':'Then click this to go to IIAB home page',\
             "FQDN": fully_qualified_domain_name, \
            'doc_root':get_iiab_env("WWWROOT") }
    es_txt={ 'message':"Haga clic en el botón para ir a la página de inicio de IIAB",\
            "FQDN": fully_qualified_domain_name, \
            'btn1':"IIAB",'doc_root':get_iiab_env("WWWROOT")}
    txt = en_txt
    if lang == "en":
        txt = en_txt
    elif lang == "es":
        txt = es_txt
    response_body = str(j2_env.get_template("simple.template").render(**txt))
    response_body = response_body.encode()
    status = '200 OK'
    response_headers = [('Content-type','text/html'),
            ('Content-Length',str(len(response_body)))]
    start_response(status, response_headers)
    return [response_body]

def mac_splash(environ,start_response):
    print('in mac_splash')
    logger.debug("in function mac_splash")
    en_txt={ 'message': "Click on the button to go to the IIAB home page",\
            'btn1': "GO TO IIAB HOME PAGE",'success_token': 'Success',
            "FQDN": fully_qualified_domain_name, \
            'doc_root':get_iiab_env("WWWROOT")}
    es_txt={ 'message':"Haga clic en el botón para ir a la página de inicio de IIAB",\
            "FQDN": fully_qualified_domain_name, \
            'btn1':"IIAB",'doc_root':get_iiab_env("WWWROOT")}
    txt = en_txt
    if lang == "en":
        txt = en_txt
    elif lang == "es":
        txt = es_txt
    set_lasttimestamp(ip)
    response_body = str(j2_env.get_template("mac.template").render(**txt))
    response_body = response_body.encode()
    status = '200 Success'
    response_headers = [('Content-type','text/html'),
            ('Content-Length',str(len(response_body)))]
    start_response(status, response_headers)
    return [response_body]

def macintosh(environ, start_response):
    print('in macintosh')
    global ip
    logger.debug("in function mcintosh")
    #print >> sys.stderr , "Geo Print to stderr" + environ['HTTP_HOST']
    if not is_inactive(ip):
        set_lasttimestamp(ip)
        return success(environ,start_response)
    # determine if it is time to redirect again
    if is_after204_timeout(ip):
        set_204after(ip,10)
        response_body = """<html><head><script>
            window.location.reload(true)
            </script></body></html>"""
        response_body = response_body.encode()
        status = '302 Moved Temporarily'
        response_headers = [('content','text/html')]
        start_response(status, response_headers)
        return [response_body]
    else:
        return mac_splash(environ,start_response)

# =============  Return html pages  ============================
def banner(environ, start_response):
    status = '200 OK'
    headers = [('Content-type', 'image/png')]
    start_response(status, headers)
    image = open("{}/js-menu/menu-files/images/iiab_banner6.png".format(doc_root), "rb").read()
    return [image]

def bootstrap(environ, start_response):
    logger.debug("in bootstrap")
    status = '200 OK'
    headers = [('Content-type', 'text/javascript')]
    start_response(status, headers)
    boot = open("{}/common/js/bootstrap.min.js".format(doc_root), "rb").read() 
    return [boot]

def jquery(environ, start_response):
    logger.debug("in jquery")
    status = '200 OK'
    headers = [('Content-type', 'text/javascript')]
    start_response(status, headers)
    boot = open("{}/common/js/jquery.min.js".format(doc_root), "rb").read() 
    return [boot]

def bootstrap_css(environ, start_response):
    logger.debug("in bootstrap_css")
    status = '200 OK'
    headers = [('Content-type', 'text/css')]
    start_response(status, headers)
    boot = open("{}/common/css/bootstrap.min.css".format(doc_root), "rb").read() 
    return [boot]

def null(environ, start_response):
    status = '404 Not Found'
    headers = [('Content-type', 'text/html')]
    start_response(status, headers)
    return [b""]

def success(environ, start_response):
    status = '200 ok'
    html = b'<html><head><title>Success</title></head><body>Success</body></html>'
    headers = [('Content-type', 'text/html')]
    start_response(status, headers)
    return [html]

def put_204(environ, start_response):
    status = '204 No Data'
    response_body = b''
    response_headers = [('Content-type','text/html'),
            ('Content-Length',str(len(response_body)))]
    start_response(status, response_headers)
    logger.debug("in function  put_204: sending 204 html response")
    return [response_body]

def put_302(environ, start_response):
    status = '302 Moved Temporarily'
    response_body = b''
    location = "http://" + fully_qualified_domain_name + "/home"
    response_headers = [('Content-type','text/html'),
            ('Location',location), 
            ('Content-Length',str(len(response_body)))]
    start_response(status, response_headers)
    logger.debug("in function  put_302: sending 302 html response")
    return [response_body]

def parse_agent(agent):
    system = ''
    system_version = ''
    match = re.search(r"(Android)\s([.\d]*)",agent)
    if match:
        system = match.group(1)
        system_version = match.group(2)
    match = re.search(r"(OS X)\s([\d_]*)",agent)
    if match:
        system = match.group(1)
        system_version = match.group(2)
    match = re.search(r"(iPhone OS)\s([\d_]*)",agent)
    if match:
        system = match.group(1)
        system_version = match.group(2)
    match = re.search(r"(Windows NT)\s([\d.]*)",agent)
    if match:
        system = match.group(1)
        system_version = match.group(2)
    match = re.search(r"(Microsoft NCSI)",agent)
    if match:
        system = match.group(1)
        system_version = "8"
    return (system, system_version)

#
# ================== Start serving the wsgi application  =================
def application (environ, start_response):
   global ip
   global CATCH
   global LIST
   global INACTIVITY_TO
   global ANDROID_TRIGGERED

   if  'HTTP_X_FORWARDED_FOR' in environ:
      ip = environ['HTTP_X_FORWARDED_FOR'].strip()
   else:
      data = ['{}: {}\n'.format(key, value) for key, value in sorted(environ.items()) ]
      #logger.debug("need the correct ip:{}".format(data))
      ip = environ['REMOTE_ADDR'].strip()
   cmd="arp -an {}|gawk \'{{print $4}}\'".format(ip)
   mac = subprocess.check_output(cmd, shell=True)
   data = []
   data.append("host: {}\n".format(environ['HTTP_HOST']))
   data.append("path: {}\n".format(environ['PATH_INFO']))
   data.append("query: {}\n".format(environ['QUERY_STRING']))
   data.append("ip: {}\n".format(ip))
   agent = environ.get('HTTP_USER_AGENT','default_agent')
   data.append("AGENT: {}\n".format(agent))
   logger.debug(data)
   #print(data)
   found = False
   return_204_flag = "False"

   # record the activity with this ip
   ts=tstamp(datetime.datetime.now(tzutc()))
   sql = "INSERT or IGNORE INTO users (current_ts,ip) VALUES (?,?)" 
   c.execute(sql,(ts,ip,))
   sql = "UPDATE users SET current_ts = ? where ip = ?" 
   c.execute(sql,(ts,ip,))
   if c.rowcount == 0:
      logger.debug("failed UPDATE  users SET current_ts = {} WHERE ip = {}".format(ts,ip,)) 
   conn.commit()
   ymd=datetime.datetime.today().strftime("%y%m%d-%H%M")

   system,system_version = parse_agent(agent)
   if system != '':
      update_user(ip, mac, system, system_version, ymd)

   #######   Return pages based upon PATH   ###############
   # do more specific stuff first
   if  environ['PATH_INFO'] == "/iiab_banner6.png":
      return banner(environ, start_response) 

   if  environ['PATH_INFO'] == "/bootstrap.min.js":
      return bootstrap(environ, start_response) 

   if  environ['PATH_INFO'] == "/bootstrap.min.css":
      return bootstrap_css(environ, start_response) 

   if  environ['PATH_INFO'] == "/jquery.min.js":
      return jquery(environ, start_response) 

   if  environ['PATH_INFO'] == "/favicon.ico":
      return null(environ, start_response) 

   if  environ['PATH_INFO'] == "/home_selected":
      # the js link to home page triggers this ajax url 
      # mark the sign-in conversation completed, return 204 or Success or Success
      ANDROID_TRIGGERED = True
      #data = ['{}: {}\n'.format(key, value) for key, value in sorted(environ.items()) ]
      #logger.debug("need the correct ip:{}".format(data))
      logger.debug("function: home_selected. Setting flag to return_204")
      #print("setting flag to return_204")
      set_204after(ip,PORTAL_TO)
      set_lasttimestamp(ip)
      status = '200 OK'
      headers = [('Content-type', 'text/html')]
      start_response(status, headers)
      return [""]

   #### parse OS platform based upon URL  ##################
   # mac
   if  environ['PATH_INFO'] == "/mac_splash":
      return mac_splash(environ, start_response) 

   if  environ['PATH_INFO'] == "/step2":
      return step2(environ, start_response) 

   if environ['HTTP_HOST'] == "captive.apple.com" or\
     environ['HTTP_HOST'] == "appleiphonecell.com" or\
     environ['HTTP_HOST'] == "*.apple.com.edgekey.net" or\
     environ['HTTP_HOST'] == "gsp1.apple.com" or\
     environ['HTTP_HOST'] == "apple.com" or\
     environ['HTTP_HOST'] == "www.apple.com": 
     current_ts, last_ts, send204after = timeout_info(ip) 
     if not send204after:
          # take care of uninitialized state
          set_204after(ip,0)
     return macintosh(environ, start_response) 

   # android
   if  environ['PATH_INFO'] == "/android_splash":
     return android_splash(environ, start_response) 
   if  environ['PATH_INFO'] == "/android_https":
     return android_https(environ, start_response) 
   if environ['HTTP_HOST'] == "clients3.google.com" or\
      environ['HTTP_HOST'] == "mtalk.google.com" or\
      environ['HTTP_HOST'] == "alt7-mtalk.google.com" or\
      environ['HTTP_HOST'] == "alt6-mtalk.google.com" or\
      environ['HTTP_HOST'] == "connectivitycheck.android.com" or\
      environ['PATH_INFO'] == "/gen_204" or\
      environ['HTTP_HOST'] == "connectivitycheck.gstatic.com":
      current_ts, last_ts, send204after = timeout_info(ip) 
      logger.debug("current_ts: {} last_ts: {} send204after: {}".format(current_ts, last_ts, send204after,))
      if not last_ts or (ts - int(last_ts) > INACTIVITY_TO):
          return android(environ, start_response) 
      elif is_after204_timeout(ip):
          return put_204(environ,start_response)
      return android(environ, start_response) 

   # microsoft
   if environ['HTTP_HOST'] == "ipv6.msftncsi.com" or\
     environ['HTTP_HOST'] == "detectportal.firefox.com" or\
     environ['HTTP_HOST'] == "ipv6.msftncsi.com.edgesuite.net" or\
     environ['HTTP_HOST'] == "www.msftncsi.com" or\
     environ['HTTP_HOST'] == "www.msftncsi.com.edgesuite.net" or\
     environ['HTTP_HOST'] == "www.msftconnecttest.com" or\
     environ['HTTP_HOST'] == "www.msn.com" or\
     environ['HTTP_HOST'] == "teredo.ipv6.microsoft.com" or\
     environ['HTTP_HOST'] == "teredo.ipv6.microsoft.com.nsatc.net": 
     return microsoft(environ, start_response) 

   logger.debug("executing the default 302 response. [{}".format(data))
   return put_302(environ,start_response)

# Instantiate the server
if __name__ == "__main__":
    httpd = make_server (
    "", # The host name
    PORT, # A port number where to wait for the request
    application # The application object name, in this case a function
    )

    httpd.serve_forever()
#vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4 background=dark

