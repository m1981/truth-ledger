#!/usr/bin/env bash
# release-battery: the content-judging checks, run at the push boundary.
# META-REPO ONLY — untemplated like fact-health and the whisper (ADR-003
# rule 2: this encodes this repo's release policy, not the machinery).
#
# WHY THIS EXISTS. A 2026-08-01 coverage audit found that of ten
# mechanisms, only three fired on their own: the archive freeze, the
# ledger gate, and invalidate-scan. The canary, the core suite, the
# version lockstep, fact-health and doc-health were all MANUAL — and the
# core suite was failing at HEAD with nobody aware, because nothing ran
# it. Detection that runs on nobody's schedule runs after the incident.
#
# WHY PUSH AND NOT COMMIT. These checks cost 1-60s; at pre-commit they
# would tax every edit and train `--no-verify`, which is worse than
# manual because it disables the fast gates too. Push is the boundary
# where staleness starts shipping to consumers (copier resolves from
# tags), and it is a boundary this operator provably crosses: the tag
# check already lives here.
#
# THE ONE RULE WORTH KEEPING. Every arm reports WHAT IT EXAMINED, not
# just pass/fail. A check that examined nothing is a FAILURE, never a
# pass — the same F1 audit law that says a sensor which cannot run must
# scream. Two gates in this repo (ADR-036 citations, ADR-037 generated
# paths) reported "clean" for weeks while checking zero files.
#
# NO SKIP FLAG, deliberately. `git push --no-verify` is the honest
# emergency exit and it is loud in the reflog. A second, softer bypass
# would be this hook teaching its own workaround (the ADR-011 lesson).
#
# Exit codes follow check-truth.sh: 0 ok / 1 governance / 2 environment.
set -u
# A PUSH GATE MUST NEVER BLOCK ON INPUT. It runs from pre-push, where a
# terminal is attached, and anything downstream that consults isatty() will
# take its interactive branch and wait forever. Measured: the canary's
# ADR-011 arms ran `TRUTH_HUMAN=1 truth verdict ... retracted` without
# redirecting stdin, so from a terminal the CLI stopped at
# `input("type <id> to confirm")` -- the operator pressed Enter twenty
# times and the battery crawled. Those three call sites are fixed at
# source; this line is the structural backstop, so the NEXT one cannot
# hang a push.
exec </dev/null
cd "$(dirname "$0")/.."

FAIL=0
ENVBAD=0
say()  { printf '%s\n' "$*" >&2; }
pass() { say "  ok    $1 -- $2"; }
bad()  { say "  FAIL  $1 -- $2"; FAIL=1; }
envr() { say "  ENV   $1 -- $2"; ENVBAD=1; }

# gate_arm <label> <summary-prefix> <command...>
# Runs one of this repo's regression SUITES and judges it by the line it
# prints about itself: "<prefix>: N caught, M missed". The count is the
# point, not the exit code -- a suite that dies before its summary, or
# reports 0 caught, examined nothing and must FAIL (the header rule). The
# suites were added 2026-08-01 and invoked by NOTHING until 2026-08-02;
# three audits found 29 armed-looking arms that no schedule reached.
gate_arm() {
  local label prefix out rc sum caught missed
  label="$1"; prefix="$2"; shift 2
  out=$("$@" 2>&1); rc=$?
  sum=$(printf '%s\n' "$out" | grep -E "^${prefix}: [0-9]+ caught, [0-9]+ missed" | tail -1)
  caught=$(printf '%s' "$sum" | sed -n 's/.*: \([0-9]*\) caught.*/\1/p')
  missed=$(printf '%s' "$sum" | sed -n 's/.*caught, \([0-9]*\) missed.*/\1/p')
  if [ -z "$sum" ]; then
    bad "$label" "no '$prefix: N caught, M missed' summary (rc=$rc) -- the suite
        died before reporting, so it examined an unknown amount:
$(printf '%s\n' "$out" | tail -3)"
  elif [ "${missed:-1}" -ne 0 ] || [ "$rc" -ne 0 ]; then
    bad "$label" "$sum (rc=$rc)
$(printf '%s\n' "$out" | grep -E '^ *MISSED' | head -3)"
  elif [ "${caught:-0}" -eq 0 ]; then
    bad "$label" "reported 0 caught -- the suite ran and examined nothing"
  else
    pass "$label" "$caught arms caught, 0 missed"
  fi
}

command -v python3 >/dev/null 2>&1 || { say "release-battery: no python3"; exit 2; }

# --- scope: what did this push actually change? -------------------------
# TRUTH_BATTERY_SCOPE is set by the pre-push hook from the pushed range,
# or the literal ALL when the range could not be determined. Unknown
# scope always means MORE checking, never less.
SCOPE="${TRUTH_BATTERY_SCOPE:-ALL}"
touches() {  # touches <regex> -> 0 when scope is ALL or matches
  [ "$SCOPE" = "ALL" ] && return 0
  printf '%s\n' "$SCOPE" | grep -qE "$1"
}

say "release-battery: content checks at the push boundary"

# --- 1. schema half of the contract (the F1 arm) ------------------------
# The core suite fails loudly when jsonschema is absent, by design: the
# JSON Schema half of the record contract is then UNCHECKED. Surface that
# here as an ENVIRONMENT problem with both documented remedies, so the
# operator resolves it deliberately. Auto-waiving it in a hook would be
# this script manufacturing exactly the dark arm it exists to prevent.
JSOK=0; python3 -c "import jsonschema" >/dev/null 2>&1 && JSOK=1
if [ "$JSOK" = 0 ] \
   && [ -z "${TRUTH_ALLOW_NO_JSONSCHEMA:-}" ]; then
  envr "jsonschema" "not importable, so the schema half of the record contract is UNCHECKED.
        This machine may already have a pip-less wheel lib -- check .local/machine.md
        before reaching for the waiver; a PYTHONPATH export is the usual answer here.
        Otherwise:  python3 -m pip install jsonschema
        Or waive deliberately:  export TRUTH_ALLOW_NO_JSONSCHEMA=1"
fi

# --- 2. cross-surface version lockstep (ADR-026) ------------------------
# Skip-aware (R8): unittest prints "OK (skipped=k)" -- which grep ^OK
# happily matches -- and "Ran N" counts the skipped tests, so a pinned
# doc renamed out from under _assert_doc_pin would report "N surfaces
# agree" having examined nothing. Any skip here IS the arm examining
# less than it claims: a FAILURE per the header rule.
OUT=$(python3 template/scripts/test-truth-core.py TestCrossSurfaceVersions 2>&1)
N=$(printf '%s' "$OUT" | sed -n 's/^Ran \([0-9]*\) test.*/\1/p')
SKIPPED=$(printf '%s' "$OUT" | sed -n 's/.*skipped=\([0-9]*\).*/\1/p')
if printf '%s' "$OUT" | grep -q "^OK"; then
  if [ "${SKIPPED:-0}" -gt 0 ]; then
    bad "version lockstep" "OK but skipped=$SKIPPED -- a pinned surface was skipped, not examined"
  else
    [ "${N:-0}" -gt 0 ] && pass "version lockstep" "$N pinned surfaces agree" \
                        || bad  "version lockstep" "ran 0 tests -- the arm is dark"
  fi
else
  bad "version lockstep" "a pinned version surface disagrees with the CLI:
$(printf '%s' "$OUT" | grep -E '^(FAIL|AssertionError)' | head -3)"
fi

# --- 3. citation tripwire (this repo's prose corpus) --------------------
OUT=$(bash scripts/fact-health.sh 2>&1); RC=$?
SUM=$(printf '%s' "$OUT" | tail -1)
CITED=$(printf '%s' "$SUM" | sed -n 's/.*, \([0-9]*\) citation.*/\1/p')
if [ "$RC" -ne 0 ]; then
  bad "fact-health" "$SUM"
elif [ "${CITED:-0}" -eq 0 ]; then
  bad "fact-health" "swept 0 citations -- the corpus globs match nothing (dark sweep)"
else
  pass "fact-health" "$SUM"
fi

# --- 4. doc hygiene -----------------------------------------------------
# NOTE a known blind spot, recorded rather than hidden: doc-health runs
# rooted at template/, so the meta-repo's own docs/ tree is outside its
# view. It is run here for the template corpus it CAN see.
if (cd template && bash scripts/doc-health.sh >/dev/null 2>&1); then
  pass "doc-health" "template corpus clean (blind to the meta-repo docs/ tree)"
else
  bad "doc-health" "broken links or forbidden names under template/"
fi

# --- 5. core + v04 suites ----------------------------------------------
OUT=$(python3 template/scripts/test-truth-core.py 2>&1)
N=$(printf '%s' "$OUT" | sed -n 's/^Ran \([0-9]*\) test.*/\1/p')
SKIPPED=$(printf '%s' "$OUT" | sed -n 's/.*skipped=\([0-9]*\).*/\1/p')
if printf '%s' "$OUT" | grep -qE "^(OK|OK \()"; then
  # Skip-aware (R8): "OK (skipped=k)" matched the old grep and passed as
  # fully examined. The ONE tolerated baseline is the three
  # @skipUnless(JSONSCHEMA) conformance tests when jsonschema is absent:
  # that absence is already surfaced by the ENV arm above or deliberately
  # waived, so those skips are a disclosed consequence, not silent
  # shrinkage -- and the pass line still names them. Anything beyond
  # that baseline (or any skip with jsonschema present) is a FAILURE.
  if [ "${SKIPPED:-0}" -eq 0 ]; then
    pass "core suite" "${N:-?} tests, 0 skipped"
  elif [ "$JSOK" = 0 ] && [ "$SKIPPED" -le 3 ]; then
    pass "core suite" "${N:-?} tests; $SKIPPED jsonschema-gated skip(s), disclosed by the ENV/waiver lane"
  else
    bad "core suite" "OK but skipped=$SKIPPED -- examined less than it claims"
  fi
else
  FAILED=$(printf '%s' "$OUT" | grep -cE "^(FAIL|ERROR):" || true)
  if [ "${TRUTH_ALLOW_NO_JSONSCHEMA:-}" = "" ] && [ "$ENVBAD" = "1" ] && [ "$FAILED" = "1" ] \
     && printf '%s' "$OUT" | grep -q "jsonschema not installed"; then
    say "  (core suite's single failure is the jsonschema arm reported above)"
  else
    bad "core suite" "${FAILED:-?} failing test(s):
$(printf '%s' "$OUT" | grep -E '^(FAIL|ERROR):' | head -3)"
  fi
fi
OUT=$(python3 template/scripts/test-truth-v04.py 2>&1)
if printf '%s' "$OUT" | grep -q "^OK" \
   && ! printf '%s' "$OUT" | grep -q "skipped="; then
  pass "v04 suite" "fold/duplicate invariants"
else
  bad "v04 suite" "fold invariant regression (or a skipped arm)"
fi

# --- 6. canary, scoped ---------------------------------------------------
# 45s: the one arm that cannot ride every push. Its 112 seeded faults pin
# CLI BEHAVIOUR, so it can only regress when the CLI or the suite itself
# moves. Run the check whose inputs changed -- not a speed hack: an
# unchanged input cannot have regressed.
if touches '^template/scripts/(truth|truth-canary\.sh)$|^template/truthlib/|^template/\.truth/'; then
  OUT=$(cd template/scripts && bash truth-canary.sh 2>&1)
  CAUGHT=$(printf '%s' "$OUT" | sed -n 's/^canary result: \([0-9]*\) caught.*/\1/p')
  if printf '%s' "$OUT" | grep -q "ALL CANARIES CAUGHT"; then
    [ "${CAUGHT:-0}" -gt 0 ] && pass "canary" "${CAUGHT} seeded faults caught" \
                             || bad  "canary" "reported success having run 0 arms"
  else
    bad "canary" "$(printf '%s' "$OUT" | grep -E '^  MISSED' | head -3)"
  fi
else
  say "  skip  canary -- this push touches neither the CLI nor the suite"
fi

# --- 7. the regression suites nothing used to invoke ---------------------
# Wired 2026-08-02. These four suites (10 + 3 + 16 + 5 = 34 arms) were
# committed as coverage and reached by NO schedule: the fact-health,
# session-digest and instruments gates were orphaned by the migration that
# created them -- and six proven canary assertions were MOVED into the
# instruments gate, so automated coverage DROPPED while the log claimed it
# rose. The whisper gate had been orphaned since it was written.
#
# UNCONDITIONAL, on a measurement rather than a hunch: together they cost
# 8.0s wall here (1.7 + 0.6 + 5.1 + 0.6), well inside the 15s budget for
# riding every push, and none of them is a pure function of the CLI the
# way the 45s canary is -- fact-health reads the prose corpus, the digest
# reads the ledger, the instruments read both, and the whisper gate reads
# a harness config no `touches` pattern would predict. Scoping them would
# be guessing at their inputs; running them is cheaper than guessing.
gate_arm "fact-health gate"    "fact-health gate"        bash scripts/test-fact-health.sh
gate_arm "session-digest gate" "session-digest gate"     bash scripts/test-session-digest.sh
gate_arm "instruments gate"    "test-instruments result" bash scripts/test-instruments.sh
gate_arm "whisper gate"        "whisper-hook gate"       bash scripts/test-whisper-hook.sh

# --- 8. reachability sweep ----------------------------------------------
# The general form of the defect above: a check no root invokes is a claim
# about coverage, not coverage. This arm is also how gate-reachability.sh
# itself gets a schedule -- it reports on itself, so leaving it orphaned
# would be the joke writing itself.
OUT=$(bash scripts/gate-reachability.sh 2>&1); RC=$?
SUM=$(printf '%s\n' "$OUT" | grep -E "^gate-reachability: examined [0-9]+ check" | tail -1)
EXAM=$(printf '%s' "$SUM" | sed -n 's/.*examined \([0-9]*\) check.*/\1/p')
if [ -z "$SUM" ]; then
  bad "reachability" "the sweep printed no summary (rc=$RC) -- it examined an unknown amount:
$(printf '%s\n' "$OUT" | tail -3)"
elif [ "$RC" -ne 0 ]; then
  bad "reachability" "$SUM
$(printf '%s\n' "$OUT" | grep -E '^  (FAIL|ADVISORY)' | head -4)"
elif [ "${EXAM:-0}" -eq 0 ]; then
  bad "reachability" "examined 0 checks -- the enumeration patterns match nothing (dark sweep)"
else
  pass "reachability" "$EXAM checks examined, every one reached by a root"
fi

# --- 9. the battery's own mutation gate, scoped -------------------------
# scripts/test-release-battery.sh proves each arm ABOVE can go red, and it
# was itself unreachable until 2026-08-02. It cannot ride every push (12
# arms, a dozen battery runs and two canaries: 6m19s measured here) and it
# cannot run unguarded from inside the battery at all -- that recurses
# (the first cut of this arm did, and cost minutes before the guard).
# Both are solved here: the
# arm fires only when the battery, its gate, or the hook that carries it
# moved (an unchanged battery cannot have regressed -- the canary's own
# argument), and TRUTH_BATTERY_NO_META tells the nested batteries not to
# re-enter. The guard is not a skip flag for operators: it is set by this
# line and nowhere else.
if [ -n "${TRUTH_BATTERY_NO_META:-}" ]; then
  say "  skip  battery meta-gate -- re-entrant run under the outer battery"
elif touches '^scripts/(release-battery|test-release-battery|gate-reachability)\.sh$|^\.githooks/pre-push$'; then
  gate_arm "battery meta-gate" "test-release-battery" \
    env TRUTH_BATTERY_NO_META=1 bash scripts/test-release-battery.sh
else
  say "  skip  battery meta-gate -- this push touches neither the battery nor its hook"
fi

# --- verdict -------------------------------------------------------------
if [ "$FAIL" = "1" ]; then
  say ""
  say "release-battery: BLOCKED. These checks were manual until 2026-08-01;"
  say "  a failure here is drift that would otherwise have shipped."
  say "  Emergency exit is 'git push --no-verify' -- loud, and in the reflog."
  exit 1
fi
if [ "$ENVBAD" = "1" ]; then
  say ""
  say "release-battery: BLOCKED on an environment problem (exit 2), not on"
  say "  your changes. Resolve the remedy above once and it stays resolved."
  exit 2
fi
say "release-battery: all arms green"
exit 0
