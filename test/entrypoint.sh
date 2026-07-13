#!/usr/bin/env bash
# Clean-room entrypoint. Drops you into a BARE machine with a clean, empty
# working folder (intentionally NOT a Spec Kit project), places the installer
# under test at a known path, then hands off. The installer is meant to
# bootstrap everything itself, so we set nothing up for it.
#
# The installer to test arrives one of two ways (set by test/run.sh):
#   * mounted at /work/spectra-setup.py        — the local working copy
#   * downloaded from a release into the same path  — the published artifact
#
# Commands (CMD / `docker run ... <cmd>`):
#   shell    drop into an interactive shell in the project (default)
#   install  run the installer once, then drop into a shell to inspect state
#   run      run the installer once and exit with its exit code
set -euo pipefail

INSTALLER="/work/spectra-setup.py"
PROJECT_DIR="/work/project"

c() { printf '\033[38;5;141m%s\033[0m\n' "$*"; }
dim() { printf '\033[38;5;98m%s\033[0m\n' "$*"; }

if [[ ! -f "$INSTALLER" ]]; then
  echo "No installer found at $INSTALLER." >&2
  echo "Did you launch via test/run.sh? It mounts/downloads the installer." >&2
  exit 1
fi

# Clean, empty working folder — deliberately NOT a Spec Kit project so the
# installer exercises its own `specify init` bootstrap (step 2).
mkdir -p "$PROJECT_DIR"
cp "$INSTALLER" "$PROJECT_DIR/spectra-setup.py"
cd "$PROJECT_DIR"

banner() {
  echo
  c "Spectra installer clean-room — bare machine"
  dim "  no specify · no uv · no .specify/ · no catalog registered"
  echo
  echo "  Run the installer end to end:   python3 spectra-setup.py"
  echo "  It will, in order:"
  echo "    • install uv + Spec Kit (latest release)"
  echo "    • offer to 'specify init' this folder (pick your agent when prompted)"
  echo "    • register the public Spectra catalog and list extensions"
  echo
  echo "  Then install the extension (no auth needed — the catalog is public):"
  echo "    specify extension add spectra"
  echo
  echo "  Inspect what the installer did:"
  echo "    command -v uv specify ; specify --version"
  echo "    cat .specify/extension-catalogs.yml 2>/dev/null"
  echo
}

case "${1:-shell}" in
  shell)
    banner
    exec /bin/bash -l
    ;;
  install)
    banner
    python3 spectra-setup.py || true
    echo
    c "Installer finished — the Spectra catalog is registered."
    c "Try: specify extension add spectra"
    exec /bin/bash -l
    ;;
  run)
    exec python3 spectra-setup.py
    ;;
  *)
    # Anything else: run it verbatim (e.g. a one-off scenario command).
    exec "$@"
    ;;
esac
