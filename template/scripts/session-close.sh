#!/usr/bin/env bash
# session-close — mechanical end-of-session survival gate.
#
# Knowledge survives sessions only as committed artifacts with ledger ids;
# a session that ends with work in flight loses it at context compaction.
# This script refuses to let that happen silently.
#
# FAIL (exit 1) — survival holes:
#   * uncommitted changes (nothing survives a dirty tree)
#   * the truth CLI failing (a sensor that cannot run must scream, never
#     read as zero counts — the F1 rule)
#   * truth work items still claimed (finish with `done --claim`, or
#     hand back with `start --release`)
#   * spec-health / doc-health failures (when those gates are present)
#   * any failing project gate in scripts/session-gates.d/
# WARN (exit 0) — triage debt, visible but not blocking:
#   * unverified claims (filer != verifier is by design; they still
#     should not accumulate)
#   * verdict-queue size (stale/diverged facts awaiting re-verification)
#
# Project-specific checks (regression gates, tracker-twin audits, ...):
# drop executable *.sh files into scripts/session-gates.d/ — each runs
# from the repo root and contributes FAIL via a non-zero exit.
#
# Usage: bash scripts/session-close.sh
set -u
cd "$(git rev-parse --show-toplevel)" || exit 2

fails=0
warns=0
fail() { printf '  FAIL  %s\n' "$*"; fails=$((fails + 1)); }
warn() { printf '  WARN  %s\n' "$*"; warns=$((warns + 1)); }
ok()   { printf '  ok    %s\n' "$*"; }
# A truth CLI that cannot run must scream, never degrade to zero counts:
# `2>/dev/null | grep -c || true` read a corrupt ledger as "0 claimed,
# safe to close" (the F1 rule, applied to this gate's own sensors).
cli_fail() {
    fail "truth CLI unavailable — nothing below was checked"
    echo
    echo "session-close: $fails failure(s), $warns warning(s)"
    echo "NOT SAFE to end the session — the items above will not survive."
    exit 1
}

echo "session-close checklist"

# 1 — working tree
dirty=$(git status --porcelain | wc -l | tr -d ' ')
if [ "$dirty" -gt 0 ]; then
    fail "uncommitted changes: $dirty file(s) — commit before closing"
    git status --porcelain | head -5 | sed 's/^/          /'
else
    ok "working tree clean"
fi

# 2 — claimed work items
# count the STATUS column, never free text: an issue TITLED "audit claimed
# sessions" (or a claim sentence containing "unverified" below) used to
# false-match a bare grep over the whole row
issues_out=$(scripts/truth issues 2>/dev/null) || cli_fail
claimed=$(printf '%s\n' "$issues_out" | awk '$2 == "claimed"' | grep -c '^wk-')
if [ "${claimed:-0}" -gt 0 ]; then
    fail "$claimed work item(s) still claimed — 'truth done --claim' or 'truth start --release'"
    printf '%s\n' "$issues_out" | awk '$2 == "claimed"' | head -5 | sed 's/^/          /'
else
    ok "no claimed work items"
fi

# 3 — unverified claims (warn: dispatch verifiers, don't let them pile up)
list_out=$(scripts/truth list --unverified 2>/dev/null) || cli_fail
unver=$(printf '%s\n' "$list_out" | grep -c '^tr-')
if [ "${unver:-0}" -gt 0 ]; then
    warn "$unver claim(s) unverified — dispatch verifiers or expect ready-gate warnings"
else
    ok "no unverified claims"
fi

# 4 — verdict queue (warn + count)
# count queue ROWS (tr- prefixed), not output lines: an empty queue
# prints a one-line "queue empty" message that wc -l misread as debt
queue_out=$(scripts/truth queue 2>/dev/null) || cli_fail
queue=$(printf '%s\n' "$queue_out" | grep -c '^tr-')
if [ "${queue:-0}" -gt 0 ]; then
    warn "verdict queue holds $queue claim(s) — re-verify what your session staled"
else
    ok "verdict queue empty"
fi

# 5/6 — spec + doc gates, when the repo ships them
for gate in spec-health doc-health; do
    if [ -f "scripts/$gate.sh" ]; then
        # exit code is the gates' contract (1 iff failures); parsing the
        # summary line misread spec-health's legitimate "no spec files
        # found" case as a failure
        if bash "scripts/$gate.sh" >/dev/null 2>&1; then
            ok "$gate: passing"
        else
            fail "$gate has failures"
        fi
    else
        ok "$gate: not present (skipped)"
    fi
done

# 7 — project gates (extension point)
if [ -d scripts/session-gates.d ]; then
    found=0
    for g in scripts/session-gates.d/*.sh; do
        [ -e "$g" ] || continue
        found=1
        if bash "$g" >/dev/null 2>&1; then
            ok "project gate $(basename "$g"): passed"
        else
            fail "project gate $(basename "$g") failed — run it directly for detail"
        fi
    done
    [ "$found" -eq 1 ] || ok "session-gates.d present but empty"
else
    ok "no project gates (scripts/session-gates.d/ absent)"
fi

echo
echo "session-close: $fails failure(s), $warns warning(s)"
if [ "$fails" -gt 0 ]; then
    echo "NOT SAFE to end the session — the items above will not survive."
    exit 1
fi
echo "Safe to close."
exit 0
