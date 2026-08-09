# Spectra CLI clean-room.
#
# A throwaway machine with only the basics a real new user has (python3, git,
# curl) and *nothing* Spectra has touched — no `specify` CLI, no `.specify/`
# project, no registered catalog. Each `docker run` is a fresh user's first
# five minutes.
#
# Build:  docker build -t spectra-cli-test test/
# Run:    test/run.sh        (see that script / test/README.md)

FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

# Base tooling only. No `gh` is needed: the Spectra catalog is public, so the
# CLI authenticates nothing.
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      python3 python3-venv git curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# uv is the ONE prerequisite, because it is how `spectra` itself is installed —
# a user who is about to run `uv tool install` has already installed uv. Everything
# downstream of it (the Spec Kit CLI, the project, the catalog, the extensions) is
# deliberately absent so the CLI has to bootstrap it, which is the thing under test.
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# uv drops binaries here, and so does `uv tool install`.
ENV PATH="/root/.local/bin:${PATH}"

ENV SHELL=/bin/bash
WORKDIR /work

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["shell"]
