# shellcheck shell=bash
# Module file (no shebang). Bundled by build_bundle.sh

RED="\033[31m"; YEL="\033[33m"; GRN="\033[32m"; BLU="\033[34m"; RST="\033[0m"; BOLD="\033[1m"

log()      { printf "${BLU}[iiab]${RST} %s\n" "$*"; }
ok()       { printf "${GRN}[iiab]${RST} %s\n" "$*"; }
warn()     { printf "${YEL}[iiab] WARNING:${RST} %s\n" "$*" >&2; }
warn_red() { printf "${RED}${BOLD}[iiab] WARNING:${RST} %s\n" "$*" >&2; }

have() { command -v "$1" >/dev/null 2>&1; }
need() { have "$1" || return 1; }
die()  { echo "[!] $*" >&2; exit 1; }

# -------------------------
# Global defaults (may be overridden via environment)
# -------------------------
STATE_DIR="${STATE_DIR:-${HOME}/.iiab-android}"
ADB_STATE_DIR="${ADB_STATE_DIR:-${STATE_DIR}/adbw_pair}"
LOG_DIR="${LOG_DIR:-${STATE_DIR}/logs}"

HOST="${HOST:-127.0.0.1}"
CONNECT_PORT="${CONNECT_PORT:-}"
TIMEOUT_SECS="${TIMEOUT_SECS:-180}"

# Defaults used by ADB flows / logging / misc
CLEANUP_OFFLINE="${CLEANUP_OFFLINE:-1}"
DEBUG="${DEBUG:-0}"
