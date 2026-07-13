#!/usr/bin/env bash
# Spin up a clean container and test the Spectra installer in it.
#
# By default it tests your *local working copy* of spectra-setup.py — run this
# before tagging a release. With --release <tag> it downloads the published
# artifact from the GitHub release and tests exactly what users will get.
#
# Usage:
#   test/run.sh                      # interactive shell, local working copy
#   test/run.sh install              # auto-run installer, then drop to a shell
#   test/run.sh run                  # run installer once, exit with its code
#   test/run.sh --release v1.2.0     # test the published artifact (interactive)
#   test/run.sh --release v1.2.0 run
#
# The installer needs no authentication — the Spectra catalog is public, so it
# just registers the catalog and lists the extensions. --release downloads the
# published artifact with `gh` (public repo, so no login is required).
#
# Each run is a brand-new container: nothing Spectra has touched, no catalog
# registered. Exit the shell and the machine is gone.
set -euo pipefail

REPO="xavient/spectra"
IMAGE="spectra-installer-test"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"

RELEASE_TAG=""
MODE="shell"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --release) RELEASE_TAG="${2:?--release needs a tag}"; shift 2 ;;
    shell|install|run) MODE="$1"; shift ;;
    -h|--help) sed -n '2,30p' "$0"; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done

echo "Building $IMAGE …"
docker build -t "$IMAGE" "$HERE"

# Decide which installer to mount in.
if [[ -n "$RELEASE_TAG" ]]; then
  TMP="$(mktemp -d)"
  trap 'rm -rf "$TMP"' EXIT
  echo "Downloading installer from release $RELEASE_TAG ($REPO) …"
  gh release download "$RELEASE_TAG" -R "$REPO" -p spectra-setup.py -D "$TMP" --clobber
  INSTALLER="$TMP/spectra-setup.py"
  echo "Testing the PUBLISHED artifact from $RELEASE_TAG."
else
  INSTALLER="$ROOT/spectra-setup.py"
  echo "Testing your LOCAL working copy: $INSTALLER"
fi

[[ -f "$INSTALLER" ]] || { echo "Installer not found: $INSTALLER" >&2; exit 1; }

exec docker run --rm -it \
  -v "$INSTALLER:/work/spectra-setup.py:ro" \
  "$IMAGE" "$MODE"
