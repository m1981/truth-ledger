#!/usr/bin/env bash
# Regression gate for scripts/release-battery.sh and the pre-push wiring.
# META-REPO ONLY: it guards untemplated consumer machinery, which by
# definition has no home in the template canary.
#
# WHY THIS FILE IS BASH, AND WHY IT CAME BACK (2026-08-21)
# -------------------------------------------------------
# `32022c6` (2026-08-15) deleted five bash test scripts and replaced them
# with one stdlib runner, template/scripts/test-integrations.py. Its own
# message lists what the replacement covers: CLI contracts, refusals,
# ADR-051 refresh, whisper hook, session digest, Tier C instruments,
# doc/session health. Four of the five had a successor. THIS one did not
# -- the battery's gate was swept along with the scaffolding rather than
# retired on its merits, and for six days the mechanism that guards every
# other gate was the only one unguarded. AGENTS.md recorded the gap and
# even recorded it wrongly ("its six arms" -- there were twelve), which is
# how invisible it had become.
#
# So this is not a reversal of `32022c6`; it is the part of it that never
# happened. Bash rather than a class in test-integrations.py, for two
# reasons, both measured:
#
#   COST. Every arm here runs the battery. Twelve arms cost 6m19s when
#   this file was first written; a scoped run costs ~18s today. Inside
#   test-integrations.py that price would be paid on EVERY push, because
#   the battery runs that suite unconditionally. Here it is paid only when
#   the battery itself moved -- see the meta-gate in release-battery.sh
#   section 11, and ARM 14 below, which proves that conditionality.
#
#   MEDIUM. The arms mutate shell gates with `sed` and execute the result.
#   That is bash's native register; a Python wrapper would add a layer
#   between the mutation and the thing mutated without adding an assertion.
#
#   BONUS, not a reason: `scripts/test-*.sh` is already a CHECKS glob in
#   gate-reachability.sh, so restoring the name makes this file a swept
#   check again with no policy edit.
#
# Each arm below must be verified to FAIL against a deliberately mutated
# battery before it is credited. An arm that has never been seen red is an
# arm that cannot go red -- this repo shipped exactly that defect twice:
# a canary arm whose grep matched doctor's OK line as happily as its WARN
# line (2026-08-01), and ARM 5 of this very file, which as first written
# asked whether a healthy battery printed both FAIL and green.
#
# RED-VERIFICATION STATUS, 2026-08-21 -- who has actually seen what fail.
# The doctrine in AGENTS.md is "do not add an arm you have not seen fail",
# and this is the file that enforces it, so its own compliance is stated
# rather than assumed:
#
#   ARMS 4, 5, 15   SEEN RED IN THIS SESSION. 4 and 5 reported MISSED in
#                   real runs (4 was probing the wrong interpreter, 5 was
#                   reading a stale RC from a subshell -- see run() below)
#                   and were fixed; 15's grep was broken by mutating
#                   truth-canary.sh and observed to fail.
#   ARMS 10, 11, 12 RED-CAPABILITY VERIFIED. These are new (structural,
#                   integrations) or re-pointed (12, from the removed
#                   session-digest gate to the canary's zero-examined
#                   contract). Each was checked by BREAKING the battery's
#                   guarantee -- turning the rejecting `bad` into a `pass`
#                   -- and confirming the arm's assertion then does not
#                   hold, i.e. it would report MISSED.
#   ARMS 1-3, 6-9,  RESTORED VERBATIM from the file 32022c6 deleted. Their
#   13, 14          red-verification is the ORIGINAL AUTHOR'S, recorded in
#                   that file's header, not this session's. That is
#                   second-hand evidence and is labelled as such.
#
# Closing the second-hand half needs an arm selector, because one
# red-check currently costs a full ~10min run -- a rule nobody can afford
# to re-run is a rule that decays into a norm. Filed rather than smuggled
# in here.
set -u

# Every arm that mutates writes scripts/.armN-*.sh and removes it on the
# next line. An interrupted run skips that line and leaves mutated copies
# of the release gates in scripts/ -- dotfiles, so they read as noise
# rather than as damage. ARM 11 plants a NON-dotfile orphan as well, and
# an orphan check left in scripts/ is exactly what gate-reachability.sh
# fails on, so the debris would resurface later as a confusing gate
# failure rather than as leftover test state. Hence: rollback on EVERY
# exit path, not just the happy one.
cleanup_mutants() {
  local m found=0
  for m in scripts/.arm*.sh scripts/.skip-stub.py scripts/test-zz-dark-arm.sh; do
    [ -e "$m" ] || continue
    rm -f "$m"; found=1
  done
  [ "$found" = 1 ] && printf '  (cleaned leftover mutants)\n' >&2
  return 0
}
trap cleanup_mutants EXIT INT TERM
cleanup_mutants

PASS=0; FAIL=0
ok()   { PASS=$((PASS+1)); printf '  CAUGHT: %s\n' "$*"; }
miss() { FAIL=$((FAIL+1)); printf '  MISSED: %s\n' "$*"; }

# BATTERY is overridable so the arms can be pointed at a deliberately
# mutated copy -- that is how each one is proven capable of failing.
B="${BATTERY:-scripts/release-battery.sh}"
SCOPED="docs/x.md"            # a scope that touches neither CLI nor suite

# EVERY battery this file runs must skip the meta-gate, or an arm whose
# scope matches `scripts/release-battery.sh` re-enters this very suite.
# Invoked AS a gate that is automatic -- the battery exports the guard --
# but a HAND run has it unset, and ARM 3 (scope ALL) matches everything.
# Measured before this line existed: a hand run nested one full 14-arm
# suite inside ARM 3 and doubled the wall clock. ARM 14 is the deliberate
# exception and unsets it per-invocation to exercise BOTH branches.
export TRUTH_BATTERY_NO_META=1

mutate() {  # mutate <sedscript> <dest> -> 0 when the copy really changed
  sed "$1" "$B" > "$2"
  if cmp -s "$B" "$2"; then
    rm -f "$2"
    return 1   # the pattern drifted: an unmutated copy would PASS blindly
  fi
}

run() {  # run <script> [env assignments...] -> sets OUT and RC as GLOBALS
  # CALL IT BARE: `run "$B"`, then read "$OUT" and "$RC".
  # NEVER `O=$(run "$B")`. The original of this file had no such helper --
  # every arm inlined its own `OUT=$(...); RC=$?` -- and adding one
  # reintroduced the exact defect this file exists to catch: called inside
  # a command substitution, the function body runs in a SUBSHELL, so its
  # `RC=$?` never reaches the caller and the arm silently judges the
  # PREVIOUS arm's exit code. ARM 5 reported MISSED for that reason
  # (2026-08-21) and ARM 13's exit assertion was reading stale state while
  # still printing CAUGHT -- an arm that passes on the wrong evidence.
  local s="$1"; shift
  OUT=$(env TRUTH_ALLOW_NO_JSONSCHEMA=1 TRUTH_BATTERY_SCOPE="$SCOPED" "$@" bash "$s" 2>&1)
  RC=$?
}

# --- scope arms ----------------------------------------------------------

echo "ARM 1: an out-of-scope push must SKIP the 45s canary"
run "$B"; O="$OUT"
if printf '%s' "$O" | grep -q "skip  canary"; then
  ok "canary skipped when neither the CLI nor the suite moved"
else
  miss "canary did not skip on an out-of-scope push -- every push now costs 45s"
fi

# ARMS 2 and 3 judge the SCOPE DECISION, not the canary. Running the real
# canary to learn whether the battery decided to run it costs 45s per arm
# and measures the wrong thing -- so the invocation is stubbed with a
# valid summary line. Measured: this cut the suite from >10min to ~4min.
# The canary's own correctness is the canary's business (template/), and
# ARM 12 below covers the battery's reading of its summary.
CANARY_STUB='s|OUT=$(cd template/scripts \&\& bash truth-canary\.sh 2>&1)|OUT=$(printf "canary result: 7 caught, 0 missed\\\\nALL CANARIES CAUGHT\\\\n")|'

echo "ARM 2: a push touching the CLI must RUN the canary"
MUT="scripts/.arm2-scope.sh"
if mutate "$CANARY_STUB" "$MUT"; then
  O=$(env TRUTH_ALLOW_NO_JSONSCHEMA=1 TRUTH_BATTERY_SCOPE="template/truthlib/kernel.py" \
      bash "$MUT" 2>&1)
  rm -f "$MUT"
  if printf '%s' "$O" | grep -qE "ok    canary|FAIL  canary"; then
    ok "canary runs when the CLI moved"
  else
    miss "canary skipped on a CLI push -- seeded-fault coverage is dark exactly when it matters"
  fi
else
  miss "ARM 2 could not stub the canary invocation -- the pattern drifted, so this arm was checking nothing"
fi

echo "ARM 3: unknown scope must widen to ALL, never narrow"
MUT="scripts/.arm3-scope.sh"
if mutate "$CANARY_STUB" "$MUT"; then
  O=$(env TRUTH_ALLOW_NO_JSONSCHEMA=1 TRUTH_BATTERY_SCOPE="ALL" bash "$MUT" 2>&1)
  rm -f "$MUT"
  if printf '%s' "$O" | grep -qE "ok    canary|FAIL  canary"; then
    ok "scope ALL runs the canary -- an unresolvable range means MORE checking"
  else
    miss "scope ALL skipped the canary -- unknown scope narrowed instead of widening"
  fi
else
  miss "ARM 3 could not stub the canary invocation -- the pattern drifted, so this arm was checking nothing"
fi

# --- environment vs governance ------------------------------------------

echo "ARM 4: a missing jsonschema is named as an ENVIRONMENT problem, not swallowed"
# NB: this script runs under `set -u` only. Do NOT `set -e` -- arms 4, 5
# and others deliberately run a battery that exits non-zero, and errexit
# would kill the suite mid-arm (it silently did, until 2026-08-01).
#
# REWRITTEN 2026-08-21, because as inherited this arm was UNEXERCISABLE and
# reported MISSED for a reason that was nobody's defect. Two drifts had
# accumulated under it:
#
#   1. `961d698`-era change put a project-local .venv on PATH inside the
#      battery, so the battery's `python3` is the venv's and DOES import
#      jsonschema. The arm probed the OUTER interpreter, which does not.
#      It was asking about a different python than the one under test.
#   2. The old assertion demanded exit 2. That holds only when the missing
#      module is the battery's ONLY problem -- the verdict checks FAIL
#      before ENVBAD -- and a jsonschema absent by design also fails the
#      core suite. Exit 2 is therefore not reachable from a bare removal.
#
# What is still guaranteed, and what an operator actually needs, is the
# NAMED environment diagnosis with both remedies. That is what this arm
# now asserts, against a battery mutated to skip the venv so the branch is
# reachable at all. The exit-code half is deliberately narrowed to
# non-zero; narrowing it in the open beats asserting something the code no
# longer promises.
MUT="scripts/.arm4-novenv.sh"
if mutate 's|if \[ -f "\.venv/bin/activate" \]; then|if false; then|' "$MUT"; then
  O=$(env -u TRUTH_ALLOW_NO_JSONSCHEMA -u VIRTUAL_ENV TRUTH_BATTERY_SCOPE="$SCOPED" \
      TRUTH_BATTERY_NO_META=1 bash "$MUT" 2>&1); RC=$?
  rm -f "$MUT"
  if python3 -c "import jsonschema" >/dev/null 2>&1; then
    echo "  (skipped: the bare interpreter has jsonschema, so the branch cannot be reached)"
  elif [ "$RC" != "0" ] && printf '%s' "$O" | grep -q "ENV   jsonschema" \
       && printf '%s' "$O" | grep -q "TRUTH_ALLOW_NO_JSONSCHEMA=1"; then
    ok "a missing jsonschema is named as an environment problem, with both remedies, and blocks"
  else
    miss "missing jsonschema was not named as an environment problem (rc=$RC) -- the schema half of the contract would go unchecked in silence"
  fi
else
  miss "ARM 4 could not disable the venv activation -- the pattern drifted, so this arm was checking nothing"
fi

echo "ARM 5: a battery with ANY failing arm must not report green, and must exit 1"
# This arm was VACUOUS as first written (2026-08-01): it asked whether a
# healthy battery printed both FAIL and green, which a healthy battery
# never does, so it could only ever pass. It now MANUFACTURES a failing
# arm, which is the only way to test the exclusion it claims to test.
MUT="scripts/.arm5-forced-fail.sh"
if mutate 's|^say "release-battery: content checks at the push boundary"|&\nbad "synthetic" "deliberately failing arm injected by ARM 5"|' "$MUT"; then
  run "$MUT"; O="$OUT"
  rm -f "$MUT"
  if printf '%s' "$O" | grep -q "all arms green"; then
    miss "battery printed 'all arms green' while an arm reported FAIL"
  elif [ "$RC" != "1" ]; then
    miss "battery exited $RC with a failing arm -- a governance failure must exit 1"
  else
    ok "a failing arm suppresses the green verdict and exits 1"
  fi
else
  miss "ARM 5 could not inject a failing arm -- the banner line drifted, so this arm was checking nothing"
fi

echo "ARM 6: the pre-push hook keeps its tag-check arm ahead of the battery"
if grep -q "tag-check" .githooks/pre-push && grep -q "release-battery.sh" .githooks/pre-push; then
  ok "pre-push carries both the tag check and the battery"
else
  miss "pre-push lost an arm -- release coherence or content checking is dark"
fi

# --- the skip-awareness arms --------------------------------------------
# "OK (skipped=k)" is what a suite prints when it examined less than it
# claims, and until 2026-08-01 the battery read it as a pass. These arms
# feed the battery SYNTHETIC suite output through a stub, because the
# alternative is mutating the suites themselves, which live in template/
# and answer to the canary.
STUB="scripts/.skip-stub.py"
cat > "$STUB" <<'PY'
#!/usr/bin/env python3
"""Synthetic suite output for the skip-awareness arms: prints whatever
SUITE_OUT holds and exits 0, exactly as unittest does on a green run."""
import os
print(os.environ.get("SUITE_OUT", ""))
PY

skip_arm() {  # skip_arm <n> <sedscript> <badlabel> <oklabel> <skipout> <cleanout> <desc>
  local n="$1" sedscript="$2" badlabel="$3" oklabel="$4"
  local skipout="$5" cleanout="$6" desc="$7"
  local MUT="scripts/.arm${n}-skip.sh"
  if mutate "$sedscript" "$MUT"; then
    local O1 O2 R1
    O1=$(env TRUTH_ALLOW_NO_JSONSCHEMA=1 TRUTH_BATTERY_SCOPE="$SCOPED" \
         SUITE_OUT="$skipout" bash "$MUT" 2>&1); R1=$?
    O2=$(env TRUTH_ALLOW_NO_JSONSCHEMA=1 TRUTH_BATTERY_SCOPE="$SCOPED" \
         SUITE_OUT="$cleanout" bash "$MUT" 2>&1)
    rm -f "$MUT"
    if printf '%s' "$O1" | grep -q "FAIL  $badlabel" && [ "$R1" != "0" ] \
       && printf '%s' "$O2" | grep -q "ok    $oklabel"; then
      ok "$desc"
    else
      miss "the $badlabel arm accepted a skipped run (rc=$R1) -- $desc did not hold"
    fi
  else
    miss "ARM $n could not mutate the $badlabel invocation -- the pattern drifted, so this arm was checking nothing"
  fi
}

echo "ARM 7: a SKIPPED pinned surface must fail the version-lockstep arm"
skip_arm 7 's|python3 template/scripts/test-truth-core\.py TestCrossSurfaceVersions|python3 scripts/.skip-stub.py|' \
  "version lockstep" "version lockstep" \
  $'Ran 7 tests in 0.010s\n\nOK (skipped=1)' $'Ran 7 tests in 0.010s\n\nOK' \
  "a skipped pinned surface fails lockstep, and the same surfaces pass when none is skipped"

echo "ARM 8: ANY skip in the core suite must fail"
skip_arm 8 's|python3 template/scripts/test-truth-core\.py 2>&1|python3 scripts/.skip-stub.py 2>\&1|' \
  "core suite" "core suite" \
  $'Ran 531 tests in 1.000s\n\nOK (skipped=1)' $'Ran 531 tests in 1.000s\n\nOK' \
  "a skipped core test fails the arm, and an unskipped run still passes"

echo "ARM 9: ANY skip in the v04 suite must fail (no baseline there)"
skip_arm 9 's|python3 template/scripts/test-truth-v04\.py|python3 scripts/.skip-stub.py|' \
  "v04 suite" "v04 suite" \
  $'Ran 13 tests in 0.100s\n\nOK (skipped=1)' $'Ran 13 tests in 0.100s\n\nOK' \
  "a skipped fold invariant fails the v04 arm, and an unskipped run still passes"

echo "ARM 10: ANY skip in the structural suite must fail"
skip_arm 10 's|python3 template/scripts/test-structural\.py|python3 scripts/.skip-stub.py|' \
  "structural suite" "structural suite" \
  $'Ran 116 tests in 0.500s\n\nOK (skipped=1)' $'Ran 116 tests in 0.500s\n\nOK' \
  "a skipped selector test fails the structural arm, and an unskipped run still passes"

echo "ARM 11: ANY skip in the integration suite must fail"
skip_arm 11 's|python3 template/scripts/test-integrations\.py|python3 scripts/.skip-stub.py|' \
  "integrations" "integrations" \
  $'Ran 28 tests in 1.000s\n\nOK (skipped=1)' $'Ran 28 tests in 1.000s\n\nOK' \
  "a skipped integration arm fails the arm, and an unskipped run still passes"
rm -f "$STUB"

echo "ARM 12: a suite reporting ZERO examined must FAIL, not pass quietly"
# Re-pointed 2026-08-21. The original judged the session-digest gate,
# which `32022c6` removed from the battery; the canary arm carries the
# same contract today ("reported success having run 0 arms"), so the
# guarantee survives its first subject.
MUT="scripts/.arm12-zero.sh"
if mutate "${CANARY_STUB/7 caught/0 caught}" "$MUT"; then
  O=$(env TRUTH_ALLOW_NO_JSONSCHEMA=1 TRUTH_BATTERY_SCOPE="template/truthlib/kernel.py" \
      bash "$MUT" 2>&1); RC=$?
  rm -f "$MUT"
  if printf '%s' "$O" | grep -q "FAIL  canary" && [ "$RC" != "0" ]; then
    ok "a suite that examined nothing fails the battery instead of passing silently"
  else
    miss "a suite reporting 0 examined passed the battery (rc=$RC) -- the arm reports pass/fail, not what it examined"
  fi
else
  miss "ARM 12 could not mutate the canary invocation -- is the suite still wired into the battery?"
fi

echo "ARM 13: the reachability sweep must ride the battery, and a dark check must block"
run "$B"; O="$OUT"
DARK="scripts/test-zz-dark-arm.sh"        # an orphan nothing invokes
printf '#!/usr/bin/env bash\n# temporary orphan planted by test-release-battery ARM 13\nexit 0\n' > "$DARK"
run "$B"; O2="$OUT"; R2="$RC"
rm -f "$DARK"
if ! printf '%s' "$O" | grep -qE "ok    reachability -- [0-9]+ check"; then
  miss "the battery does not run the reachability sweep, or the sweep examined nothing"
elif printf '%s' "$O2" | grep -q "FAIL  reachability" && [ "$R2" != "0" ]; then
  ok "the sweep rides the battery and a planted orphan check blocks the push"
else
  miss "a check no root invokes passed the battery (rc=$R2) -- the sweep is decorative"
fi

echo "ARM 14: the battery must run THIS gate when the battery moves -- and only then"
# Exercised through a stub, because the honest version (letting the arm
# run the real gate) is this file calling itself. The stub stands in for
# the gate's summary line, which is what the arm actually judges.
META="scripts/.arm14-metastub.sh"
printf '#!/usr/bin/env bash\nprintf "test-release-battery: %%s caught, 0 missed\\n" "${STUB_CAUGHT:-14}"\n' > "$META"
MUT="scripts/.arm14-meta.sh"
if mutate 's|bash scripts/test-release-battery\.sh|bash scripts/.arm14-metastub.sh|' "$MUT"; then
  ON=$(env -u TRUTH_BATTERY_NO_META TRUTH_ALLOW_NO_JSONSCHEMA=1 \
       TRUTH_BATTERY_SCOPE="scripts/release-battery.sh" bash "$MUT" 2>&1)
  OFF=$(env -u TRUTH_BATTERY_NO_META TRUTH_ALLOW_NO_JSONSCHEMA=1 \
        TRUTH_BATTERY_SCOPE="$SCOPED" bash "$MUT" 2>&1)
  DARKRUN=$(env -u TRUTH_BATTERY_NO_META TRUTH_ALLOW_NO_JSONSCHEMA=1 STUB_CAUGHT=0 \
            TRUTH_BATTERY_SCOPE="scripts/release-battery.sh" bash "$MUT" 2>&1); RC=$?
  GUARDED=$(env TRUTH_BATTERY_NO_META=1 TRUTH_ALLOW_NO_JSONSCHEMA=1 \
            TRUTH_BATTERY_SCOPE="scripts/release-battery.sh" bash "$MUT" 2>&1)
  rm -f "$MUT" "$META"
  if ! printf '%s' "$ON" | grep -q "ok    battery meta-gate"; then
    miss "a push touching the battery did NOT run its mutation gate -- changed pass/fail logic ships unproven"
  elif ! printf '%s' "$OFF" | grep -q "skip  battery meta-gate"; then
    miss "the meta-gate ran on an unrelated push -- every push now pays minutes for an unchanged battery"
  elif ! printf '%s' "$DARKRUN" | grep -q "FAIL  battery meta-gate" || [ "$RC" = "0" ]; then
    miss "the meta-gate reported 0 arms caught and the battery called it green (rc=$RC)"
  elif ! printf '%s' "$GUARDED" | grep -q "skip  battery meta-gate -- re-entrant"; then
    miss "the re-entrancy guard is dead -- a battery run from inside the gate would recurse"
  else
    ok "the meta-gate fires on a battery push, skips otherwise, fails on a 0-arm report, and honours the re-entrancy guard"
  fi
else
  rm -f "$META"
  miss "ARM 14 could not mutate the meta-gate invocation -- is this file still wired into the battery?"
fi

echo "ARM 15: the canary summary contract must hold at its SOURCE, not just in the stub"
# ARMS 2, 3 and 12 feed the battery a SYNTHETIC canary summary, which makes
# them fast but also makes them a SECOND implementation of one contract.
# The dangerous drift is silent: change the battery's parser and update the
# stub in one move, and this suite stays green while the real canary emits
# the old format -- the battery would stop judging the canary in production
# and say nothing. Raised by session 01JdHzXY, 2026-08-21.
#
# The fix is to pin the contract to the PRODUCER'S SOURCE rather than to a
# run of it: cheap (a grep, not 45s), and it fails the moment the stub and
# the producer stop describing the same thing.
CANARY_SRC="template/scripts/truth-canary.sh"
if ! grep -q 'canary result: \$PASS caught' "$CANARY_SRC"; then
  miss "the canary no longer emits 'canary result: N caught' -- the battery's parser and this suite's stub are now fiction"
elif ! grep -q 'ALL CANARIES CAUGHT' "$CANARY_SRC"; then
  miss "the canary no longer emits 'ALL CANARIES CAUGHT' -- the battery's success test is now fiction"
elif ! grep -q "sed -n 's/\^canary result: " scripts/release-battery.sh; then
  miss "the battery no longer parses the canary summary the way this suite stubs it"
else
  ok "the canary's summary contract holds at the producer, so the stub still stands for something real"
fi

printf '\ntest-release-battery: %d caught, %d missed\n' "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ] || exit 1
echo "ALL BATTERY ARMS CAUGHT."
