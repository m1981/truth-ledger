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
#
# RUN scripts/mutmut-coverage.sh FIRST, or the survivor list lies. mutmut 2.x
# picks which tests to run per mutant from recorded context coverage; if that
# data predates your edit, mutants are scored against the wrong tests. Measured
# 2026-08-18 on gates.py: three consecutive runs over the SAME tree reported 86,
# 42 and 80 mutants, and one "survivor" (`or` -> `and` in _gate_scope_decay's
# override_decay argument) was killed FOUR times over when applied by hand.
# `make mutate` regenerates coverage first and is the safe entry point; calling
# this script directly is not. Ground truth for any survivor is
# `./scripts/mutate.sh apply <id>` followed by running the suite yourself.
set -uo pipefail
cd "$(dirname "$0")/.."
exec uvx --python 3.11 --with coverage mutmut==2.5.1 "${@:-run}"
