#!/usr/bin/env bash
# Scenario helpers for the Spectra clean-room, sourced into the container's interactive shell.
#
# The point of these is that **nothing is mocked**. Each one puts a real component into a real
# out-of-date state, so `spectra version` and `spectra update` exercise the same detection paths they
# will in front of a user:
#
#   stale_specify      installs an older specify-cli, so `specify self check` genuinely reports a
#                      newer release exists
#   stale_integration  rewrites the version in .specify/integration.json, which is the only place the
#                      integration version is recorded
#   stale_agents       rewrites the version in the installed extension manifest
#   stale_cli          rebuilds your working copy with a lower VERSION, so the real GitHub release feed
#                      is genuinely ahead of the installed command
#
# `stale_cli` is the one that needs explaining: you cannot test it by installing an *old* Spectra CLI,
# because an old CLI has no four-component report to test. So it installs *your* code carrying a low
# version number instead — the comparison it then makes against the live release feed is real.
#
# Run `scenarios` in the container for the menu.

SPECTRA_SRC_COPY="${SPECTRA_SRC_COPY:-/tmp/spectra-src}"
PROJECT_DIR="${PROJECT_DIR:-/work/project}"

# Kept in step with the newest published Spec Kit release; `stale_specify` installs older than this.
SPECIFY_OLD_TAG_DEFAULT="v0.16.0"

_c()   { printf '\033[38;5;141m%s\033[0m\n' "$*"; }
_dim() { printf '\033[38;5;98m%s\033[0m\n' "$*"; }
_ok()  { printf '\033[38;5;42m✓\033[0m %s\n' "$*"; }
_warn(){ printf '\033[38;5;221m!\033[0m %s\n' "$*"; }
_err() { printf '\033[38;5;203m✗ %s\033[0m\n' "$*"; }

_require_project() {
  if [[ ! -d "$PROJECT_DIR/.specify" ]]; then
    _err "No Spec Kit project at $PROJECT_DIR yet."
    _dim "  Run 'bootstrap' first (or 'spectra install' by hand)."
    return 1
  fi
}

# --------------------------------------------------------------------------- #
# Inspecting
# --------------------------------------------------------------------------- #

# What each component actually reports right now, read from source rather than from `spectra version`,
# so you can confirm the CLI's verdict against ground truth.
stack_truth() {
  _c "Ground truth (read directly, not via spectra):"
  printf '  %-22s %s\n' "specify (installed)" "$(specify --version 2>/dev/null | head -1 || echo 'not installed')"
  printf '  %-22s %s\n' "specify self check"  "$(specify self check 2>/dev/null | head -1 || echo 'n/a')"
  printf '  %-22s %s\n' "integration.json"    "$(python3 -c "
import json,sys
try: print(json.load(open('$PROJECT_DIR/.specify/integration.json'))['version'])
except Exception: print('unreadable/absent')" 2>/dev/null)"
  printf '  %-22s %s\n' "spectra CLI"         "$(cd /tmp && spectra 2>/dev/null | grep -o 'cli v[0-9.]*' || echo 'unknown')"
  printf '  %-22s %s\n' "extension manifest"  "$(grep -m1 '^  version:' "$PROJECT_DIR/.specify/extensions/spectra/extension.yml" 2>/dev/null | tr -d ' version:"' || echo 'absent')"
  echo
}

# The command under test, plus its exit code — which is half the contract.
stack_show() {
  cd "$PROJECT_DIR" 2>/dev/null || true
  _c "\$ spectra version"
  spectra version; local code=$?
  _dim "  exit=$code  (0 is correct for every verdict, including unknown)"
}

# --------------------------------------------------------------------------- #
# Making things stale
# --------------------------------------------------------------------------- #

# 1) A genuinely older Spec Kit CLI. Also drags the Core agents row with it, because the integration
#    version tracks the CLI version — so this scenario should show TWO rows needing updates.
stale_specify() {
  local tag="${1:-$SPECIFY_OLD_TAG_DEFAULT}"
  _c "Installing specify-cli @ $tag (older than the latest release) …"
  uv tool install specify-cli --from "git+https://github.com/github/spec-kit.git@${tag}" --force \
    || { _err "install failed — is $tag a real tag? try: stale_specify v0.15.2"; return 1; }
  _ok "specify is now $(specify --version 2>/dev/null | head -1)"
  _dim "  Expect: Specify CLI AND Core agents both 'needs updating' (the integration tracks the CLI)."
}

# 2) The integration recorded against an older Spec Kit. This is the real state of the Spectra repo
#    itself, and the gap nothing surfaced before this feature.
stale_integration() {
  local version="${1:-0.12.14}"
  _require_project || return 1
  python3 - "$PROJECT_DIR/.specify/integration.json" "$version" <<'PY'
import json, sys
path, version = sys.argv[1], sys.argv[2]
with open(path) as fh:
    data = json.load(fh)
data["version"] = version
with open(path, "w") as fh:
    json.dump(data, fh, indent=2)
    fh.write("\n")
print(f"integration.json version -> {version}")
PY
  _ok "Core agents pinned to $version"
  _dim "  Expect: Core agents 'needs updating', the other three unchanged."
}

# 3) The installed extension manifest rolled back.
#
# Spec Kit records an extension's installed version in `.specify/extensions/.registry`, while Spectra
# scans the manifest. Editing only the manifest produces a state Spectra calls stale and Spec Kit calls
# current — so `spectra update` delegates, Spec Kit says "up to date", exits 0, and nothing moves. Both
# are rewritten here so the scenario is one `spectra update` can actually repair.
#
# Pass `--manifest-only` to reproduce the disagreement deliberately: `spectra update` should then warn
# that the underlying command reported success without changing anything, rather than claiming a win.
stale_agents() {
  local version="1.0.0" manifest_only=""
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --manifest-only) manifest_only=1; shift ;;
      *) version="$1"; shift ;;
    esac
  done
  _require_project || return 1
  local manifest="$PROJECT_DIR/.specify/extensions/spectra/extension.yml"
  local registry="$PROJECT_DIR/.specify/extensions/.registry"
  [[ -f "$manifest" ]] || { _err "no extension manifest at $manifest"; return 1; }
  # Only the extension block's own version line, two spaces deep — the same line the CLI scans for.
  python3 - "$manifest" "$version" <<'PY'
import re, sys
path, version = sys.argv[1], sys.argv[2]
text = open(path, encoding="utf-8").read()
new, n = re.subn(r'^(  version:\s*")[^"]+(")', rf'\g<1>{version}\g<2>', text, count=1, flags=re.M)
if not n:
    sys.exit("could not find the extension version line")
open(path, "w", encoding="utf-8").write(new)
print(f"extension.yml version -> {version}")
PY
  if [[ -z "$manifest_only" && -f "$registry" ]]; then
    python3 - "$registry" "$version" <<'PY'
import json, sys
path, version = sys.argv[1], sys.argv[2]
with open(path) as fh:
    data = json.load(fh)
entry = data.get("extensions", {}).get("spectra")
if entry is None:
    sys.exit("no spectra entry in the registry")
entry["version"] = version
with open(path, "w") as fh:
    json.dump(data, fh, indent=2)
    fh.write("\n")
print(f".registry version -> {version}")
PY
    _ok "Spectra agents pinned to $version (manifest + registry)"
    _dim "  Expect: Spectra agents 'needs updating', and 'spectra update' genuinely repairs it."
  else
    _ok "Spectra agents pinned to $version (manifest only)"
    _warn "Spec Kit's registry still says current, so its updater will no-op."
    _dim "  Expect: 'spectra update' warns it reported success without changing anything (exit 4)."
  fi
}

# 4) The command reporting itself behind. Reinstalls YOUR code with a lower VERSION so the comparison
#    against the live release feed is genuine — see the header note on why an old CLI will not do.
stale_cli() {
  local version="${1:-4.0.0}"
  [[ -d "$SPECTRA_SRC_COPY" ]] || { _err "no source copy at $SPECTRA_SRC_COPY (launch via test/run.sh)"; return 1; }
  _c "Rebuilding your working copy as version $version …"
  echo "$version" > "$SPECTRA_SRC_COPY/VERSION"
  uv tool install spectra-cli --from "$SPECTRA_SRC_COPY" --force >/dev/null \
    || { _err "reinstall failed"; return 1; }
  _ok "spectra now reports $(cd /tmp && spectra 2>/dev/null | grep -o 'cli v[0-9.]*')"
  _dim "  Expect: Spectra CLI 'needs updating' against the newest published release."
  _warn "This is still your code — only the version number is lower."
}

# --------------------------------------------------------------------------- #
# Putting it back
# --------------------------------------------------------------------------- #

# Restore every component to current. Uses the real VERSION from your tree, and the newest Spec Kit.
stack_reset() {
  _c "Restoring every component to current …"
  uv tool install specify-cli --from git+https://github.com/github/spec-kit.git --force >/dev/null 2>&1 \
    && _ok "specify: latest"
  if [[ -f "$SPECTRA_SRC_COPY/VERSION.orig" ]]; then
    cp "$SPECTRA_SRC_COPY/VERSION.orig" "$SPECTRA_SRC_COPY/VERSION"
    uv tool install spectra-cli --from "$SPECTRA_SRC_COPY" --force >/dev/null 2>&1 \
      && _ok "spectra CLI: $(cat "$SPECTRA_SRC_COPY/VERSION")"
  fi
  if [[ -d "$PROJECT_DIR/.specify" ]]; then
    local current
    current="$(specify --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)"
    [[ -n "$current" ]] && stale_integration "$current" >/dev/null && _ok "integration: $current"
    specify extension update spectra >/dev/null 2>&1 \
      && _ok "spectra agents: re-synced from the catalog" \
      || _warn "extension re-sync skipped (offline?)"
  fi
  echo
  _dim "Run 'stack_show' to confirm."
}

# --------------------------------------------------------------------------- #
# Degraded environments
# --------------------------------------------------------------------------- #

# Run a command with `specify` genuinely unavailable.
#
# PATH surgery cannot do this: uv installs `specify` and `spectra` into the *same* directory, so
# dropping it from PATH removes the command under test along with it. Moving the shim aside is the only
# honest way to simulate "Spec Kit is not installed".
#
#   no_specify spectra version     -> expect the first two rows unknown, exit 0
no_specify() {
  local shim
  shim="$(command -v specify || true)"
  if [[ -z "$shim" ]]; then
    _warn "specify is already absent; running as-is."
    "$@"
    return $?
  fi
  mv "$shim" "${shim}.hidden"
  local code=0
  "$@" || code=$?
  mv "${shim}.hidden" "$shim"
  return $code
}

# Run a command with no network, to exercise every "latest could not be resolved" path at once.
# Expect four unknown rows and the "nothing could be checked" wording — never a claim of currency.
no_network() {
  _dim "Pointing published-data reads at a closed port and blocking GitHub …"
  SPECTRA_RAW_BASE="http://127.0.0.1:9" SPECTRA_UPDATE_REPO="127.0.0.1/nope" "$@"
}

# --------------------------------------------------------------------------- #
# Bootstrap
# --------------------------------------------------------------------------- #

# A working project, non-interactively: Spec Kit installed, project initialized, Spectra installed.
# `spectra install` is interactive by design, so this drives the pieces directly.
bootstrap() {
  local integration="${1:-claude}"
  _c "Bootstrapping a Spec Kit project with Spectra ($integration) …"
  command -v specify >/dev/null || uv tool install specify-cli --from git+https://github.com/github/spec-kit.git --force
  mkdir -p "$PROJECT_DIR" && cd "$PROJECT_DIR"
  # --ignore-agent-tools: the container has no agent CLI installed and does not need one. We are
  # testing Spectra's own version/update surface, not whether Claude Code is on PATH.
  [[ -d .specify ]] || specify init --here --integration "$integration" --force --ignore-agent-tools
  specify extension catalog add \
    https://raw.githubusercontent.com/xavient/spectra/main/catalog.json \
    --name spectra --priority 5 --install-allowed >/dev/null 2>&1 || true
  specify extension add spectra --force >/dev/null 2>&1 || specify extension add spectra || true
  echo
  _ok "Project ready at $PROJECT_DIR"
  stack_show
}

# --------------------------------------------------------------------------- #
# Menu
# --------------------------------------------------------------------------- #

scenarios() {
  cat <<'MENU'

  Spectra stack scenarios — nothing here is mocked

  Setup
    bootstrap [integration]     install Spec Kit, init the project, add Spectra (default: claude)
    stack_show                  run `spectra version` and show its exit code
    stack_truth                 read each version from source, to check the CLI against ground truth

  Make one component stale
    stale_specify [tag]         older specify-cli        (default v0.16.0) -> expect 2 rows stale
    stale_integration [ver]     older integration.json   (default 0.12.14)
    stale_agents [ver]          older extension.yml      (default 1.0.0)
    stale_cli [ver]             rebuild your code lower  (default 4.0.0)

  Put it back
    stack_reset                 restore all four to current

  Worth trying
    spectra version                  four rows; exit 0 for every verdict
    spectra update                   one prompt, then updates in canonical order
    spectra update --yes             no prompt
    spectra cli version              retired -> exit 2, names its replacement
    spectra cli update               retired -> exit 2
    spectra cli uninstall            still here, unchanged
    spectra --help                   Tool commands panel has ONE row now
    cd /tmp && spectra version       exit 5: needs a project (this is intended)
    cd /tmp && spectra               the banner's `cli vX.Y.Z` works anywhere

  Degraded paths (the ones most likely to regress)
    no_specify spectra version              Spec Kit absent -> 2 rows unknown, still exit 0
    no_specify spectra update               those 2 skipped, not attempted; exit reflects the rest
    no_network spectra version              nothing resolvable -> 4 unknown rows, exit 0
    no_network spectra update               says nothing could be checked; never claims currency
    spectra version --no-update-check       suppresses ONLY the Spectra CLI lookup
    rm .specify/integration.json && spectra version    one row unknown, rest fine
    echo garbage > .specify/integration.json && spectra version   same, malformed

  Note on `no_specify`: PATH surgery cannot hide Spec Kit, because uv installs `specify` and
  `spectra` into the same directory. The helper moves the shim aside and puts it back.

MENU
}
