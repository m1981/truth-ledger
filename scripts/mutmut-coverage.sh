#!/usr/bin/env bash
# mutmut-coverage.sh -- (re)generate the .coverage file mutmut 2.x consumes.
#
# Two consumers, one file:
#   * --use-coverage        skips mutants on lines no test executes
#   * mutmut_config.py      reads the per-line dynamic CONTEXTS to run only the
#                           tests that touch the mutated line
#
# The second is what turns days into minutes, and it only works because
# [tool.coverage.run] dynamic_context = "test_function" is set in pyproject.toml.
# Without contexts the file still works for --use-coverage, but every mutant
# falls back to the full 9.7s suite.
#
# Run this again after adding or renaming tests -- a stale .coverage silently
# under-selects, and an under-selected mutant reads as "survived".
#
# TRUTH_MUTMUT_SUITE picks the suite (default: the core suite), and must match
# the one scripts/mutmut-runner.sh will run -- contexts recorded from one suite
# select tests that do not exist in another. See mutmut-runner.sh for why.
# NOTE: .coverage holds ONE suite's contexts at a time, so re-run this for the
# core suite before scoring a core module again.
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="${PYTHONPATH:+$PYTHONPATH:}$HOME/.cache/truth-ledger-pylib"
rm -f .coverage
uv run --python 3.14 --with coverage --no-project \
    python -m coverage run \
    "${TRUTH_MUTMUT_SUITE:-template/scripts/test-truth-core.py}" "$@"
echo "--- contexts recorded ---"
uv run --python 3.14 --with coverage --no-project \
    python -c "
from coverage import Coverage
c = Coverage('.coverage'); c.load()
d = c.get_data()
ctx = [x for x in d.measured_contexts() if x]
print(f'{len(d.measured_files())} files, {len(ctx)} test contexts')
"
