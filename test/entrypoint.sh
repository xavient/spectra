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
#   stack    install the CLI, bootstrap a working project non-interactively, then drop into a shell
#            with the stack-scenario helpers loaded (this is the one for testing version/update)
set -euo pipefail

SOURCE="${SPECTRA_SOURCE:?SPECTRA_SOURCE is not set. Did you launch via test/run.sh?}"
PROJECT_DIR="/work/project"
SPECTRA_SRC_COPY="/tmp/spectra-src"
export PROJECT_DIR SPECTRA_SRC_COPY

c() { printf '\033[38;5;141m%s\033[0m\n' "$*"; }
dim() { printf '\033[38;5;98m%s\033[0m\n' "$*"; }

# A local source is mounted read-only so the container can never dirty your working
# tree — but setuptools writes `*.egg-info` into the source dir as it builds, so copy
# it somewhere writable first and build from the copy.
if [[ -d "$SOURCE" ]]; then
  rm -rf "$SPECTRA_SRC_COPY"
  cp -a "$SOURCE" "$SPECTRA_SRC_COPY"
  dim "Copied the mounted working copy to $SPECTRA_SRC_COPY (your tree stays read-only and clean)."
  # Kept so `stack_reset` can undo a `stale_cli` version rewrite.
  cp "$SPECTRA_SRC_COPY/VERSION" "$SPECTRA_SRC_COPY/VERSION.orig" 2>/dev/null || true
  SOURCE="$SPECTRA_SRC_COPY"
fi

# An optional lower version, for landing straight in the "my CLI is behind" state.
if [[ -n "${SPECTRA_FAKE_VERSION:-}" && -d "$SPECTRA_SRC_COPY" ]]; then
  echo "$SPECTRA_FAKE_VERSION" > "$SPECTRA_SRC_COPY/VERSION"
  dim "Building as version $SPECTRA_FAKE_VERSION so the CLI reports itself behind."
fi

c "Installing the Spectra CLI from: $SOURCE"
uv tool install spectra-cli --from "$SOURCE" --force
echo
# Bare `spectra` carries the version in its banner and works from any directory. `--version` was
# removed in 5.0.0 and `spectra cli version` was retired in 6.0.0, so this is the way to read it.
dim "Installed: $(cd /tmp && spectra 2>/dev/null | grep -o 'cli v[0-9.]*' || echo 'unknown')"

# Scenario helpers, available in every interactive shell this container starts.
if [[ -f /usr/local/lib/scenarios.sh ]]; then
  cat >> /root/.bashrc <<'RC'
source /usr/local/lib/scenarios.sh
RC
fi

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
  echo "    spectra cli uninstall        # the one tool-scoped verb left"
  echo "    spectra version             # the whole stack (needs a project)"
  echo "    cd /tmp && spectra          # the banner's version, from anywhere"
  echo
  echo "  Testing version/update scenarios? Relaunch with: test/run.sh stack"
  echo
}

stack_banner() {
  echo
  c "Spectra stack clean-room — a working project, ready to break on purpose"
  dim "  Spec Kit installed · project initialized · Spectra agents installed"
  echo
  echo "  Type 'scenarios' for the menu."
  echo
  echo "  The quick tour:"
  echo "    stack_show           what spectra version reports now"
  echo "    stale_integration    put the core agents behind, then stack_show again"
  echo "    stale_specify        put Spec Kit behind (drags core agents with it)"
  echo "    stale_agents         put the extension behind"
  echo "    stale_cli            put this command behind"
  echo "    spectra update       fix whatever is behind, in canonical order"
  echo "    stack_reset          put everything back"
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
  stack)
    # A working project without prompts, then hand over with the helpers loaded. `spectra install` is
    # interactive by design, so the pieces are driven directly here instead.
    source /usr/local/lib/scenarios.sh
    bootstrap "${SPECTRA_INTEGRATION:-claude}" || true
    stack_banner
    exec /bin/bash -l
    ;;
  *)
    # Anything else: run it verbatim (e.g. a one-off scenario command).
    exec "$@"
    ;;
esac
