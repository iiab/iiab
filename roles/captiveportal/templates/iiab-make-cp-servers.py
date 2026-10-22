#!/usr/bin/env python3
# The script reads the list of online portal checkers and generates the NGINX
# server blocks and dnsmasq entries from the same normalized names.

import re
import subprocess
import sys
from pathlib import Path

CHECK_URLS_PATH = Path('/opt/iiab/captiveportal/checkurls')
NGINX_CONFIG_PATH = Path('/etc/nginx/sites-available/capture.conf')
CAPTURE_PATH = Path('/etc/dnsmasq.d/capture')
DEFAULT_VARS_PATH = Path('/opt/iiab/iiab/vars/default_vars.yml')
LOCAL_VARS_PATH = Path('/etc/iiab/local_vars.yml')
IIAB_ENV_PATH = Path('/etc/iiab/iiab.env')
LAN_IP = '{{ lan_ip }}'
CAPTIVEPORTAL_PROBE_IP = '{{ captiveportal_probe_ip }}'

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
        # Internet" ("Limited connection"). The server returns a 302 to the
        # IIAB homepage, which nginx serves independently of the portal backend.
        error_page 502 503 504 =302 http://{{ iiab_fqdn }}/;
    }
}
'''


def nginx_server_name(checkurl):
    """Translate a checkurls entry into a normalized server name.

    A checkurls entry '*.example.org' means "any host under example.org".
    nginx spells that wildcard the same way ('*.example.org'), so such
    entries are used unchanged.

    Note that '.*.example.org' (what a naive '*' -> '.*' substitution
    produces) is *not* an nginx wildcard: nginx keeps the part behind the
    asterisk as the domain suffix, so it would only ever match
    '..example.org' and thus nothing at all.

    For other wildcard forms, use the domain suffix after the last wildcard
    label. This at least captures the domain root when nginx cannot express
    the wildcard itself.
    """
    name = checkurl.strip()
    if '*' not in name:
        return name
    if name.startswith('.*.') and name.count('*') == 1:
        name = name[1:]
    if name.startswith('*.') and name.count('*') == 1:
        return name if name != '*.' else None
    labels = name.split('.')
    wildcard_label = max(
        (index for index, label in enumerate(labels) if '*' in label),
        default=-1,
    )
    root_labels = labels[wildcard_label + 1:]
    if wildcard_label == 0 and labels[0].startswith('*'):
        wildcard_suffix = labels[0].split('*', 1)[1]
        if wildcard_suffix:
            root_labels.insert(0, wildcard_suffix)
    domain_root = '.'.join(root_labels)
    return domain_root or None


def iter_server_names():
    """Yield unique, normalized names from the captive portal probe list."""
    server_names = set()
    if not CHECK_URLS_PATH.exists():
        return
    with CHECK_URLS_PATH.open(encoding='utf-8') as checkurls:
        for line in checkurls:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            server_name = nginx_server_name(line)
            if server_name is None:
                print(
                    f'iiab-make-cp-servers: ignoring unsupported wildcard in checkurls entry: {line}',
                    file=sys.stderr,
                )
                continue
            server_names.add(server_name)
    yield from sorted(server_names)


def iter_server_entries():
    """Yield the default server and one entry for each captive portal probe."""
    yield ' default_server', '_'
    yield from (('', server_name) for server_name in iter_server_names())


def render_dnsmasq_config():
    """Render dnsmasq entries for the normalized captive portal probe list."""
    domains = {
        server_name[2:] if server_name.startswith('*.') else server_name
        for server_name in iter_server_names()
    }
    entries = [
        f'address=/{domain}/'
        f'{LAN_IP if domain == "captive.lan" else CAPTIVEPORTAL_PROBE_IP}'
        for domain in sorted(domains)
    ]
    entries.extend(
        (
            f'address=/box/{LAN_IP}',
            f'address=/box.local/{LAN_IP}',
            '# Windows NCSI captive portal detection',
            'address=/dns.msftncsi.com/131.107.255.255',
        )
    )
    return '\n'.join(entries)


def iiab_var_value(name):
    """Read an IIAB variable, with local_vars overriding default_vars."""
    values = {}
    pattern = re.compile(rf'^{re.escape(name)}:\s+(.*)$')
    for path in (DEFAULT_VARS_PATH, LOCAL_VARS_PATH):
        try:
            lines = path.read_text(encoding='utf-8').splitlines()
        except FileNotFoundError:
            continue
        for line in lines:
            match = pattern.match(line)
            if match:
                value = match.group(1).split('#', 1)[0].strip()
                if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
                    value = value[1:-1]
                values[path] = value
    local_value = values.get(LOCAL_VARS_PATH, '')
    return local_value if local_value else values.get(DEFAULT_VARS_PATH, '')


def iiab_env_values():
    """Read the shell-style values needed to determine portal activity."""
    try:
        lines = IIAB_ENV_PATH.read_text(encoding='utf-8').splitlines()
    except FileNotFoundError:
        return {}
    values = {}
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        name, value = line.split('=', 1)
        values[name] = value
    return values


def is_true(value):
    return value.lower() in {'true', 'yes', 'on', '1'}


def portal_is_active():
    """Return whether dnsmasq should divert connectivity probes."""
    env = iiab_env_values()
    return (
        is_true(iiab_var_value('captiveportal_enabled'))
        and env.get('IIAB_LAN_DEVICE', '') != 'none'
        and not is_true(env.get('IIAB_GATEWAY_ENABLED', ''))
        and CHECK_URLS_PATH.exists()
    )


def update_dnsmasq():
    """Create or remove the dnsmasq diversion and reload dnsmasq if needed."""
    new_config = render_dnsmasq_config() if portal_is_active() else ''
    try:
        current_config = CAPTURE_PATH.read_text(encoding='utf-8').rstrip('\n')
    except FileNotFoundError:
        current_config = ''
    if current_config == new_config:
        return

    if new_config:
        CAPTURE_PATH.parent.mkdir(parents=True, exist_ok=True)
        CAPTURE_PATH.write_text(f'{new_config}\n', encoding='utf-8')
    else:
        try:
            CAPTURE_PATH.unlink()
        except FileNotFoundError:
            pass
    subprocess.run(
        ('systemctl', 'reload', 'dnsmasq'),
        check=False,
        stderr=subprocess.STDOUT,
    )
    subprocess.run(
        ('systemctl', 'restart', 'dnsmasq'),
        check=True,
        stderr=subprocess.STDOUT,
    )


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
    update_dnsmasq()


if __name__ == '__main__':
    main()
