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

# --- project virtualenv, activated not dispatched ------------------------
# A project-local .venv is put on PATH here so every arm below runs against
# the same interpreter and the same installed jsonschema, whatever the
# operator's shell had. Activation is the whole mechanism: it changes what
# the WORD `python3` resolves to, and the arms keep spelling that word.
#
# THAT SPELLING IS LOAD-BEARING, and the cost of forgetting it is measured.
# Hoisting the interpreter into a variable (PYTHON="$(command -v python3)";
# "$PYTHON" template/scripts/test-truth-core.py) is the obvious tidy-up and
# it silently un-wires this file: gate-reachability.sh reads invocations
# textually, its INVOKER token is the literal bash|sh|zsh|python3?|exec|
# source|./, and a line dispatching through "$PYTHON" carries no such
# token. On 2026-08-17 exactly that edit turned the battery's four python
# arms -- test-truth-core.py, test-truth-v04.py, test-integrations.py and
# instruments/field-consumers.py -- into dark gates: still RUN by this
# script, but invisible to the sweep that certifies they have a schedule,
# which failed 4/10 unreachable. The sweep is fail-safe by design (a
# variable-built path reads as unreachable, never as reached), so the
# alarm was loud and correct. Keep the literal.
if [ -f ".venv/bin/activate" ]; then
  # shellcheck source=/dev/null
  . ".venv/bin/activate"
fi

FAIL=0
ENVBAD=0
say()  { printf '%s\n' "$*" >&2; }
pass() { say "  ok    $1 -- $2"; }
bad()  { say "  FAIL  $1 -- $2"; FAIL=1; }
envr() { say "  ENV   $1 -- $2"; ENVBAD=1; }

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

# --- 3b. retracted figures (the complement of section 3) -----------------
# fact-health sweeps *.md for ledger IDS. This sweeps CODE AND POLICY for
# NUMBERS the project has withdrawn -- a figure restated in a .py string is
# invisible to fact-health twice over, wrong file type and wrong token type.
# Measured 2026-08-18: J-040 recounted the whisper metric, the correction
# reached the journal, the runbook and the dossier, and four LIVE surfaces
# kept quoting the withdrawn pair for a day -- including gates.py's REFUSAL
# text, so the gate argued from a number the project had already withdrawn.
#
# A DARK SWEEP IS THE FAILURE MODE HERE, not a red one: with an empty
# .truth/retracted-figures this exits 0 having examined nothing, and that
# reads exactly like health. So the zero-occurrence case is judged, the
# same way section 3 refuses a zero-citation corpus.
OUT=$(bash scripts/retracted-figures.sh 2>&1); RC=$?
SUM=$(printf '%s' "$OUT" | tail -1)
FIGS=$(printf '%s' "$SUM" | sed -n 's/^retracted-figures: \([0-9]*\) figure.*/\1/p')
if [ "$RC" -ne 0 ]; then
  bad "retracted-figures" "$SUM:
$(printf '%s\n' "$OUT" | grep -E '^  FAIL' | head -3)"
elif [ -z "$SUM" ]; then
  bad "retracted-figures" "the sweep printed no summary (rc=$RC) -- it examined an unknown amount"
elif [ "${FIGS:-0}" -eq 0 ]; then
  pass "retracted-figures" "no figure retracted yet -- nothing to sweep (not a finding)"
else
  pass "retracted-figures" "$SUM"
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

# --- 5b. structural selectors (truthlib/structural.py) -------------------
# Its own root, not an arm of the core suite: structural.py is a leaf that
# imports nothing from truthlib, and its suite returns the favour by importing
# nothing else -- so it stays runnable, and scoreable by mutmut, on its own.
# Same F1 rule as every other arm: 0 tests, or any skip, is a failure.
OUT=$(python3 template/scripts/test-structural.py 2>&1); RC=$?
N=$(printf '%s' "$OUT" | sed -n 's/^Ran \([0-9]*\) test.*/\1/p')
SKIPPED=$(printf '%s' "$OUT" | sed -n 's/.*skipped=\([0-9]*\).*/\1/p')
if [ "$RC" -eq 0 ] && printf '%s' "$OUT" | grep -q "^OK"; then
  if [ "${SKIPPED:-0}" -gt 0 ]; then
    bad "structural suite" "OK but skipped=$SKIPPED (F1 failure rule)"
  elif [ "${N:-0}" -eq 0 ]; then
    bad "structural suite" "ran 0 tests -- the arm is dark (F1 failure rule)"
  else
    pass "structural suite" "$N tests, 0 skipped -- selectors and canonical hashing"
  fi
else
  bad "structural suite" "$(printf '%s' "$OUT" | grep -E '^(FAIL|ERROR):' | head -3)"
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

# --- 7. integration suite (ADR-051, refusals, instruments, hooks) --------
OUT=$(python3 template/scripts/test-integrations.py 2>&1); RC=$?
N=$(printf '%s' "$OUT" | sed -n 's/^Ran \([0-9]*\) test.*/\1/p')
SKIPPED=$(printf '%s' "$OUT" | sed -n 's/.*skipped=\([0-9]*\).*/\1/p')
if [ "$RC" -eq 0 ] && printf '%s' "$OUT" | grep -q "^OK"; then
  if [ "${SKIPPED:-0}" -gt 0 ]; then
    bad "integrations" "OK but skipped=$SKIPPED -- an integration arm was skipped (F1 failure rule)"
  elif [ "${N:-0}" -eq 0 ]; then
    bad "integrations" "ran 0 tests -- the arm is dark (F1 failure rule)"
  else
    pass "integrations" "$N tests, 0 skipped"
  fi
else
  FAILED=$(printf '%s' "$OUT" | grep -cE "^(FAIL|ERROR):" || true)
  bad "integrations" "${FAILED:-?} failing test(s) (rc=$RC):
$(printf '%s' "$OUT" | grep -E '^(FAIL|ERROR):' | head -3)"
fi

# --- 8. field consumers audit (ADR-046) ----------------------------------
OUT=$(python3 instruments/field-consumers.py 2>&1); RC=$?
SUM=$(printf '%s\n' "$OUT" | tail -1)
FAIL_COUNT=$(printf '%s' "$SUM" | sed -n 's/.*-- \([0-9]*\) failure(s).*/\1/p')
if [ "$RC" -ne 0 ] || [ "${FAIL_COUNT:-1}" -ne 0 ]; then
  bad "field-consumers" "$SUM:
$(printf '%s\n' "$OUT" | grep -E '^FAIL' | head -3)"
else
  pass "field-consumers" "$SUM"
fi

# --- 8b. label coupling audit (Tier C) -----------------------------------
# Two modules carrying the same ADRs with no import between them are one
# contract in two implementations -- the F1/F5 drift lesson this repo names
# twice in its own prose and detects nowhere. Literal python3 on purpose:
# see the dark-gate note at the top of this file.
OUT=$(python3 instruments/label-coupling.py 2>&1); RC=$?
SUM=$(printf '%s\n' "$OUT" | tail -1)
if [ "$RC" -ne 0 ]; then
  bad "label-coupling" "$SUM:
$(printf '%s\n' "$OUT" | grep -E '^FAIL' | head -3)"
else
  pass "label-coupling" "$SUM"
fi

# --- 8c. arm-index: every enforced family names what it guards -----------
# wk-db5fce52. This instrument was a DARK GATE for as long as it existed:
# outside the CHECKS globs, invoked by no root, and FAILING (2 families in
# the canary declared no subject) with nobody to read the exit code. A
# check nothing calls is a claim about coverage, not coverage -- section 9
# below states the general form; this arm is one instance of it paying.
#
# Subject-less families are a REPORTED warning for non-enforced species and
# a FAILURE for enforced ones (today: the canary). That asymmetry is the
# instrument's, not this arm's -- read its exit code and print its summary,
# decide nothing here.
OUT=$(python3 instruments/arm-index.py 2>&1); RC=$?
SUM=$(printf '%s\n' "$OUT" | tail -1)
if [ "$RC" -ne 0 ]; then
  bad "arm-index" "$SUM:
$(printf '%s\n' "$OUT" | grep -E '^FAIL' | head -3)"
else
  pass "arm-index" "$SUM"
fi

# --- 9. reachability sweep ----------------------------------------------
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

# --- 10. reproduction sweep (Reproduce-on-Read, step 2.3) ----------------
# The direct measurement, replacing the proxy. `invalidate-scan` asks a
# SYNTACTIC question -- did git touch a watched path -- and on this ledger
# it answered yes 1971 times while the evidence actually changed 70 times
# (PPV 3.6%). `reproduce` asks the semantic one: does the recorded capsule
# still produce its recorded output, here, now? Measured cost: ~8ms per
# capsule, 0.53s for the whole live ledger -- so the proxy was an
# optimisation for an operation that is free at this scale.
#
# It files NOTHING on success. That is the point of on-read verification:
# a green sweep leaves no record, because there is no stored state to
# advance.
#
# Exit 8 blocks as hard as exit 7. A sweep that examined ZERO claims has
# not passed (ADR-042 rule 2) -- an empty or unreadable ledger would
# otherwise sail through the gate reporting success by measuring nothing,
# which is the F1 failure this battery exists to refuse.
OUT=$(python3 template/scripts/truth reproduce 2>&1); RC=$?
SUM=$(printf '%s\n' "$OUT" | grep -E "^reproduce: " | tail -1)
case "$RC" in
  0) if [ -z "$SUM" ]; then
       bad "reproduce" "the sweep printed no summary (rc=0) -- it examined an unknown amount"
     else
       pass "reproduce" "$SUM"
     fi ;;
  7) bad "reproduce" "a live claim's recorded capsule no longer reproduces:
$(printf '%s\n' "$OUT" | grep -E 'capsule-stale|unexecutable' | head -4)
        Judge it -- 'truth verdict <id> diverge' or an agree with
        --refresh-evidence (ADR-051). Do NOT re-file blind." ;;
  8) bad "reproduce" "examined 0 live claims (exit 8) -- a sweep that measured nothing is a failure, never a pass (ADR-042 rule 2)" ;;
  *) bad "reproduce" "unexpected exit $RC -- the verb's contract is 0/7/8:
$(printf '%s\n' "$OUT" | tail -3)" ;;
esac

# --- 11. battery meta-gate, scoped ---------------------------------------
# scripts/test-release-battery.sh proves each arm ABOVE can go red. It
# cannot ride every push -- fourteen arms, a dozen battery runs, minutes --
# and it cannot run unguarded from inside the battery at all, because that
# recurses (the first cut of this arm did, in 2026-08, and cost minutes
# before the guard).
#
# Both are solved here. The arm fires only when the battery, its gate, or
# the hook that carries it moved -- an unchanged battery cannot have
# regressed, which is the canary's own argument. TRUTH_BATTERY_NO_META
# tells the nested batteries not to re-enter; it is set by THIS LINE and
# nowhere else, and is not a skip flag for operators.
#
# Restored 2026-08-21 after `32022c6` swept both the gate and this arm
# away with the bash scaffolding. For six days the mechanism guarding
# every other gate was itself unguarded -- see the header of the gate.
if [ -n "${TRUTH_BATTERY_NO_META:-}" ]; then
  say "  skip  battery meta-gate -- re-entrant run under the outer battery"
elif touches '^scripts/(release-battery|test-release-battery|gate-reachability)\.sh$|^\.githooks/pre-push$'; then
  OUT=$(env TRUTH_BATTERY_NO_META=1 bash scripts/test-release-battery.sh 2>&1); RC=$?
  SUM=$(printf '%s\n' "$OUT" | grep -E "^test-release-battery: " | tail -1)
  CAUGHT=$(printf '%s' "$SUM" | sed -n 's/^test-release-battery: \([0-9]*\) caught.*/\1/p')
  if [ "$RC" != 0 ]; then
    bad "battery meta-gate" "$(printf '%s\n' "$OUT" | grep -E '^  MISSED' | head -3)"
  elif [ "${CAUGHT:-0}" -eq 0 ]; then
    bad "battery meta-gate" "reported success having run 0 arms"
  else
    pass "battery meta-gate" "${CAUGHT} arm(s) proven able to fail"
  fi
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
