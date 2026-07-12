# -*- makefile -*-

# Run all commands within an UV context, so that deps are auto-installed.
set shell := ['uv', 'run', 'bash', '-euo', 'pipefail', '-c']
set positional-arguments
sources := "src"

# default checks
qa *args: lint types (test args)

# formatting + lints
lint:
    ruff format --diff
    ruff check

# reformat code
reformat:
    ruff format

# check types with Mypy
types:
    mypy {{sources}}

# run the test suite
test *args:
    pytest -v "$@"

# Run tests under multiple configurations (Python and lxml versions)
multitest *args:
  #!/usr/bin/env bash
  set -xeuo pipefail
  uv run --isolated --python=3.10 pytest -v "$@"
  uv run --isolated --python=3.11 pytest -v "$@"
  uv run --isolated --python=3.12 pytest -v "$@"
  uv run --isolated --python=3.13 pytest -v "$@"
  uv run --isolated --python=3.14 pytest -v "$@"
  uv run --isolated --resolution=lowest pytest -v "$@"

# build wheels into `dist/` folder
dist:
    #!/usr/bin/env bash
    set -euo pipefail
    bold=$'\e[1m'; reset=$'\e[0m'
    explicitly() { printf '%s' "${bold}running:${reset}"; echo " ${@@K}"; "$@"; }  # print command before running

    explicitly uv build

    # run smoke tests for the build artifacts
    for dist in dist/yaxmldiff-*.{whl,tar.gz}; do
      echo "${bold}running smoke test for ${dist}${reset}"
      explicitly uv run --isolated --no-sync --with "$dist" \
        python -c "import yaxmldiff; assert yaxmldiff.compare_xml('<x/>', '<x/>') is None"
    done
    echo "${bold}all smoke tests succeeded${reset}"
