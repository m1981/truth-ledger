#!/usr/bin/env bash
# mutate.sh -- mutation testing for truthlib.
#
#   ./scripts/mutate.sh                                 # whole package (SLOW: see below)
#   ./scripts/mutate.sh run --paths-to-mutate template/truthlib/kernel.py
#   ./scripts/mutate.sh results                         # survivors from the last run
#   ./scripts/mutate.sh show <id>                       # the diff of one mutant
#   ./scripts/mutate.sh apply <id>                      # put one mutant on disk to debug it
#
# Scope and rationale live in [tool.mutmut] in pyproject.toml -- including why
# this is mutmut 2.5.1 and not 3.x. This wrapper supplies only what a config
# file cannot: mutmut 2.5.1 predates Python 3.13 and does not run on this
# machine's default interpreter, so its own interpreter is pinned to 3.11. The
# TESTS still run on 3.14 -- see scripts/mutmut-runner.sh.
#
# NOTE: mutmut 2.x mutates template/truthlib/*.py IN PLACE and restores each
# file after each mutant. A hard kill (SIGKILL, power loss) can leave a mutated
# file on disk. `git status template/truthlib/` before you commit.
#
# `mutmut run` exits non-zero when mutants survive, which is a finding, not a
# failure of this script -- so no `set -e` around the exec.
set -uo pipefail
cd "$(dirname "$0")/.."
exec uvx --python 3.11 --with coverage mutmut==2.5.1 "${@:-run}"
