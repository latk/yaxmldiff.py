# -*- makefile -*-

# Run all commands within an UV context, so that deps are auto-installed.
set shell := ['uv', 'run', 'bash', '-euo', 'pipefail', '-c']
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
[positional-arguments]
test *args:
    pytest -v "$@"

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
