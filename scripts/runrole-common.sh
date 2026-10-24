#!/bin/bash

# Shared by ./runrole and ./runroles. Both set these paths before sourcing:
# DEFAULT_VARS_FILE, LOCAL_VARS_FILE, IIAB_STATE_FILE, IIAB_INI_FILE.

# Ansible role name & var name sometimes differ :/
role_var() {
    case $1 in
        calibre-web)
            echo calibreweb
            ;;
        iiab-admin)
            echo iiab_admin
            ;;
        osm-vector-maps)    # TO BE REMOVED in 2026/2027
            echo osm_vector_maps
            ;;
        *)
            echo "$1"
            ;;
    esac
}

# True if <role>_install resolves to True across default + local vars.
role_install_enabled() {
    local var
    local enabled=false
    var=$(role_var "$1")
    grep -q "^${var}_install:\s\+[Tt]rue\b" "$DEFAULT_VARS_FILE" && enabled=true
    grep -q "^${var}_install:\s\+[Ff]alse\b" "$LOCAL_VARS_FILE" && enabled=false
    grep -q "^${var}_install:\s\+[Tt]rue\b" "$LOCAL_VARS_FILE" && enabled=true
    $enabled
}

status_role() {
    local role="$1"
    local var
    var=$(role_var "$role")
    echo "Role: $role (variable prefix: ${var}_)"
    if [ -f "$IIAB_STATE_FILE" ] && grep -q "^${var}_" "$IIAB_STATE_FILE"; then
        echo "Installed state:"
        grep "^${var}_" "$IIAB_STATE_FILE" | sed 's/^/  /'
    else
        echo "Installed state: not installed"
    fi
    if [ -f "$LOCAL_VARS_FILE" ] && grep -q "^${var}_install:" "$LOCAL_VARS_FILE"; then
        grep "^${var}_install:" "$LOCAL_VARS_FILE" | sed 's/^/  desired /'
    elif [ -f "$DEFAULT_VARS_FILE" ] && grep -q "^${var}_install:" "$DEFAULT_VARS_FILE"; then
        grep "^${var}_install:" "$DEFAULT_VARS_FILE" | sed 's/^/  default /'
    fi
    if [ -f "$LOCAL_VARS_FILE" ] && grep -q "^${var}_enabled:" "$LOCAL_VARS_FILE"; then
        grep "^${var}_enabled:" "$LOCAL_VARS_FILE" | sed 's/^/  desired /'
    elif [ -f "$DEFAULT_VARS_FILE" ] && grep -q "^${var}_enabled:" "$DEFAULT_VARS_FILE"; then
        grep "^${var}_enabled:" "$DEFAULT_VARS_FILE" | sed 's/^/  default /'
    fi
    if [ -f "$IIAB_INI_FILE" ] && grep -q "^${var}_version[[:space:]]*=" "$IIAB_INI_FILE"; then
        grep "^${var}_version[[:space:]]*=" "$IIAB_INI_FILE" | tail -1 | sed 's/^/  installed /'
    fi
    echo
}
