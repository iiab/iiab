#!/usr/bin/env bash

set -euo pipefail

BASE_URL="${CAPTIVE_PORTAL_TEST_URL:-http://127.0.0.1}"
BASE_URL="${BASE_URL%/}"
PORTAL_HOST="${CAPTIVE_PORTAL_TEST_PORTAL_HOST:-captive.apple.com}"
ANDROID_HOST="${CAPTIVE_PORTAL_TEST_ANDROID_HOST:-clients3.google.com}"
WINDOWS_HOST="${CAPTIVE_PORTAL_TEST_WINDOWS_HOST:-www.msftconnecttest.com}"
FEDORA_HOST="${CAPTIVE_PORTAL_TEST_FEDORA_HOST:-fedoraproject.org}"
TEST_DOMAIN="${CAPTIVE_PORTAL_TEST_DOMAIN:-lan}"
HOME_HOST="${CAPTIVE_PORTAL_TEST_HOME_HOST:-box.${TEST_DOMAIN}}"
HOME_URL="${CAPTIVE_PORTAL_TEST_HOME_URL:-http://${HOME_HOST}/}"
# First IPv4 address the host reports, used only as a Host header to verify
# that address literals reach the normal server instead of the portal
# default_server. Fall back to 127.0.0.1 when no IPv4 address is available.
first_host_ipv4() {
    hostname -I 2>/dev/null | tr ' ' '\n' | awk '/^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$/ { print; exit }'
}
LOCAL_IP="${CAPTIVE_PORTAL_TEST_LOCAL_IP:-$(first_host_ipv4 || true)}"
LOCAL_IP="${LOCAL_IP:-127.0.0.1}"
CAPTIVE_SPLASH="${CAPTIVE_PORTAL_TEST_SPLASH_PATH:-/captive_splash}"
IIAB_ENV="${CAPTIVE_PORTAL_TEST_IIAB_ENV:-/etc/iiab/iiab.env}"
LAN_IP="${CAPTIVE_PORTAL_TEST_LAN_IP:-$(sed -n 's/^LAN_IP=//p' "$IIAB_ENV" 2>/dev/null | head -n 1)}"
LAN_IP="${LAN_IP:-$LOCAL_IP}"
# The portal redirects probes to the LAN address, not to a relative path on
# the probe hostname (several probe hostnames are HSTS-preloaded).
CAPTIVE_SPLASH_URL="${CAPTIVE_PORTAL_TEST_SPLASH_URL:-http://${LAN_IP}${CAPTIVE_SPLASH}}"
TIMEOUT="${CAPTIVE_PORTAL_TEST_TIMEOUT:-10}"
CLIENT_BASE="${CAPTIVE_PORTAL_TEST_CLIENT_BASE:-$((20 + RANDOM % 180))}"

MACOS_UA='Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15'
IPHONE_UA='Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'
ANDROID_UA='Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Mobile Safari/537.36'
WINDOWS_UA='Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
BROWSER_UA='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36'

if ! [[ "$CLIENT_BASE" =~ ^[0-9]+$ ]] || (( CLIENT_BASE < 2 || CLIENT_BASE > 248 )); then
    printf 'CLIENT_BASE must be an integer from 2 through 248\n' >&2
    exit 2
fi

TEST_DIR="$(mktemp -d "${TMPDIR:-/tmp}/iiab-captiveportal-curl.XXXXXX")"
trap 'rm -rf -- "$TEST_DIR"' EXIT

client_ip() {
    printf '127.0.0.%d' "$((CLIENT_BASE + $1))"
}

fail() {
    printf 'FAIL: %s\n' "$1" >&2
    exit 1
}

request() {
    local name="$1"
    local source_ip="$2"
    local host="$3"
    local path="$4"
    local user_agent="$5"
    local body="$TEST_DIR/$name.body"
    local headers="$TEST_DIR/$name.headers"
    local status
    local method="${6:-GET}"

    if ! status="$(
        curl --silent --show-error --max-time "$TIMEOUT" \
            --interface "$source_ip" \
            --request "$method" \
            --user-agent "$user_agent" \
            --header "Host: $host" \
            --dump-header "$headers" \
            --output "$body" \
            --write-out '%{http_code}' \
            "$BASE_URL$path"
    )"; then
        fail "$name request failed"
    fi

    REQUEST_STATUS="$status"
    REQUEST_BODY="$body"
    REQUEST_HEADERS="$headers"
    printf '  %-28s %s\n' "$name" "$REQUEST_STATUS"
}

assert_status() {
    local expected="$1"
    [[ "$REQUEST_STATUS" == "$expected" ]] ||
        fail "expected HTTP $expected, got HTTP $REQUEST_STATUS"
}

assert_body_contains() {
    local expected="$1"
    grep -Fq "$expected" "$REQUEST_BODY" ||
        fail "response did not contain: $expected"
}

assert_body_equals() {
    local expected="$1"
    local actual
    actual="$(cat "$REQUEST_BODY")"
    [[ "$actual" == "$expected" ]] ||
        fail "expected response body '$expected', got '$actual'"
}

assert_body_empty() {
    [[ ! -s "$REQUEST_BODY" ]] ||
        fail "expected an empty response body"
}

assert_body_not_contains() {
    local unexpected="$1"
    ! grep -Fq "$unexpected" "$REQUEST_BODY" ||
        fail "response unexpectedly contained: $unexpected"
}

assert_header_contains() {
    local expected="$1"
    grep -Fqi "$expected" "$REQUEST_HEADERS" ||
        fail "response headers did not contain: $expected"
}

response_location() {
    sed -n -E 's/^[Ll]ocation:[[:space:]]*//p' "$REQUEST_HEADERS" |
        tr -d '\r' |
        head -n 1
}

assert_location() {
    local expected="$1"
    local actual
    actual="$(response_location)"
    [[ "$actual" == "$expected" ]] ||
        fail "expected Location $expected, got ${actual:-<none>}"
}

printf 'Captive portal curl integration tests against %s\n' "$BASE_URL"

# Client lifecycle:
# - Apple and Android clients are completed after their informational splash
#   has been displayed briefly;
# - completion changes only that client's subsequent probe responses.
request \
    macos-precompletion-probe "$(client_ip 0)" "$PORTAL_HOST" \
    /hotspot-detect.html "$MACOS_UA"
assert_status 302
assert_location "$CAPTIVE_SPLASH_URL"

request \
    macos-precompletion-splash "$(client_ip 0)" "$PORTAL_HOST" \
    "$CAPTIVE_SPLASH" "$MACOS_UA"
assert_status 200
assert_body_contains 'Welcome to IIAB'
assert_body_not_contains '/home_selected'
assert_body_not_contains 'SIGN IN'
assert_body_contains 'You may close this window.'
assert_header_contains 'Cache-Control: no-store'

request \
    macos-precompletion-repeat "$(client_ip 0)" "$PORTAL_HOST" \
    /hotspot-detect.html "$MACOS_UA"
assert_status 302
assert_location "$CAPTIVE_SPLASH_URL"

sleep 11

request \
    macos-completed-after-splash "$(client_ip 0)" "$PORTAL_HOST" \
    /hotspot-detect.html "$MACOS_UA"
assert_status 200
assert_body_contains 'Success'
assert_header_contains 'text/html'

request \
    macos-library-completed "$(client_ip 0)" "$PORTAL_HOST" \
    /library/test/success.html "$MACOS_UA"
assert_status 200
assert_body_contains 'Success'
assert_header_contains 'text/html'

request \
    android-precompletion-probe "$(client_ip 1)" "$ANDROID_HOST" \
    /generate_204 "$ANDROID_UA"
assert_status 302
assert_location "$CAPTIVE_SPLASH_URL"

request \
    android-precompletion-splash "$(client_ip 1)" "$ANDROID_HOST" \
    "$CAPTIVE_SPLASH" "$ANDROID_UA"
assert_status 200
assert_body_contains 'Welcome to IIAB'
assert_body_not_contains '/home_selected'
assert_body_not_contains 'SIGN IN'
assert_body_contains 'You may close this page.'

request \
    android-precompletion-repeat "$(client_ip 1)" "$ANDROID_HOST" \
    /generate_204 "$ANDROID_UA"
assert_status 302
assert_location "$CAPTIVE_SPLASH_URL"

sleep 11

request \
    android-completed-probe "$(client_ip 1)" "$ANDROID_HOST" \
    /generate_204 "$ANDROID_UA"
assert_status 204
assert_body_empty

request \
    android-completed-splash "$(client_ip 1)" "$ANDROID_HOST" \
    "$CAPTIVE_SPLASH" "$ANDROID_UA"
assert_status 204
assert_body_empty

# A different client remains pre-authenticated while Android completes.
request \
    iphone-precompletion-probe "$(client_ip 2)" "$PORTAL_HOST" \
    /hotspot-detect.html "$IPHONE_UA"
assert_status 302
assert_location "$CAPTIVE_SPLASH_URL"

request \
    iphone-precompletion-splash "$(client_ip 2)" "$PORTAL_HOST" \
    "$CAPTIVE_SPLASH" "$IPHONE_UA"
assert_status 200
assert_body_contains 'Welcome to IIAB'
assert_body_not_contains '/home_selected'
assert_body_not_contains 'SIGN IN'
assert_body_contains 'You may close this page.'

request \
    iphone-precompletion-repeat "$(client_ip 2)" "$PORTAL_HOST" \
    /hotspot-detect.html "$IPHONE_UA"
assert_status 302
assert_location "$CAPTIVE_SPLASH_URL"

sleep 11

request \
    macos-completed-probe "$(client_ip 0)" "$PORTAL_HOST" \
    /hotspot-detect.html "$MACOS_UA"
assert_status 200
assert_body_contains 'Success'

request \
    iphone-completed-probe "$(client_ip 2)" "$PORTAL_HOST" \
    /hotspot-detect.html "$IPHONE_UA"
assert_status 200
assert_body_contains 'Success'

request \
    windows-probe "$(client_ip 3)" "$WINDOWS_HOST" \
    /connecttest.txt "$WINDOWS_UA"
assert_status 302
assert_location "$CAPTIVE_SPLASH_URL"

request \
    windows-splash "$(client_ip 3)" "$WINDOWS_HOST" \
    "$CAPTIVE_SPLASH" "$WINDOWS_UA"
assert_status 200
assert_body_contains 'Welcome to IIAB'
assert_body_contains 'You may close this page.'
assert_body_contains 'http-equiv="refresh"'
assert_body_contains "url=$CAPTIVE_SPLASH_URL"

sleep 11

request \
    windows-home-after-splash "$(client_ip 3)" "$WINDOWS_HOST" \
    "$CAPTIVE_SPLASH" "$WINDOWS_UA"
assert_status 302
assert_location "$HOME_URL"

request \
    windows-completed-probe "$(client_ip 3)" "$WINDOWS_HOST" \
    /connecttest.txt "$WINDOWS_UA"
assert_status 200
assert_body_equals 'Microsoft Connect Test'

request \
    fedora-probe "$(client_ip 4)" "$FEDORA_HOST" \
    /static/hotspot.txt "$BROWSER_UA"
assert_status 302
assert_location "$CAPTIVE_SPLASH_URL"

request \
    fedora-splash "$(client_ip 4)" "$FEDORA_HOST" \
    "$CAPTIVE_SPLASH" "$BROWSER_UA"
assert_status 200
assert_body_contains 'Welcome to IIAB'
assert_body_contains 'You may close this page.'
assert_body_contains 'http-equiv="refresh"'

sleep 11

request \
    fedora-home-after-splash "$(client_ip 4)" "$FEDORA_HOST" \
    "$CAPTIVE_SPLASH" "$BROWSER_UA"
assert_status 302
assert_location "$HOME_URL"

request \
    fedora-completed-probe "$(client_ip 4)" "$FEDORA_HOST" \
    /static/hotspot.txt "$BROWSER_UA"
assert_status 200
assert_body_equals 'OK'

# Host header normalization: a port, different case, or a trailing root dot
# must not bypass probe routing or change the success body.
request \
    kde-host-port-pre "$(client_ip 7)" "networkcheck.kde.org:80" / "$BROWSER_UA"
assert_status 302
assert_location "$CAPTIVE_SPLASH_URL"

request \
    kde-host-uppercase-pre "$(client_ip 7)" "NETWORKCHECK.KDE.ORG" / "$BROWSER_UA"
assert_status 302
assert_location "$CAPTIVE_SPLASH_URL"

request \
    kde-host-trailing-dot-pre "$(client_ip 7)" "networkcheck.kde.org." / "$BROWSER_UA"
assert_status 302
assert_location "$CAPTIVE_SPLASH_URL"

request \
    fedora-host-port-pre "$(client_ip 7)" "fedoraproject.org:80" /static/hotspot.txt "$BROWSER_UA"
assert_status 302
assert_location "$CAPTIVE_SPLASH_URL"

# The allow timer starts on the first request; no splash was served here, so
# wait for the 12 s unconditional timer rather than the 8 s splash timer.
sleep 13

request \
    kde-host-port-post "$(client_ip 7)" "networkcheck.kde.org:80" / "$BROWSER_UA"
assert_status 200
assert_body_equals 'OK'

request \
    kde-host-uppercase-post "$(client_ip 7)" "NETWORKCHECK.KDE.ORG" / "$BROWSER_UA"
assert_status 200
assert_body_equals 'OK'

request \
    kde-host-trailing-dot-post "$(client_ip 7)" "networkcheck.kde.org." / "$BROWSER_UA"
assert_status 200
assert_body_equals 'OK'

request \
    fedora-host-port-post "$(client_ip 7)" "fedoraproject.org:80" /static/hotspot.txt "$BROWSER_UA"
assert_status 200
assert_body_equals 'OK'

# The splash must also be reachable through the normal server, using the LAN
# address, so browsers that HSTS-upgrade probe URLs still have a usable page.
request \
    lan-ip-splash "$(client_ip 8)" "$LAN_IP" "$CAPTIVE_SPLASH" "$BROWSER_UA"
assert_status 200
assert_body_contains 'Welcome to IIAB'
assert_header_contains 'Cache-Control: no-store'

request \
    lan-ip-banner "$(client_ip 8)" "$LAN_IP" /iiab_banner6.png "$BROWSER_UA"
assert_status 200
assert_header_contains 'image/png'

request \
    homepage-root "$(client_ip 5)" "$HOME_HOST" / "$BROWSER_UA"
if [[ "$REQUEST_STATUS" == 3* ]] && [[ "$(response_location)" == "$HOME_URL" ]]; then
    fail "homepage root redirects to itself: $HOME_URL"
fi

# Requesting IIAB by an address that belongs to the host must reach the
# normal NGINX server, not the Captive Portal default_server (which would
# redirect to HOME_URL and fail for clients that cannot resolve it).
request \
    local-ip-homepage "$(client_ip 6)" "$LOCAL_IP" / "$BROWSER_UA"
if [[ "$REQUEST_STATUS" == 3* ]]; then
    local_ip_location="$(response_location)"
    [[ "$local_ip_location" != "$HOME_URL" ]] ||
        fail "local IP $LOCAL_IP redirects to $HOME_URL"
    [[ "$local_ip_location" != "$CAPTIVE_SPLASH" && "$local_ip_location" != "$CAPTIVE_SPLASH_URL" ]] ||
        fail "local IP $LOCAL_IP redirects to the captive splash"
fi

printf 'All captive portal curl integration tests passed.\n'
