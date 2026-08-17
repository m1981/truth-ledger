#!/usr/bin/env bash
# mutmut-runner.sh -- the --runner mutmut 2.x invokes for every mutant.
#
# Why this is a script and not just `python3 template/scripts/test-truth-core.py`
# on the mutmut command line:
#
#   1. mutmut splits --runner with shlex.split() and execs WITHOUT a shell, so
#      an inline `VAR=value cmd` prefix is passed as a literal argv[0] and fails.
#   2. Under `uvx`, PATH puts uvx's own interpreter first, so a bare `python3`
#      is mutmut's 3.11 -- not the 3.14 that ~/.cache/truth-ledger-pylib was
#      built against. jsonschema then fails to import (rpds is a cpython-3.14
#      .so), TestJsonschemaPresent fails, and EVERY mutant reads as killed by a
#      test that was already red. A green baseline is the whole premise of a
#      mutation score, so this must be pinned, not waived with
#      TRUTH_ALLOW_NO_JSONSCHEMA=1.
#
# Do NOT cd here: mutmut mutates source files in place, relative to the cwd it
# was started in.
#
# WHICH SUITE
#
# TRUTH_MUTMUT_SUITE names the suite to score against; it defaults to the core
# suite, so every existing invocation is unchanged. It exists because the
# runner and the module under mutation must agree: scoring
# template/truthlib/structural.py against test-truth-core.py would run 442 tests
# that never import it, and EVERY mutant would read as "survived" -- a 0% score
# that measures the wiring, not the suite. Set it in the same command that
# sets --paths-to-mutate, and set it for scripts/mutmut-coverage.sh too, or the
# per-mutant test selection is drawn from the wrong suite's contexts:
#
#   TRUTH_MUTMUT_SUITE=template/scripts/test-structural.py \
#       bash scripts/mutmut-coverage.sh
#   TRUTH_MUTMUT_SUITE=template/scripts/test-structural.py \
#       ./scripts/mutate.sh run --paths-to-mutate template/truthlib/structural.py
set -euo pipefail
export PYTHONPATH="${PYTHONPATH:+$PYTHONPATH:}$HOME/.cache/truth-ledger-pylib"
exec /opt/homebrew/bin/python3 \
    "${TRUTH_MUTMUT_SUITE:-template/scripts/test-truth-core.py}" "$@"
