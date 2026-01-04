#!/bin/bash
# ===================================================================================
# IIAB Patch Maintenance Tool (v3.1 - Top Notch Edition)
# ===================================================================================
#
# Robust, modular tool for managing Git patches against upstream repositories.
# Designed for Ansible roles but generic enough for any patch workflow.
#
# Features:
# - Multi-patch support (independent patch files)
# - Automatic metadata stripping (chmod/file mode noise)
# - Selective file export (prevents bloat)
# - Rebase support (update patches against new upstream versions)
# - Robust error handling, whitespace leniency, and safety checks
#
# ===================================================================================

set -e

# ===================================================================================
# Configuration & Defaults
# ===================================================================================

SCRIPT_DIR="$(dirname "$(realpath "$0")")"
WORK_DIR="/tmp/iiab-patch-work-$(id -u)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# ===================================================================================
# Helper Functions
# ===================================================================================

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

check_deps() {
    for cmd in git sed du awk dirname realpath; do
        if ! command -v "$cmd" &>/dev/null; then
            log_error "Missing required dependency: $cmd"
        fi
    done
}

usage() {
    echo ""
    echo -e "${YELLOW}IIAB Patch Maintenance Tool (v3.1)${NC}"
    echo ""
    echo "Usage: $0 [command] <args>"
    echo ""
    echo "Commands:"
    echo "  setup <repo_url> <patch_path> [ref]  Clone repo and apply patch."
    echo "                                       (Optional [ref]: tag/branch/commit to checkout)"
    echo "  update <version>                     Fetch upstream and rebase current workspace."
    echo "  finish <patch_path> [files...]       Export to patch file (cleanly)."
    echo "  clean-all [directory]                Strip metadata from all patches in directory."
    echo ""
    echo "Arguments:"
    echo "  <repo_url>    Git URL (e.g. https://github.com/iiab/calibre-web.git)"
    echo "  <patch_path>  Path to patch file (absolute or relative)"
    echo "  <version>     Upstream tag/branch to rebase onto"
    echo ""
    exit 1
}

# Strip metadata noise from a patch file
strip_metadata() {
    local pfile="$1"
    if [ ! -f "$pfile" ]; then return; fi
    # Remove 'old mode', 'new mode', 'new file mode', 'index' hashes
    # Remove 'old mode' and 'new mode' (permissions), but KEEP 'new file mode'
    sed -i '/^old mode 100/d; /^new mode 100/d' "$pfile"
    # sed -i '/^index [0-9a-f]*\.\.[0-9a-f]*/d' "$pfile" # Keep index lines for safety
    log_info "Cleaned metadata (permissions) from $(basename "$pfile")"
}

# ===================================================================================
# Commands
# ===================================================================================

do_clean_all() {
    TARGET_DIR="${1:-.}"
    if [ ! -d "$TARGET_DIR" ]; then
        log_error "Directory not found: $TARGET_DIR"
    fi
    log_info "Cleaning patches in $TARGET_DIR..."
    for p in "$TARGET_DIR"/*.patch; do
        if [ -f "$p" ]; then strip_metadata "$p"; fi
    done
    log_success "All patches cleaned."
}

do_setup() {
    REPO_URL="$1"
    PATCH_PATH="$(realpath "$2")"
    REF="$3"

    if [ -z "$REPO_URL" ] || [ -z "$2" ]; then usage; fi
    if [ ! -f "$PATCH_PATH" ]; then log_error "Patch file not found: $PATCH_PATH"; fi

    log_info "Setting up workspace in $WORK_DIR..."

    # Cleanup Previous
    if [ -d "$WORK_DIR" ]; then rm -rf "$WORK_DIR"; fi

    # Clone
    log_info "Cloning $REPO_URL..."
    git clone "$REPO_URL" "$WORK_DIR"
    cd "$WORK_DIR"

    # Checkout specific ref if requested
    if [ -n "$REF" ]; then
        log_info "Checking out $REF..."
        git checkout "$REF"
    fi

    # Configure Git Safety
    git config user.email "patcher@iiab.io"
    git config user.name "IIAB Patch Maintainer"

    # Apply Patch
    log_info "Applying $(basename "$PATCH_PATH")..."
    
    # Strategy 1: Clean Apply
    if git apply --check "$PATCH_PATH" 2>/dev/null; then
        git apply "$PATCH_PATH"
        git add .
        git commit -m "Applied local patch"
        log_success "Patch applied cleanly."
    else
        log_warn "Standard apply failed. Trying lenient whitespace apply..."
        # Strategy 2: Whitespace Lenient
        if git apply --ignore-space-change --ignore-whitespace "$PATCH_PATH" 2>/dev/null; then
             git add .
             git commit -m "Applied local patch (whitespace relaxed)"
             log_success "Patch applied with whitespace fuzzing."
        # Strategy 3: 3-Way Merge
        elif git apply --3way "$PATCH_PATH"; then
             git add .
             git commit -m "Applied local patch (3-way)"
             log_success "Patch applied via 3-way merge."
        else
             log_error "Failed to apply patch. Please fix conflicts manually in $WORK_DIR"
        fi
    fi
}

do_update() {
    VERSION="$1"
    if [ -z "$VERSION" ]; then log_error "Version required (e.g., v1.2.3)"; fi
    if [ ! -d "$WORK_DIR" ]; then log_error "Run setup first."; fi

    cd "$WORK_DIR"
    log_info "Fetching upstream..."
    git fetch origin

    log_info "Rebasing onto origin/$VERSION..."
    if git rebase "origin/$VERSION"; then
        log_success "Rebase successful."
    else
        log_warn "Conflicts detected during rebase."
        echo "1. Go to $WORK_DIR"
        echo "2. Fix conflicts."
        echo "3. Run 'git rebase --continue'"
        echo "4. Then run '$0 finish ...'"
        exit 1
    fi
}

do_finish() {
    PATCH_PATH="$(realpath "$1")"
    shift
    FILES_TO_INCLUDE=("$@")

    if [ -z "$1" ] && [ -z "$PATCH_PATH" ]; then usage; fi
    if [ ! -d "$WORK_DIR" ]; then log_error "Work directory not found. Run setup first."; fi

    cd "$WORK_DIR"

    # Auto-Stage changes
    if ! git diff-index --quiet HEAD --; then
         log_warn "Staging unstaged changes..."
         git add .
    fi

    log_info "Exporting to $PATCH_PATH..."

    # Detect Base (Robust)
    BASE_REF=""
    if git rev-parse --verify origin/HEAD >/dev/null 2>&1; then
        # Handle cases where HEAD points to something weird or standard refs
        HEAD_TARGET=$(git symbolic-ref --short refs/remotes/origin/HEAD | sed 's|^origin/||')
        BASE_REF="origin/$HEAD_TARGET"
    elif git rev-parse --verify origin/main >/dev/null 2>&1; then
        BASE_REF="origin/main"
    else
        BASE_REF="origin/master"
    fi
    log_info "Detected base reference: $BASE_REF"

    if [ ${#FILES_TO_INCLUDE[@]} -eq 0 ]; then
        log_warn "Exporting ALL changes."
        git diff "$BASE_REF" > "$PATCH_PATH"
    else
        log_info "Exporting only: ${FILES_TO_INCLUDE[*]}"
        git diff "$BASE_REF" -- "${FILES_TO_INCLUDE[@]}" > "$PATCH_PATH"
    fi

    # Cleanup
    strip_metadata "$PATCH_PATH"
    
    SIZE=$(du -h "$PATCH_PATH" | cut -f1)
    log_success "Patch saved: $(basename "$PATCH_PATH") ($SIZE)"
}

# ===================================================================================
# Entry Point
# ===================================================================================

check_deps
CMD="$1"
shift || true

case "$CMD" in
    setup) do_setup "$1" "$2" "$3" ;;
    update) do_update "$1" ;;
    finish) do_finish "$@" ;;
    clean-all) do_clean_all "$1" ;;
    *) usage ;;
esac
