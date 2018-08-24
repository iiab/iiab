#! /usr/bin/env python
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
CAPTIVE_PORTAL_BASE = "/opt/iiab/captive-portal"
j2_env = Environment(loader=FileSystemLoader(CAPTIVE_PORTAL_BASE),trim_blocks=True)

# Define time outs
INACTIVITY_TO = 30
PORTAL_TO = 0 # delay after triggered by ajax upon click of link to home page
# I had hoped that returning 204 status after some delay 
#  would dispense with android's "sign-in to network" (no work)


# Get the IIAB variables
sys.path.append('/etc/iiab/')
from iiab_env import get_iiab_env
doc_root = get_iiab_env("WWWROOT")

# make a way to find new URLs queried by new clients
# CATCH substitues this server for apache at port 80
CATCH = False
if len(sys.argv) > 1 and sys.argv[1] == '-d':
    CATCH = True
    PORT=80
else:
    PORT=9090

# set up some logging -- selectable for diagnostics
# Create dummy iostream to capture stderr and stdout
class StreamToLogger(object):
    """
    Fake file-like stream object that redirects writes to a logger instance.
    """
    def __init__(self, logger, log_level=logging.INFO):
        self.logger = logger
        self.log_level = log_level
        self.linebuf = ''

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.log_level, line.rstrip())

if len(sys.argv) > 1 and sys.argv[1] == '-l':
    loggingLevel = logging.DEBUG
else:
    loggingLevel = logging.ERROR
loggingLevel = logging.DEBUG
logging.basicConfig(filename='/var/log/apache2/portal.log',format='%(asctime)s.%(msecs)03d:%(name)s:%(message)s', datefmt='%M:%S',level=loggingLevel)


logger = logging.getLogger('/var/log/apache2/portal.log')
handler = RotatingFileHandler("/var/log/apache2/portal.log", maxBytes=100000, backupCount=2)
logger.addHandler(handler)


# divert stdout and stderr to logger
stdout_logger = logging.getLogger('STDOUT')
sl = StreamToLogger(stdout_logger, logging.ERROR)
#sys.stdout = sl

stderr_logger = logging.getLogger('STDERR')
sl = StreamToLogger(stderr_logger, logging.ERROR)
sys.stderr = sl


# Define globals
MAC_SUCCESS=False
ANDROID_TRIGGERED=False

logger.debug("")
logger.debug('##########################################')
# what language are we speaking?
lang = os.environ['LANG'][0:2]
logger.debug('speaking: %s'%lang)

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
    logger.debug("function: is_after204_timeout send204after:%s current: %s"%(send204after,ts,))
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
    #logger.debug("sending microsoft response")
    en_txt={ 'message':"Click on the button to go to the IIAB home page",\
            'btn1':"GO TO IIAB HOME PAGE",'doc_root':get_iiab_env("WWWROOT")}
    es_txt={ 'message':"Haga clic en el botón para ir a la página de inicio de IIAB",\
            'btn1':"IIAB",'doc_root':get_iiab_env("WWWROOT")}
    if lang == "en":
        txt = en_txt
    elif lang == "es":
        txt = es_txt
    response_body = str(j2_env.get_template("simple.template").render(**txt))
    status = '200 OK'
    response_headers = [('Content-type','text/html'),
            ('Content-Length',str(len(response_body)))]
    start_response(status, response_headers)
    return [response_body]

def android(environ, start_response):
    global ANDROID_TRIGGERED
    ip = environ['HTTP_X_FORWARDED_FOR'].strip()
    system,system_version = platform_info(ip)
    if system_version[0:1] < '6':
        logger.debug("system < 6:%s"%system_version)
        location = '/android_splash'
        set_204after(ip,0)
    else:
        set_204after(ip,20)
        location = '/android_https'
    agent = environ['HTTP_USER_AGENT']
    response_body = "hello"
    status = '302 Moved Temporarily'
    response_headers = [('Location',location)]
    start_response(status, response_headers)
    return [response_body]

def android_splash(environ, start_response):
    en_txt={ 'message':"Click on the button to go to the IIAB home page",\
            'btn1':"GO TO IIAB HOME PAGE", \
            'doc_root':get_iiab_env("WWWROOT") }
    es_txt={ 'message':"Haga clic en el botón para ir a la página de inicio de IIAB",\
            'btn1':"IIAB",'doc_root':get_iiab_env("WWWROOT")}
    if lang == "en":
        txt = en_txt
    elif lang == "es":
        txt = es_txt
    response_body = str(j2_env.get_template("simple.template").render(**txt))
    status = '200 OK'
    response_headers = [('Content-type','text/html'),
            ('Content-Length',str(len(response_body)))]
    start_response(status, response_headers)
    return [response_body]

def android_https(environ, start_response):
    en_txt={ 'message':"""Please ignore the SECURITY warning which appears after clicking the first button""",\
             'btn2':'Click this first Go to the browser we need',\
             'btn1':'Then click this to go to IIAB home page',\
            'doc_root':get_iiab_env("WWWROOT") }
    es_txt={ 'message':"Haga clic en el botón para ir a la página de inicio de IIAB",\
            'btn1':"IIAB",'doc_root':get_iiab_env("WWWROOT")}
    if lang == "en":
        txt = en_txt
    elif lang == "es":
        txt = es_txt
    response_body = str(j2_env.get_template("simple.template").render(**txt))
    status = '200 OK'
    response_headers = [('Content-type','text/html'),
            ('Content-Length',str(len(response_body)))]
    start_response(status, response_headers)
    return [response_body]

def mac_splash(environ,start_response):
    logger.debug("in function mac_splash")
    en_txt={ 'message':"Click on the button to go to the IIAB home page",\
            'btn1':"GO TO IIAB HOME PAGE",'success_token': 'Success',
            'doc_root':get_iiab_env("WWWROOT")}
    es_txt={ 'message':"Haga clic en el botón para ir a la página de inicio de IIAB",\
            'btn1':"IIAB",'doc_root':get_iiab_env("WWWROOT")}
    if lang == "en":
        txt = en_txt
    elif lang == "es":
        txt = es_txt
    set_lasttimestamp(ip)
    response_body = str(j2_env.get_template("mac.template").render(**txt))
    status = '200 Success'
    response_headers = [('Content-type','text/html'),
            ('Content-Length',str(len(response_body)))]
    start_response(status, response_headers)
    return [response_body]

def macintosh(environ, start_response):
    global ip
    logger.debug("in function mcintosh")
    if not is_inactive(ip):
        set_lasttimestamp(ip)
        return success(environ,start_response)
    # determine if it is time to redirect again
    if is_after204_timeout(ip):
        set_204after(ip,10)
        response_body = """<html><head><script>
            window.location.reload(true)
            </script></body></html>"""
        status = '302 Moved Temporarily'
        response_headers = [('content','text/html')]
        start_response(status, response_headers)
        return [response_body]
    else:
        return mac_splash(environ,start_response)

def microsoft_connect(environ,start_response):
    status = '200 ok'
    headers = [('Content-type', 'text/html')]
    start_response(status, headers)
    return ["Microsoft Connect Test"]

# =============  Return html pages  ============================
def banner(environ, start_response):
    status = '200 OK'
    headers = [('Content-type', 'image/png')]
    start_response(status, headers)
    image = open("%s/iiab-menu/menu-files/images/iiab_banner6.png"%doc_root, "rb").read() 
    return [image]

def bootstrap(environ, start_response):
    logger.debug("in bootstrap")
    status = '200 OK'
    headers = [('Content-type', 'text/javascript')]
    start_response(status, headers)
    boot = open("%s/common/js/bootstrap.min.js"%doc_root, "rb").read() 
    return [boot]

def jquery(environ, start_response):
    logger.debug("in jquery")
    status = '200 OK'
    headers = [('Content-type', 'text/javascript')]
    start_response(status, headers)
    boot = open("%s/common/js/jquery.min.js"%doc_root, "rb").read() 
    return [boot]

def bootstrap_css(environ, start_response):
    logger.debug("in bootstrap_css")
    status = '200 OK'
    headers = [('Content-type', 'text/css')]
    start_response(status, headers)
    boot = open("%s/common/css/bootstrap.min.css"%doc_root, "rb").read() 
    return [boot]

def null(environ, start_response):
    status = '200 ok'
    headers = [('Content-type', 'text/html')]
    start_response(status, headers)
    return [""]

def success(environ, start_response):
    status = '200 ok'
    html = '<html><head><title>Success</title></head><body>Success</body></html>'
    headers = [('Content-type', 'text/html')]
    start_response(status, headers)
    return [html]

def put_204(environ, start_response):
    status = '204 No Data'
    response_body = ''
    response_headers = [('Content-type','text/html'),
            ('Content-Length',str(len(response_body)))]
    start_response(status, response_headers)
    logger.debug("sending 204 html response")
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
    return (system, system_version)

#
# ================== Start serving the wsgi application  =================
def application (environ, start_response):
    global ip
    global CATCH
    global LIST
    global INACTIVITY_TO
    global ANDROID_TRIGGERED

    # Log the URLs that are not in checkurls
    # This "CATCH" mode substitutes this server for apache at port 80
    # CATCH mode is started by "iiab-catch" and turned off by "iiab-uncath".
    if CATCH:
        logger.debug("Checking for url %s. USER_AGENT:%s"%(environ['HTTP_HOST'],\
               environ['HTTP_USER_AGENT'],))
        if environ['HTTP_HOST'] == '/box.lan':
            return                            
        if  'HTTP_X_FORWARDED_FOR' in environ:
            ip = environ['HTTP_X_FORWARDED_FOR'].strip()
        else:
            ip = environ['HTTP_HOST'].strip()
        cmd="arp -an %s|gawk \'{print $4}\'" % ip
        mac = subprocess.check_output(cmd, shell=True)
        data = []
        data.append("host: %s\n"%environ['HTTP_HOST'])
        data.append("path: %s\n"%environ['PATH_INFO'])
        data.append("query: %s\n"%environ['QUERY_STRING'])
        data.append("ip: %s\n"%ip)
        agent = environ['HTTP_USER_AGENT']
        data.append("AGENT: %s\n"%agent)
        #print(data)
        found = False
        url_list = os.path.join(CAPTIVE_PORTAL_BASE,"checkurls")
        if os.path.exists(url_list):
           with open(url_list,"r") as checkers:
              for line in checkers:
                 if line.find(environ['HTTP_HOST']) > -1:
                    found = True
                    break
        if not found:
            with open(url_list,"a") as checkers:
               outstr ="%s\n" %  (environ['HTTP_HOST']) 
               checkers.write(outstr)
            data = ['%s: %s\n' % (key, value) for key, value in sorted(environ.items()) ]
            logger.debug("This url was missing from checkurls:%s"%data)
    
    # Normal query for captive portal
    else:
        if  'HTTP_X_FORWARDED_FOR' in environ:
            ip = environ['HTTP_X_FORWARDED_FOR'].strip()
        else:
            data = ['%s: %s\n' % (key, value) for key, value in sorted(environ.items()) ]
            #logger.debug("need the correct ip:%s"%data)
            ip = environ['REMOTE_ADDR'].strip()
        cmd="arp -an %s|gawk \'{print $4}\'" % ip
        mac = subprocess.check_output(cmd, shell=True)
        data = []
        data.append("host: %s\n"%environ['HTTP_HOST'])
        data.append("path: %s\n"%environ['PATH_INFO'])
        data.append("query: %s\n"%environ['QUERY_STRING'])
        data.append("ip: %s\n"%ip)
        agent = environ['HTTP_USER_AGENT']
        data.append("AGENT: %s\n"%agent)
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
            logger.debug("failed UPDATE  users SET current_ts = %s WHERE ip = %s"%(ts,ip,)) 
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
            #data = ['%s: %s\n' % (key, value) for key, value in sorted(environ.items()) ]
            #logger.debug("need the correct ip:%s"%data)
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
           environ['HTTP_HOST'] == "detectportal.firefox.com" or\
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
            environ['HTTP_HOST'] == "connectivitycheck.gstatic.com":
            current_ts, last_ts, send204after = timeout_info(ip) 
            if not last_ts or (ts - int(last_ts) > INACTIVITY_TO):
                return android(environ, start_response) 
            elif is_after204_timeout(ip):
                return put_204(environ,start_response)
            return #return without doing anything

        # microsoft
        if  environ['PATH_INFO'] == "/connecttest.txt" and not is_inactive(ip):
           return microsoft_connect(environ, start_response) 
        if environ['HTTP_HOST'] == "ipv6.msftncsi.com" or\
           environ['HTTP_HOST'] == "ipv6.msftncsi.com.edgesuite.net" or\
           environ['HTTP_HOST'] == "www.msftncsi.com" or\
           environ['HTTP_HOST'] == "www.msftncsi.com.edgesuite.net" or\
           environ['HTTP_HOST'] == "www.msftconnecttest.com" or\
           environ['HTTP_HOST'] == "teredo.ipv6.microsoft.com" or\
           environ['HTTP_HOST'] == "teredo.ipv6.microsoft.com.nsatc.net": 
           return microsoft(environ, start_response) 

    logger.debug("executing the defaut 204 response. [%s"%data)
    return put_204(environ,start_response)

# Instantiate the server
httpd = make_server (
    "", # The host name
    PORT, # A port number where to wait for the request
    application # The application object name, in this case a function
)

httpd.serve_forever()
#vim: tabstop=3 expandtab shiftwidth=3 softtabstop=3 background=dark

