#NGINX is on port 8008 and expects ka-lite on port 7007
PRODUCTION_PORT=7007

#Persist ka-lite django page cache between reboots
CACHE_LOCATION = '/var/tmp/kalite/cache'

#Optimise cherrypy server for Raspberry Pi
CHERRYPY_THREAD_COUNT = 20

