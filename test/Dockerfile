# Spectra installer clean-room.
#
# A throwaway machine with only the basics a real new user has (python3, git,
# curl) and *nothing* Spectra has touched — no `uv`, no `specify` CLI, no
# .specify/ project, no registered catalog. Each `docker run` is a fresh user's
# first five minutes.
#
# Build:  docker build -t spectra-installer-test test/
# Run:    test/run.sh        (see that script / test/README.md)

FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

# Base tooling only. No `gh` is needed: the Spectra catalog is public, so the
# installer authenticates nothing. (`test/run.sh --release` downloads the
# artifact with the *host* gh, not this container's.)
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      python3 python3-venv git curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Intentionally a BARE machine: neither `uv` nor the `specify` CLI is
# pre-installed. spectra-setup.py is meant to bootstrap them itself, so leaving
# them out lets the installer be tested end to end (install uv -> install Spec
# Kit at the latest release -> `specify init`). We only put uv's default tool
# bin dir on PATH so the executables the installer drops there are discoverable.
ENV PATH="/root/.local/bin:${PATH}"

ENV SHELL=/bin/bash
WORKDIR /work

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["shell"]
