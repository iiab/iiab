#!/bin/bash
#
# Shared by ./runrole and ./runroles.  DEFAULT_VARS_FILE follows the checkout;
# LOCAL_VARS_FILE and the state files stay under /etc/iiab.

IIAB_REPO="${IIAB_REPO:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
IIAB_STATE_CMD="${IIAB_STATE_CMD:-$IIAB_REPO/scripts/iiab-state}"
ROLE_LIFECYCLE_CMD="${ROLE_LIFECYCLE_CMD:-$IIAB_REPO/scripts/role_lifecycle.py}"
PYTHON="${PYTHON:-python3}"

DEFAULT_VARS_FILE="${DEFAULT_VARS_FILE:-$IIAB_REPO/vars/default_vars.yml}"
LOCAL_VARS_FILE="${LOCAL_VARS_FILE:-/etc/iiab/local_vars.yml}"
IIAB_STATE_FILE="${IIAB_STATE_FILE:-/etc/iiab/iiab_state.yml}"
IIAB_INI_FILE="${IIAB_INI_FILE:-/etc/iiab/iiab.ini}"
export IIAB_STATE_FILE

TEMP_PLAYBOOK=""

cleanup_temp_files() {
    [ -n "$TEMP_PLAYBOOK" ] && rm -f "$TEMP_PLAYBOOK"
    return 0
}

state_cmd() {
    "$IIAB_STATE_CMD" --file "$IIAB_STATE_FILE" "$@"
}

# Only 0 (yes) and 1 (no) are normal answers; anything else is a read error.
state_has_prefix() {
    local status
    state_cmd has-prefix "$1"
    status=$?
    if [ "$status" -ne 0 ] && [ "$status" -ne 1 ]; then
        echo -e "\e[1mERROR: could not read $IIAB_STATE_FILE (see above).\e[0m" >&2
        exit 2
    fi
    return "$status"
}

# True when <name> is a variable prefix from 0-init's validation checklist,
# even when it is not a standalone role (squid, hostapd, dnsmasq).
is_checklist_prefix() {
    role_lifecycle checklist-prefixes | grep -qxF -- "$1"
}

state_show_prefix() {
    state_cmd list --prefix "$1"
}

# Role names, variable prefixes, and capabilities live in one place:
# scripts/role_lifecycle.py (shared with scripts/test-role-lifecycle.py).
role_lifecycle() {
    "$PYTHON" "$ROLE_LIFECYCLE_CMD" "$@"
}

role_var() {
    role_lifecycle var "$1"
}

# Install/enabled prefix. Empty for always-on helper roles.
role_install_var() {
    role_lifecycle install-var "$1"
}

# Like role_install_var, but also accepts a bare checklist prefix.
checklist_install_var() {
    role_lifecycle install-var "$1" 2>/dev/null || printf '%s' "$1"
}

role_exists() {
    role_lifecycle exists "$1"
}

# True if the role's main.yml dispatches to the shared lifecycle runner.
role_uses_runner() {
    role_lifecycle uses-runner "$1"
}

# True if <role> implements <feature>.
role_supports() {
    role_lifecycle supports "$1" "$2"
}

role_capabilities() {
    role_lifecycle capabilities "$1"
}

# Print an error unless <role> implements <feature>.
role_require_capability() {
    local role=$1
    local flag=$2
    local feature=$3
    local reason=${4:-}
    if role_supports "$role" "$feature"; then
        return 0
    fi
    echo -e "\e[1mERROR: role '$role' does not support $flag.\e[0m" >&2
    if [ -n "$reason" ]; then
        echo "$reason" >&2
    fi
    echo "Reference tasks/${feature}.yml from the role entrypoint, add a 'when: ${feature}' condition there, or declare '${feature}: true' in roles/${role}/meta/runrole.yml." >&2
    return 1
}

# Ask for explicit confirmation before an operation that removes data.
confirm_destructive() {
    local ans
    if [ "$ASSUME_YES" = true ]; then
        return 0
    fi
    printf "Type 'yes' to continue: "
    if [ -t 0 ]; then
        read -r ans < /dev/tty
    else
        echo
        echo "No TTY: refusing without --yes." >&2
        return 1
    fi
    echo
    [ "$ans" = "yes" ]
}

# Print one <key>: <value> from a vars file; 1 when the key is absent.
yaml_value() {
    local file=$1
    local key=$2
    local line
    [ -f "$file" ] || return 1
    line=$(grep -E "^[[:space:]]*${key}:[[:space:]]*[^#[:space:]]" "$file" | tail -n 1)
    [ -n "$line" ] || return 1
    printf '%s\n' "$line" |
        sed -E "s/^[[:space:]]*${key}:[[:space:]]*//; s/[[:space:]]+#.*$//; s/[[:space:]]+$//; s/^[\"']//; s/[\"']$//"
}

var_value() {
    local value
    value=$(yaml_value "$LOCAL_VARS_FILE" "$1") || value=""
    if [ -z "$value" ]; then
        value=$(yaml_value "$DEFAULT_VARS_FILE" "$1") || value=""
    fi
    printf '%s' "$value"
}

var_source() {
    if [ -f "$LOCAL_VARS_FILE" ] && yaml_value "$LOCAL_VARS_FILE" "$1" > /dev/null; then
        echo desired
    elif [ -f "$DEFAULT_VARS_FILE" ] && yaml_value "$DEFAULT_VARS_FILE" "$1" > /dev/null; then
        echo default
    fi
}

install_var_enabled() {
    local value
    value=$(var_value "${1}_install")
    case $value in
        True|true|TRUE|Yes|yes|YES|On|on|ON|1)
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

# A helper role with no install/enabled switch is always considered enabled.
role_install_enabled() {
    local prefix
    prefix=$(role_install_var "$1" 2>/dev/null) || prefix=$1
    if [ -z "$prefix" ]; then
        return 0
    fi
    install_var_enabled "$prefix"
}

desired_for() {
    local value
    if [ -z "$1" ]; then
        printf 'always'
        return
    fi
    value=$(var_value "${1}_install")
    printf '%s' "${value:--}"
}

# Show one role's markers, desired configuration, and capabilities.
status_role() {
    local role="$1"
    local var
    local install_var
    local feature
    local capabilities
    local source
    local installed=false
    local standalone=true
    var=$(role_var "$role" 2>/dev/null) || var=$role
    install_var=$(role_install_var "$role" 2>/dev/null) || install_var=$var
    if ! role_exists "$role"; then
        standalone=false
        # Prefixes managed by a larger role or stage still get a report.
        if ! state_has_prefix "$var" && [ -z "$(var_source "${var}_install")" ]; then
            echo "ERROR: unknown role: $role" >&2
            echo "Run './runrole --list' to see the available roles." >&2
            return 1
        fi
    fi
    if $standalone; then
        echo "Role: $role (state prefix: ${var}_)"
        if [ -n "$install_var" ] && [ "$install_var" != "$var" ]; then
            echo "  (install/enabled prefix: ${install_var}_)"
        elif [ -z "$install_var" ]; then
            echo "  (always-on helper role: no install/enabled vars)"
        fi
    else
        echo "Role: $role (not a standalone role; variable prefix: ${var}_)"
    fi
    if state_has_prefix "$var"; then
        installed=true
        echo "Installed state:"
        state_show_prefix "$var" | sed 's/^/  /'
    else
        echo "Installed state: not installed"
    fi
    if [ -n "$install_var" ]; then
        for feature in install enabled; do
            source=$(var_source "${install_var}_${feature}")
            if [ -n "$source" ]; then
                printf '  %s %s_%s: %s\n' "$source" "$install_var" "$feature" "$(var_value "${install_var}_${feature}")"
            fi
        done
    fi
    if [ -f "$IIAB_INI_FILE" ] && grep -q "^${var}_version[[:space:]]*=" "$IIAB_INI_FILE"; then
        grep "^${var}_version[[:space:]]*=" "$IIAB_INI_FILE" | tail -1 | sed 's/^/  installed /'
    fi
    if $installed && [ -n "$install_var" ] && ! role_install_enabled "$role"; then
        echo
        echo -e "\e[1;33mCONFLICT: ${role} is installed, but ${install_var}_install is not True.\e[0m"
        echo "  Keep it:   set '${install_var}_install: True' in $LOCAL_VARS_FILE"
        if ! $standalone; then
            echo "  This prefix is managed by another role or install stage."
            echo "  Run './runrole --list' to find the role that owns it."
        elif role_supports "$role" uninstall; then
            echo "  Remove it: sudo ./runrole --uninstall ${role}"
        else
            echo "  ${role} does not support --uninstall."
            echo "  If the program and its program data are already gone, clear the"
            echo "  stale marker with: sudo ./scripts/iiab-state forget ${var}"
        fi
    fi
    if $standalone; then
        capabilities=$(role_capabilities "$role")
        if [ -z "$capabilities" ]; then
            echo "Capabilities: none"
        else
            echo "Capabilities: ${capabilities//_/-}"
        fi
    else
        echo "No standalone role owns this prefix, so it has no runrole capabilities."
        echo "Run './runrole --list' to see the role that manages it (e.g. squid -> network)."
    fi
    echo
    return 0
}

# Match has-prefix semantics without a process per role.
prefix_in_listing() {
    local prefix=$1
    local listing=$2
    awk -v prefix="$prefix" '
        {
            key = $0
            sub(/:.*/, "", key)
            value = $0
            sub(/^[^:]*:[ \t]*/, "", value)
            if ((key == prefix || index(key, prefix "_") == 1) &&
                tolower(value) ~ /^(true|yes|on|1)$/) {
                found = 1
                exit
            }
        }
        END { exit(found ? 0 : 1) }
    ' <<< "$listing"
}

# Print every runnable role with its state, desired value, and capabilities.
list_roles() {
    local role
    local var
    local install_var
    local capabilities
    local installed
    local conflict
    local state_listing
    if ! state_listing=$(state_cmd list); then
        echo -e "\e[1mERROR: could not read $IIAB_STATE_FILE (see above).\e[0m" >&2
        return 2
    fi
    printf '%-24s %-10s %-8s %-9s %s\n' "ROLE" "INSTALLED" "DESIRED" "CONFLICT" "CAPABILITIES"
    while IFS='|' read -r role var install_var capabilities; do
        installed="no"
        conflict="no"
        if prefix_in_listing "$var" "$state_listing"; then
            installed="yes"
        fi
        if [ "$installed" = yes ] && [ -n "$install_var" ] && ! install_var_enabled "$install_var"; then
            conflict="yes"
        fi
        capabilities=${capabilities//_/-}
        printf '%-24s %-10s %-8s %-9s %s\n' \
            "$role" "$installed" "$(desired_for "$install_var")" "$conflict" "${capabilities:-none}"
    done < <(role_lifecycle table)
}

# Refuse contradictory or destructive option combinations.  The first argument
# is "single" for ./runrole, where a log file is also accepted.
# shellcheck disable=SC2153  # Flags are set by the caller.
validate_options() {
    local log=false
    if [ "${1:-multi}" = single ]; then
        log=$LOGFILE
    fi
    if $CHECK_LOCAL_VARS && ($log || $UNINSTALL || $REINSTALL || $CLEAN_INSTALL || $ADD || $STATUS || $ASSUME_YES || $VERBOSE); then
        echo "--check-local-vars is read-only and cannot be combined with other options."
        exit 1
    fi
    if $UNINSTALL && ($REINSTALL || $CLEAN_INSTALL || $ADD); then
        echo "--uninstall cannot be combined with --add, --reinstall, or --clean-install."
        exit 1
    fi
    if $CLEAN_INSTALL && ($REINSTALL || $ADD); then
        echo "--clean-install cannot be combined with --add or --reinstall."
        exit 1
    fi
    if $STATUS && ($log || $UNINSTALL || $REINSTALL || $CLEAN_INSTALL || $ADD || $ASSUME_YES || $VERBOSE); then
        echo "--status is read-only and cannot be combined with other options."
        exit 1
    fi
}

# Copy local facts once, so roles can read ansible_local.local_facts.
install_local_facts() {
    $CHECK_LOCAL_VARS && return 0
    mkdir -p /etc/ansible/facts.d
    cp "$IIAB_REPO/scripts/local_facts.fact" /etc/ansible/facts.d/local_facts.fact
}

# Entry playbooks still load the state file with vars_files, so it must exist.
# ./scripts/iiab-state owns the file format, including its header.
ensure_state_file() {
    $CHECK_LOCAL_VARS && return 0
    [ -f "$IIAB_STATE_FILE" ] && return 0
    state_cmd ensure || {
        echo -e "\e[1mERROR: could not create $IIAB_STATE_FILE (see above).\e[0m" >&2
        exit 2
    }
}

run_playbook() {
    local extra_vars=$1
    local -a args=(
        -i "$INVENTORY"
        "$PLAYBOOK"
        --connection=local
        --extra-vars "$extra_vars"
    )
    if $VERBOSE; then
        args+=(-v)
    fi
    printf '\n\033[1mRunning:\033[0m\n\n'
    printf '%q ' ansible-playbook "${args[@]}"
    printf '\n\n'
    ansible-playbook "${args[@]}"
}

# A role that forgets its final 'state=absent' task must not look uninstalled.
verify_uninstall_markers() {
    local role=$1
    local var
    var=$(role_var "$role")
    if state_has_prefix "$var"; then
        echo -e "\e[1mERROR: ${role} finished, but its markers are still in $IIAB_STATE_FILE:\e[0m" >&2
        state_show_prefix "$var" | sed 's/^/  /' >&2
        echo "IIAB will keep reporting ${role} as installed until its uninstall phase removes them." >&2
        return 1
    fi
}
