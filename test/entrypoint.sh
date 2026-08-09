#!/usr/bin/env bash
# Clean-room entrypoint. Installs the Spectra CLI under test, then drops you into
# a clean, empty working folder (intentionally NOT a Spec Kit project) and hands
# off. Everything downstream of uv — the Spec Kit CLI, the project, the catalog,
# the extensions — is meant to be bootstrapped by `spectra` itself, so we set up
# none of it.
#
# The CLI source arrives via SPECTRA_SOURCE (set by test/run.sh):
#   * /work/src                               — the local working copy, mounted read-only
#   * git+https://github.com/xavient/spectra  — the published CLI (optionally @<tag>)
#
# Commands (CMD / `docker run ... <cmd>`):
#   shell    install the CLI, then drop into an interactive shell (default)
#   install  install the CLI, run `spectra install` once, then drop into a shell to inspect state
#   run      install the CLI, run `spectra install` once and exit with its exit code
set -euo pipefail

SOURCE="${SPECTRA_SOURCE:?SPECTRA_SOURCE is not set. Did you launch via test/run.sh?}"
PROJECT_DIR="/work/project"

c() { printf '\033[38;5;141m%s\033[0m\n' "$*"; }
dim() { printf '\033[38;5;98m%s\033[0m\n' "$*"; }

# A local source is mounted read-only so the container can never dirty your working
# tree — but setuptools writes `*.egg-info` into the source dir as it builds, so copy
# it somewhere writable first and build from the copy.
if [[ -d "$SOURCE" ]]; then
  BUILD_SRC="/tmp/spectra-src"
  rm -rf "$BUILD_SRC"
  cp -a "$SOURCE" "$BUILD_SRC"
  dim "Copied the mounted working copy to $BUILD_SRC (your tree stays read-only and clean)."
  SOURCE="$BUILD_SRC"
fi

c "Installing the Spectra CLI from: $SOURCE"
uv tool install spectra-cli --from "$SOURCE" --force
echo
dim "Installed: $(spectra --version --no-update-check 2>/dev/null || echo 'unknown')"

# Clean, empty working folder — deliberately NOT a Spec Kit project so the CLI
# exercises its own `specify init` bootstrap (step 2).
mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

banner() {
  echo
  c "Spectra CLI clean-room — bare machine"
  dim "  uv only · no specify · no .specify/ · no catalog registered"
  echo
  echo "  Run the CLI end to end:   spectra install"
  echo "  (bare 'spectra' just prints the banner and exits)"
  echo "  It will, in order:"
  echo "    • install Spec Kit (latest release) via uv"
  echo "    • offer to 'specify init' this folder (pick your agent when prompted)"
  echo "    • register the public Spectra catalog and install every extension in it"
  echo
  echo "  Inspect what it did:"
  echo "    command -v uv specify spectra ; specify --version"
  echo "    specify extension list"
  echo "    cat .specify/extension-catalogs.yml 2>/dev/null"
  echo
  echo "  Manage the tool itself:"
  echo "    spectra --version ; spectra --update ; spectra --uninstall"
  echo
}

case "${1:-shell}" in
  shell)
    banner
    exec /bin/bash -l
    ;;
  install)
    banner
    spectra install || true
    echo
    c "Finished — inspect the state above."
    c "Try: specify extension list"
    exec /bin/bash -l
    ;;
  run)
    exec spectra install
    ;;
  *)
    # Anything else: run it verbatim (e.g. a one-off scenario command).
    exec "$@"
    ;;
esac
