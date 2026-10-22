#!/usr/bin/env bash

set -euo pipefail

BASE_URL="${CAPTIVE_PORTAL_TEST_URL:-http://127.0.0.1}"
BASE_URL="${BASE_URL%/}"
PORTAL_HOST="${CAPTIVE_PORTAL_TEST_PORTAL_HOST:-captive.apple.com}"
ANDROID_HOST="${CAPTIVE_PORTAL_TEST_ANDROID_HOST:-clients3.google.com}"
WINDOWS_HOST="${CAPTIVE_PORTAL_TEST_WINDOWS_HOST:-www.msftconnecttest.com}"
HOME_HOST="${CAPTIVE_PORTAL_TEST_HOME_HOST:-box.lan}"
HOME_URL="${CAPTIVE_PORTAL_TEST_HOME_URL:-http://box.lan/}"
CAPTIVE_SPLASH="${CAPTIVE_PORTAL_TEST_SPLASH_PATH:-/captive_splash}"
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

request \
    macos-splash "$(client_ip 0)" "$PORTAL_HOST" \
    /hotspot-detect.html "$MACOS_UA"
assert_status 200
assert_body_contains 'Welcome to IIAB'
assert_body_contains '/home_selected'
assert_body_contains 'close the window'

request \
    macos-precompletion-probe "$(client_ip 0)" "$PORTAL_HOST" \
    /hotspot-detect.html "$MACOS_UA"
assert_status 200
assert_body_contains 'Welcome to IIAB'

request \
    iphone-splash "$(client_ip 1)" "$PORTAL_HOST" \
    /hotspot-detect.html "$IPHONE_UA"
assert_status 200
assert_body_contains 'Welcome to IIAB'
assert_body_contains 'Use Without Internet'

request \
    android-probe "$(client_ip 2)" "$ANDROID_HOST" \
    /generate_204 "$ANDROID_UA"
assert_status 302
assert_location "$CAPTIVE_SPLASH"

request \
    android-splash "$(client_ip 2)" "$ANDROID_HOST" \
    "$CAPTIVE_SPLASH" "$ANDROID_UA"
assert_status 200
assert_body_contains 'Welcome to IIAB'
assert_body_contains 'I UNDERSTAND - SIGN IN'

request \
    android-completion-click "$(client_ip 2)" "$ANDROID_HOST" \
    /home_selected "$ANDROID_UA" POST
assert_status 204
assert_body_empty

request \
    android-completed-splash "$(client_ip 2)" "$ANDROID_HOST" \
    "$CAPTIVE_SPLASH" "$ANDROID_UA"
assert_status 204

request \
    windows-probe "$(client_ip 3)" "$WINDOWS_HOST" \
    /connecttest.txt "$WINDOWS_UA"
assert_status 302
assert_location "$HOME_URL"

request \
    macos-completion-splash "$(client_ip 4)" "$PORTAL_HOST" \
    /hotspot-detect.html "$MACOS_UA"
assert_status 200
assert_body_contains 'Welcome to IIAB'

request \
    macos-completion-click "$(client_ip 4)" "$PORTAL_HOST" \
    /home_selected "$MACOS_UA"
assert_status 200
assert_body_empty

request \
    macos-completed-probe "$(client_ip 4)" "$PORTAL_HOST" \
    /hotspot-detect.html "$MACOS_UA"
assert_status 200
assert_body_contains 'Success'

request \
    homepage-root "$(client_ip 5)" "$HOME_HOST" / "$BROWSER_UA"
if [[ "$REQUEST_STATUS" == 3* ]] && [[ "$(response_location)" == "$HOME_URL" ]]; then
    fail "homepage root redirects to itself: $HOME_URL"
fi

printf 'All captive portal curl integration tests passed.\n'
