"""The process exit codes, in one place both `cli.py` and `install.py` can reach.

They lived in `cli.py` until the install flow needed to return them. It cannot import them from there:
`cli.py` imports `install.py`, so a back-import would be circular, and `run_install` was returning bare
`0` / `1` literals as a result. Splitting the constants out is the smallest fix that leaves one source of
truth — `cli.py` re-exports these names, so `cli.EXIT_OK` still resolves for anything that reads it that
way.

The values are unchanged and are the tool's published contract:

* `0` — the command did what it was asked, or was asked to do nothing.
* `1` — the user declined an offered action. Not a failure; the requested end state simply does not hold.
* `2` — bad flag or unknown command (argparse's convention).
* `3` — published data could not be retrieved.
* `4` — a delegated `specify` or `uv` command failed.
* `5` — the project is not in the required state, so the question could not be asked at all.
* `130` — interrupted.

`4` is what a failed **attempt** at coverage returns, and `0` is what an abstention with a stated reason
returns (spec 011 § Clarifications). The distinction is the whole reason this module exists.
"""

from __future__ import annotations

EXIT_OK = 0
EXIT_DECLINED = 1        # the user declined an offered action
EXIT_USAGE = 2           # bad flag or unknown command (argparse's convention)
EXIT_UNREACHABLE = 3     # published data could not be retrieved
EXIT_DELEGATION = 4      # a delegated `specify` or `uv` command failed
EXIT_PROJECT_STATE = 5   # the project is not in the required state
EXIT_INTERRUPTED = 130
