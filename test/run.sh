#!/usr/bin/env bash
# Spin up a clean container and test the Spectra CLI in it.
#
# By default it tests your *local working copy* — the repo is mounted in read-only,
# copied inside the container, and installed with `uv tool install --from <copy>`, so
# you exercise your tree exactly as uv would build it without dirtying it. Run this
# before tagging a release. With --published it installs from the GitHub URL instead,
# testing what users actually get.
#
# Usage:
#   test/run.sh                      # interactive shell, local working copy
#   test/run.sh install              # auto-install + run `spectra`, then a shell
#   test/run.sh run                  # run `spectra` once, exit with its code
#   test/run.sh --published          # install from git+https://github.com/... (latest main)
#   test/run.sh --published 3.0.0    # install from that tag
#   test/run.sh --published run
#
# The CLI needs no authentication — the Spectra catalog is public, so it just
# registers the catalog and installs the extensions it advertises.
#
# Each run is a brand-new container: nothing Spectra has touched, no catalog
# registered. Exit the shell and the machine is gone.
set -euo pipefail

REPO_URL="https://github.com/xavient/spectra"
IMAGE="spectra-cli-test"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"

PUBLISHED=""
PUBLISHED_TAG=""
MODE="shell"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --published)
      PUBLISHED=1
      shift
      # An optional bare-semver tag may follow (`--published 3.0.0`).
      if [[ $# -gt 0 && "$1" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        PUBLISHED_TAG="$1"; shift
      fi
      ;;
    shell|install|run) MODE="$1"; shift ;;
    -h|--help) sed -n '2,21p' "$0"; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done

echo "Building $IMAGE …"
docker build -t "$IMAGE" "$HERE"

# Decide which source uv installs the CLI from, and pass it to the entrypoint.
if [[ -n "$PUBLISHED" ]]; then
  SOURCE="git+${REPO_URL}${PUBLISHED_TAG:+@$PUBLISHED_TAG}"
  echo "Testing the PUBLISHED CLI: $SOURCE"
  exec docker run --rm -it \
    -e "SPECTRA_SOURCE=$SOURCE" \
    "$IMAGE" "$MODE"
fi

echo "Testing your LOCAL working copy: $ROOT"
[[ -f "$ROOT/pyproject.toml" ]] || { echo "No pyproject.toml at $ROOT" >&2; exit 1; }

# Mounted read-only: the container copies it before building, so a test run can never
# leave build artifacts (or anything else) behind in your working tree.
exec docker run --rm -it \
  -e "SPECTRA_SOURCE=/work/src" \
  -v "$ROOT:/work/src:ro" \
  "$IMAGE" "$MODE"
