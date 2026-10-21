#!/usr/bin/env python3
# Read the list of online portal checkers and make nginx server blocks.

from pathlib import Path

CHECK_URLS_PATH = Path('/opt/iiab/captiveportal/checkurls')
NGINX_CONFIG_PATH = Path('/etc/nginx/sites-available/capture.conf')

SERVER_BLOCK = '''server {
    listen {{ nginx_port }}%(listen_suffix)s;
    server_name %(server_name)s;
    location / {
        include uwsgi_params;
        uwsgi_param HTTP_HOST $http_host;
        uwsgi_param SERVER_NAME $server_name;
        uwsgi_param HTTP_X_FORWARDED_FOR $remote_addr;
        uwsgi_pass unix:///run/uwsgi/captiveportal.socket;
        # If the Captive Portal backend (uWSGI) is down or wedged, probes must
        # not receive 502/504: client operating systems read that as "no
        # Internet" ("Limited connection").  Send them to the IIAB homepage,
        # which nginx serves independently of the portal backend.
        error_page 502 503 504 =302 http://{{ iiab_fqdn }}/;
    }
}
'''


def iter_server_entries():
    """Yield the default server and one entry for each captive portal probe."""
    yield ' default_server', '_'

    # Read the deployed list so role reruns use the same checkurls file as
    # iiab-divert-to-nginx.
    with CHECK_URLS_PATH.open(encoding='utf-8') as checkurls:
        for line in checkurls:
            yield '', line.replace('*', '.*').strip()


def render_server_block(listen_suffix, server_name):
    return SERVER_BLOCK % {
        'listen_suffix': listen_suffix,
        'server_name': server_name,
    }


def main():
    nginx_config = ''.join(
        render_server_block(listen_suffix, server_name) for listen_suffix, server_name in iter_server_entries()
    )
    NGINX_CONFIG_PATH.write_text(nginx_config, encoding='utf-8')


if __name__ == '__main__':
    main()
