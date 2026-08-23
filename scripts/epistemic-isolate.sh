#!/usr/bin/env bash
# epistemic-isolate: restore the MEASURING APPARATUS from origin/main
# before a judging run reads any of it (ADR-058).
#
# META-REPO ONLY — untemplated, like release-battery.sh and fact-health.sh
# (ADR-003 rule 2: this encodes this repo's release policy, not the
# machinery a consumer gets).
#
# WHY THIS EXISTS. The layer has three tiers: L0 is the code and the world,
# L1 is the ledger and its instrument (truthlib), L2 is the oracle that
# checks whether L1 told the truth — CI, the battery, a human. The worst
# available failure is a leak between L1 and L2: a system that authorizes
# its own lies. An agent that can edit `template/truthlib/` and then run
# the battery has exactly that power, and it does not need to be malicious
# to use it. Widening `.truth/evidence-allow`, softening a refusal string,
# making one gate return None — each turns a red run green, and each looks
# like an ordinary edit in the diff.
#
# So a judging run is given an instrument it cannot have authored: the one
# on origin/main, which got there through a push that was itself judged.
#
# WHERE THIS RUNS: nowhere yet, deliberately. It was briefly wired into
# scripts/release-battery.sh and the operator reverted that on 2026-08-23,
# because a LOCAL pre-push hook cannot isolate the very thing a local change
# is editing -- it would judge a legitimate truthlib change's new tests
# against the old implementation and block correct work, and a gate that
# only blocks honest work gets bypassed. Isolation belongs at the CI/CD
# boundary, where the run is not the author. See docs/decisions/058-*.md.
#
# CALLER CONTRACT: restore the working tree when you are done
# (`trap 'git checkout -q HEAD -- <the paths below>' EXIT`). This script
# deliberately does NOT restore on its own exit -- that would undo the
# isolation before the caller had judged anything.
#
# WHAT IT ISOLATES, and why exactly these three:
#   template/truthlib/      the instrument — every gate, every refusal,
#                           the fold that derives status.
#   scripts/truth           the entry the meta-repo's own tooling calls.
#   .truth/evidence-allow   the POLICY deciding which commands the screen
#                           will execute at all. Not code, and the single
#                           highest-leverage file here: widening it admits
#                           evidence the screen exists to refuse.
#
# EXIT CODES: 0 isolated, 2 could not isolate. There is no 1 and no skip
# flag. FAIL-CLOSED is the whole point — if this script cannot establish
# which instrument it is holding, the honest answer is that the caller must
# not run, not that it should run with whatever is lying around.
set -euo pipefail

cd "$(dirname "$0")/.."

ISOLATED_PATHS=(template/truthlib scripts/truth .truth/evidence-allow)

say() { printf 'epistemic-isolate: %s\n' "$*" >&2; }

# --- 1. get origin/main, or refuse --------------------------------------
# Offline, no remote, no such branch, auth failure -- all of them mean the
# same thing here: no trusted reference exists in this clone right now.
if ! git fetch origin main -q 2>/dev/null; then
  say "cannot fetch origin/main -- there is no trusted reference to
    isolate against, so the caller would be judging with whatever this
    working tree happens to contain. Refusing (ADR-058, fail-closed).
    Fix the remote, or run from a clone that has one."
  exit 2
fi

# --- 2. refuse to destroy uncommitted work ------------------------------
# NOT in the ADR's letter, and load-bearing. `git checkout origin/main --
# <path>` overwrites the working tree AND the index with no undo: run it
# over a dirty truthlib and the edits are gone, with no reflog entry and
# no stash to recover from. A gate that silently eats an operator's work
# is a gate they will disable, which costs more than the leak it closed.
#
# Refusing here is strictly MORE fail-closed than the ADR asks: it stops
# on exactly the state where isolation is both destructive and pointless
# (uncommitted instrument changes have not been judged by anything).
DIRTY=$(git status --porcelain -- "${ISOLATED_PATHS[@]}")
if [ -n "$DIRTY" ]; then
  say "the measuring apparatus has UNCOMMITTED changes:
$(printf '%s\n' "$DIRTY" | sed 's/^/      /')
    Isolating would overwrite them irrecoverably, and an uncommitted
    instrument has been judged by nothing. Commit or stash first.
    Refusing (ADR-058, fail-closed)."
  exit 2
fi

# --- 3. install the trusted instrument ----------------------------------
if ! git checkout origin/main -- "${ISOLATED_PATHS[@]}"; then
  say "could not check out the apparatus from origin/main. Refusing
    (ADR-058, fail-closed)."
  exit 2
fi

# --- 4. say what was actually installed ---------------------------------
# The release battery's header rule, borrowed: every arm reports WHAT IT
# EXAMINED. An
# isolation that reports nothing is indistinguishable from one that did
# nothing, and this one leaves no visible trace when HEAD already matched.
REF=$(git rev-parse --short origin/main)
DRIFT=$(git diff --stat "HEAD..origin/main" -- "${ISOLATED_PATHS[@]}" | tail -1)
if [ -n "$DRIFT" ]; then
  say "apparatus restored from origin/main ($REF); it DIFFERS from HEAD:
      $DRIFT
    Whatever runs next is judging with origin/main's instrument, not this
    branch's -- so a change to the instrument ITSELF will be judged by the
    version it replaces. That is the open residual in ADR-058, not a fault
    of this run."
else
  say "apparatus restored from origin/main ($REF); identical to HEAD."
fi
exit 0
