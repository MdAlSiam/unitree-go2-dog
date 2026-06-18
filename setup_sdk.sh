#!/usr/bin/env bash
set -euo pipefail

SDK_URL="${UNITREE_SDK2_REPO_URL:-https://github.com/unitreerobotics/unitree_sdk2.git}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SDK_DIR="${SCRIPT_DIR}/unitree_sdk2"
MODE="clone"

usage() {
    cat <<'EOF'
Usage: ./setup_sdk.sh [--clone] [--submodule]

Options:
  --clone      Clone unitree_sdk2 into ./unitree_sdk2 if it is missing (default).
  --submodule  If the current directory is a git repository, initialize/update an
               existing unitree_sdk2 submodule or add it as a new submodule.

Environment:
  UNITREE_SDK2_REPO_URL  Override the SDK git URL.
EOF
}

is_git_repo() {
    git -C "$SCRIPT_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1
}

has_submodule_config() {
    [[ -f "$SCRIPT_DIR/.gitmodules" ]] && grep -q 'path = unitree_sdk2' "$SCRIPT_DIR/.gitmodules"
}

clone_sdk() {
    if [[ -d "$SDK_DIR/.git" ]]; then
        echo "unitree_sdk2 already exists as a git checkout at $SDK_DIR"
        git -C "$SDK_DIR" remote -v | cat
        return 0
    fi

    if [[ -e "$SDK_DIR" ]]; then
        echo "Refusing to overwrite existing path: $SDK_DIR" >&2
        echo "Remove or rename it, then rerun ./setup_sdk.sh." >&2
        return 1
    fi

    echo "Cloning unitree_sdk2 into $SDK_DIR"
    git clone "$SDK_URL" "$SDK_DIR"
}

setup_submodule() {
    if ! is_git_repo; then
        echo "--submodule requires the project root to be a git repository." >&2
        echo "Initialize git first or rerun with --clone." >&2
        return 1
    fi

    if has_submodule_config; then
        echo "Initializing existing unitree_sdk2 submodule"
        git -C "$SCRIPT_DIR" submodule update --init --recursive unitree_sdk2
        return 0
    fi

    if [[ -e "$SDK_DIR" ]]; then
        echo "unitree_sdk2 already exists at $SDK_DIR." >&2
        echo "Remove or move it before adding the SDK as a submodule." >&2
        return 1
    fi

    echo "Adding unitree_sdk2 as a git submodule"
    git -C "$SCRIPT_DIR" submodule add "$SDK_URL" unitree_sdk2
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --clone)
            MODE="clone"
            ;;
        --submodule)
            MODE="submodule"
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown argument: $1" >&2
            usage >&2
            exit 1
            ;;
    esac
    shift
done

if [[ "$MODE" == "submodule" ]]; then
    setup_submodule
else
    clone_sdk
fi