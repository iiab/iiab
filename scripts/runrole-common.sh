#!/bin/bash
#
# Shared by ./runrole and ./runroles.
#
# Paths default to the usual IIAB locations. DEFAULT_VARS_FILE follows the
# checkout, so ./runrole also works from a git worktree; LOCAL_VARS_FILE and
# the state files stay under /etc/iiab because that is what the installed
# host uses.

IIAB_REPO="${IIAB_REPO:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
IIAB_STATE_CMD="${IIAB_STATE_CMD:-$IIAB_REPO/scripts/iiab-state}"
ROLE_LIFECYCLE_CMD="${ROLE_LIFECYCLE_CMD:-$IIAB_REPO/scripts/role_lifecycle.py}"
PYTHON="${PYTHON:-python3}"

DEFAULT_VARS_FILE="${DEFAULT_VARS_FILE:-$IIAB_REPO/vars/default_vars.yml}"
LOCAL_VARS_FILE="${LOCAL_VARS_FILE:-/etc/iiab/local_vars.yml}"
IIAB_STATE_FILE="${IIAB_STATE_FILE:-/etc/iiab/iiab_state.yml}"
IIAB_INI_FILE="${IIAB_INI_FILE:-/etc/iiab/iiab.ini}"
export IIAB_STATE_FILE

CHECK_STATE_FILE=""
TEMP_PLAYBOOK=""

cleanup_temp_files() {
    [ -n "$CHECK_STATE_FILE" ] && rm -f "$CHECK_STATE_FILE"
    [ -n "$TEMP_PLAYBOOK" ] && rm -f "$TEMP_PLAYBOOK"
    return 0
}

state_cmd() {
    "$IIAB_STATE_CMD" --file "$IIAB_STATE_FILE" "$@"
}

# True if any true marker belongs to prefix.  A state-file read error is fatal
# instead of silently looking like "not installed".
state_has_prefix() {
    local status
    state_cmd has-prefix "$1"
    status=$?
    if [ "$status" -eq 2 ]; then
        echo -e "\e[1mERROR: could not read $IIAB_STATE_FILE (see above).\e[0m" >&2
        exit 2
    fi
    return "$status"
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

role_exists() {
    role_lifecycle exists "$1"
}

# True if <role> implements <feature>. --clean-install is derived from
# --uninstall because it is literally uninstall followed by a normal apply.
role_supports() {
    role_lifecycle supports "$1" "$2"
}

role_capabilities() {
    role_lifecycle capabilities "$1"
}

# Print an error unless <role> implements <feature>. The optional fourth
# argument explains why the flag needs that capability.
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

# Ask for explicit confirmation before an operation that removes data. Callers
# set ASSUME_YES from -y/--yes.
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

# Print one <key>: <value> line from a vars file.  Values may be quoted and
# may carry a trailing comment.  Returns 1 when the key is absent.
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

# Effective value of <key>: local_vars.yml wins over default_vars.yml.
var_value() {
    local value
    value=$(yaml_value "$LOCAL_VARS_FILE" "$1") || value=""
    if [ -z "$value" ]; then
        value=$(yaml_value "$DEFAULT_VARS_FILE" "$1") || value=""
    fi
    printf '%s' "$value"
}

# Where the effective value came from: "desired", "default", or "".
var_source() {
    if [ -f "$LOCAL_VARS_FILE" ] && yaml_value "$LOCAL_VARS_FILE" "$1" > /dev/null; then
        echo desired
    elif [ -f "$DEFAULT_VARS_FILE" ] && yaml_value "$DEFAULT_VARS_FILE" "$1" > /dev/null; then
        echo default
    fi
}

# True if <role>_install resolves to a true value across default + local vars.
# Guarded so a missing vars file is quiet rather than three grep errors.
# A helper role with no install/enabled switch is always considered enabled.
role_install_enabled() {
    local prefix
    local value
    # Prefixes such as squid/hostapd/dnsmasq are managed by another role, so
    # role_lifecycle does not know them.  Fall back to the prefix itself.
    prefix=$(role_install_var "$1" 2>/dev/null) || prefix=$1
    if [ -z "$prefix" ]; then
        return 0
    fi
    value=$(var_value "${prefix}_install")
    case $value in
        True|true|TRUE|Yes|yes|YES|On|on|ON|1)
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

# Print the effective value of <role>_install, or "-" when it is never set.
role_desired() {
    local prefix
    local value
    prefix=$(role_install_var "$1" 2>/dev/null) || prefix=$1
    if [ -z "$prefix" ]; then
        printf 'always'
        return
    fi
    value=$(var_value "${prefix}_install")
    printf '%s' "${value:--}"
}

# Show one role's recorded markers, desired configuration, and capabilities.
# Returns 1 for an unknown role so callers can fail instead of printing a
# meaningless empty report.
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
        # A few checklist prefixes (squid, hostapd, dnsmasq, admin_console) are
        # managed by a larger role or install stage.  Still show their state,
        # so the validation error can point at './runrole --status <prefix>'.
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
            echo "  If the program and its settings are already gone, clear the"
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

# Print every runnable role with its installed state, desired value, conflict
# flag, and capabilities.  Reads the state file once.
list_roles() {
    local var
    local installed
    local conflict
    local capabilities
    if ! state_cmd list > /dev/null; then
        echo -e "\e[1mERROR: could not read $IIAB_STATE_FILE (see above).\e[0m" >&2
        return 2
    fi
    printf '%-24s %-10s %-8s %-9s %s\n' "ROLE" "INSTALLED" "DESIRED" "CONFLICT" "CAPABILITIES"
    while IFS= read -r role; do
        installed="no"
        conflict="no"
        var=$(role_var "$role")
        if state_has_prefix "$var"; then
            installed="yes"
        fi
        if [ "$installed" = yes ] && [ -n "$(role_install_var "$role")" ] && ! role_install_enabled "$role"; then
            conflict="yes"
        fi
        capabilities=$(role_capabilities "$role")
        capabilities=${capabilities//_/-}
        printf '%-24s %-10s %-8s %-9s %s\n' \
            "$role" "$installed" "$(role_desired "$role")" "$conflict" "${capabilities:-none}"
    done < <(role_lifecycle list)
}

# Copy local facts once, so roles can read ansible_local.local_facts.
install_local_facts() {
    $CHECK && return 0
    $CHECK_LOCAL_VARS && return 0
    mkdir -p /etc/ansible/facts.d
    cp "$IIAB_REPO/scripts/local_facts.fact" /etc/ansible/facts.d/local_facts.fact
}

# Stage a private copy of the state file for --check, so check mode cannot
# change the host's markers.
stage_check_state() {
    $CHECK || return 0
    CHECK_STATE_FILE=$(mktemp "${TMPDIR:-/tmp}/iiab-state.XXXXXX")
    if [ -f "$IIAB_STATE_FILE" ]; then
        cp "$IIAB_STATE_FILE" "$CHECK_STATE_FILE"
    else
        printf '%s\n' \
            '# DO *NOT* MANUALLY EDIT THIS, THANKS!' \
            '# IIAB installs apps/services; extended operations are only for' \
            '# roles that provide the matching lifecycle tasks.' \
            '' > "$CHECK_STATE_FILE"
    fi
}

# Run one ansible-playbook invocation. $1 is the JSON object for --extra-vars.
run_playbook() {
    local extra_vars=$1
    local -a args=(
        -i "$INVENTORY"
        "$PLAYBOOK"
        --connection=local
        --extra-vars "$extra_vars"
    )
    if $CHECK; then
        args+=(--check --diff)
    fi
    if $VERBOSE; then
        args+=(-v)
    fi
    printf '\n\033[1mRunning:\033[0m\n\n'
    printf '%q ' ansible-playbook "${args[@]}"
    printf '\n\n'
    ansible-playbook "${args[@]}"
}

# Confirm that an uninstall phase really removed the role's markers. A role
# that forgets its final 'iiab_state: state=absent' task must not be reported
# as uninstalled.
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
