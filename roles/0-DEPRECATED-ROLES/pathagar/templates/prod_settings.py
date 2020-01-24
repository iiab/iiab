from settings import *

FORCE_SCRIPT_NAME = '{{ pathagar_subpath }}'
LOGIN_REDIRECT_URL = FORCE_SCRIPT_NAME

MEDIA_ROOT = '{{ pathagar_media }}'
MEDIA_URL = '{{ pathagar_subpath }}/static_media/'

SECRET_KEY = '7ks@b7+gi^c4adff)6ka228#rd4f62v*g_dtmo*@i62k)qn=cs'
DATABASES = {
    'default': {
            'ENGINE':'django.db.backends.postgresql_psycopg2',
            'NAME': '{{ pathagar_db_name }}',
            'USER': '{{ pathagar_db_user }}',
            'PASSWORD': '{{ pathagar_db_password }}',
            'HOST': '127.0.0.1',
            'PORT': '5432',
        }
}

STATIC_ROOT = '{{ pathagar_collectstatic }}'
STATIC_URL = '{{ pathagar_subpath }}/static/'
