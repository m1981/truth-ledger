#!/usr/bin/env bash
# check-truth.sh -- pre-commit / CI gate for the truth ledger.
# Gate contract v0.4 (the script's own semantics, unchanged since);
# current CLI: v0.9.32 -- this line is pinned in lockstep with the CLI
# docstring by test-truth-core.py TestCrossSurfaceVersions (ADR-026).
#
# INV-A (STRICT append-only): the staged ledger must be a line-prefix
#   extension of the committed ledger. This blocks deletions, edits, AND
#   mid-file insertions (v0.2's "no deleted diff lines" heuristic passed
#   pure-addition tampering: mid-file inserts and duplicate-id appends
#   were accepted; the fold's first-claim-wins now also defuses the
#   latter, defense in depth).
# INV-B: every staged record satisfies the schema (via `truth validate`).
#
# Exit codes: 0 ok / 1 governance failure / 2 environment problem.
set -u
LEDGER=".truth/claims.jsonl"
TRUTH="scripts/truth"

if ! git diff --cached --name-only -- "$LEDGER" | grep -q .; then
  exit 0
fi

# Capture each ledger snapshot ONCE, rc checked: an unchecked `git show`
# in a pipeline fed the checks an EMPTY stream on failure -- head -n of
# nothing compared equal and `validate --stdin` blessed 0 records, a
# false green in the exact lane this gate exists to close (L3-F7). A
# git that cannot serve the content is an environment problem (exit 2),
# never a pass.
STAGED="$(mktemp)" || exit 2
trap 'rm -f "$STAGED" "${COMMITTED:-}"' EXIT
if ! git show ":$LEDGER" > "$STAGED"; then
  echo "check-truth: cannot read staged ledger from git (exit 2: environment, not governance)" >&2
  exit 2
fi

if git cat-file -e "HEAD:$LEDGER" 2>/dev/null; then
  COMMITTED="$(mktemp)" || exit 2
  if ! git show "HEAD:$LEDGER" > "$COMMITTED"; then
    echo "check-truth: cannot read committed ledger from git (exit 2: environment, not governance)" >&2
    exit 2
  fi
  OLD_N=$(wc -l < "$COMMITTED")
  if ! cmp -s "$COMMITTED" <(head -n "$OLD_N" "$STAGED"); then
    echo "check-truth: INV-A violation -- $LEDGER is append-only." >&2
    echo "  The staged ledger does not extend the committed ledger:" >&2
    echo "  a record was modified, deleted, or inserted mid-file. To" >&2
    echo "  change a claim's status, append a verdict or invalidation." >&2
    exit 1
  fi
  NEW_N=$(wc -l < "$STAGED")
  if [ "$NEW_N" -lt "$OLD_N" ]; then
    echo "check-truth: INV-A violation -- staged ledger is shorter than HEAD's." >&2
    exit 1
  fi
fi

if [ ! -x "$TRUTH" ] && [ ! -f "$TRUTH" ]; then
  echo "check-truth: cannot find $TRUTH (exit 2: environment, not governance)" >&2
  exit 2
fi
if ! python3 "$TRUTH" validate --stdin < "$STAGED"; then
  echo "check-truth: INV-B violation -- staged ledger fails schema validation." >&2
  exit 1
fi
exit 0
