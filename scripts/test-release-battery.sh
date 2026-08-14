#!/usr/bin/env bash
# Regression gate for scripts/release-battery.sh and the pre-push wiring.
# META-REPO ONLY, following the precedent of scripts/test-whisper-hook.sh:
# both guard untemplated consumer machinery, which by definition has no
# home in the template canary.
#
# Each arm below was verified to FAIL against a deliberately mutated copy
# of the battery before being committed. An arm that has never been seen
# red is an arm that cannot go red -- this repo shipped exactly that
# defect on 2026-08-01 (a canary arm whose grep matched doctor's OK line
# as happily as its WARN line, so it could never report a miss).
set -u
# Every arm below MUTATES a gate script into scripts/.armN-*.sh and removes
# it on the next line. An interrupted run skips that line, so up to six
# mutated copies of the release gates are left sitting in scripts/ -- and
# they are dotfiles, so they read as noise rather than as damage. Observed:
# a ^C during the battery left scripts/.arm5-forced-fail.sh behind. Same
# class as reprove-fingerprint.sh's seeded mutations: an instrument that
# edits the repo owes it a rollback on EVERY exit path, not just the happy
# one.
cleanup_mutants() {
  local m found=0
  # scripts/test-zz-dark-arm.sh is ARM 11's planted orphan and is NOT a
  # dotfile, so a glob over .arm*.sh alone would leave it behind -- and an
  # orphan check left in scripts/ is exactly what gate-reachability.sh
  # fails on, so the debris would surface later as a confusing gate
  # failure rather than as leftover test state.
  for m in scripts/.arm*.sh scripts/test-zz-dark-arm.sh; do
    [ -e "$m" ] || continue
    rm -f "$m"; found=1
    echo "test-release-battery: removed leftover mutant $m" >&2
  done
  [ "$found" = 1 ] && echo "test-release-battery: the run did not finish -- \
mutants were cleaned up, but re-run it to completion" >&2
  return 0
}
trap 'cleanup_mutants; exit 130' INT TERM HUP PIPE
trap cleanup_mutants EXIT
cd "$(dirname "$0")/.."
PASS=0; FAIL=0
ok()   { PASS=$((PASS+1)); printf '  CAUGHT: %s\n' "$*"; }
miss() { FAIL=$((FAIL+1)); printf '  MISSED: %s\n' "$*"; }
# BATTERY is overridable so the arms can be pointed at a deliberately
# mutated copy — that is how each one was proven capable of failing.
B="${BATTERY:-scripts/release-battery.sh}"
# RE-ENTRANCY GUARD, not a waiver. The battery gained an arm that runs
# THIS file when the battery moves (release-battery.sh section 9), so a
# battery launched from here must not launch it back: ARM 3 runs the
# battery at scope ALL, which matches that arm, and the first cut spent
# minutes running a nested copy of this whole gate. It suppresses exactly
# one arm -- the one that would recurse -- and only the battery and this
# file ever set it. ARM 12 unsets it deliberately, pointing the arm at a
# stub, which is the only way to exercise the wiring without recursing.
export TRUTH_BATTERY_NO_META=1

echo "ARM 1: an out-of-scope push must SKIP the 45s canary"
OUT=$(TRUTH_ALLOW_NO_JSONSCHEMA=1 TRUTH_BATTERY_SCOPE="docs/whatever.md" bash "$B" 2>&1)
if printf '%s' "$OUT" | grep -q "skip  canary"; then
  ok "canary skipped when neither the CLI nor the suite moved"
else
  miss "canary did not skip on an out-of-scope push -- every push now costs 45s"
fi

echo "ARM 2: a push touching the CLI must RUN the canary"
OUT=$(TRUTH_ALLOW_NO_JSONSCHEMA=1 TRUTH_BATTERY_SCOPE="template/scripts/truth" bash "$B" 2>&1)
if printf '%s' "$OUT" | grep -qE "ok    canary -- [0-9]+ seeded faults caught"; then
  ok "canary runs and reports its arm count when the CLI moved"
else
  miss "canary did not run on a CLI push -- behaviour regressions ship unchecked"
fi

echo "ARM 3: unknown scope must widen to ALL, never narrow"
OUT=$(TRUTH_ALLOW_NO_JSONSCHEMA=1 TRUTH_BATTERY_SCOPE="ALL" bash "$B" 2>&1)
if printf '%s' "$OUT" | grep -q "ok    canary"; then
  ok "scope ALL runs every arm (the fail-safe direction)"
else
  miss "scope ALL skipped an arm -- an unresolvable range would check LESS"
fi

echo "ARM 4: a missing jsonschema is an ENVIRONMENT block (exit 2), not a pass"
# NB: this script runs under `set -u` only. Do NOT `set -e` here -- arms 4
# and 5 deliberately run a battery that exits non-zero, and errexit would
# kill the suite mid-arm (it silently did, until 2026-08-01).
OUT=$(env -u TRUTH_ALLOW_NO_JSONSCHEMA TRUTH_BATTERY_SCOPE="docs/x.md" bash "$B" 2>&1); RC=$?
if python3 -c "import jsonschema" >/dev/null 2>&1; then
  echo "  (skipped: jsonschema is installed here, so the arm cannot be exercised)"
elif [ "$RC" = "2" ] && printf '%s' "$OUT" | grep -q "ENV   jsonschema"; then
  ok "missing jsonschema blocks with exit 2 and names both remedies"
else
  miss "missing jsonschema did not block as an environment problem (rc=$RC)"
fi

echo "ARM 5: a battery with ANY failing arm must not report green, and must exit 1"
# This arm was VACUOUS as first written (2026-08-01): it asked whether a
# healthy battery printed both FAIL and green, which a healthy battery
# never does, so it could only ever pass. The mutation run that "proved"
# the suite reddened arms 1-4 and never arm 5 — the evidence was in the
# output and went unread. It now MANUFACTURES a failing arm, which is the
# only way to test the exclusion it claims to test.
MUT="scripts/.arm5-forced-fail.sh"
sed 's|^say "release-battery: content checks at the push boundary"|&\nbad "synthetic" "deliberately failing arm injected by ARM 5"|' \
    "$B" > "$MUT"
OUT=$(TRUTH_ALLOW_NO_JSONSCHEMA=1 TRUTH_BATTERY_SCOPE="docs/x.md" bash "$MUT" 2>&1); RC=$?
rm -f "$MUT"
if printf '%s' "$OUT" | grep -q "all arms green"; then
  miss "battery printed 'all arms green' while an arm reported FAIL"
elif [ "$RC" != "1" ]; then
  miss "battery exited $RC with a failing arm -- a governance failure must exit 1"
else
  ok "a failing arm suppresses the green verdict and exits 1"
fi

echo "ARM 6: the pre-push hook keeps its tag-check arm ahead of the battery"
if grep -q "tag-check" .githooks/pre-push && grep -q "release-battery.sh" .githooks/pre-push; then
  ok "pre-push carries both the tag check and the battery"
else
  miss "pre-push lost an arm -- release coherence or content checking is dark"
fi


# --- the skip-awareness arms (added 2026-08-02) --------------------------
# The migration's P0 changed the battery's pass/fail LOGIC in three places
# -- the lockstep arm, the core-suite skip baseline, the v04 skip
# rejection -- and added nothing here. Changed judgment with no gate is
# the defect this file exists to prevent: "OK (skipped=k)" is what an arm
# prints when it examined less than it claims, and until 2026-08-01 the
# battery read it as a pass. These arms feed the battery SYNTHETIC suite
# output through a stub, because the alternative is mutating the suites
# themselves, which live in template/ and answer to the canary.
STUB="scripts/.skip-stub.py"
cat > "$STUB" <<'PY'
#!/usr/bin/env python3
"""Synthetic suite output for the skip-awareness arms: prints whatever
SUITE_OUT holds and exits 0, exactly as unittest does on a green run."""
import os
print(os.environ.get("SUITE_OUT", ""))
PY

mutate() {  # mutate <sedscript> <dest> -> 0 when the copy really changed
  sed "$1" "$B" > "$2"
  if cmp -s "$B" "$2"; then
    rm -f "$2"
    return 1   # the pattern drifted: an unmutated copy would PASS blindly
  fi
}

echo "ARM 7: a SKIPPED pinned surface must fail the version-lockstep arm"
MUT="scripts/.arm7-lockstep.sh"
if mutate 's|python3 template/scripts/test-truth-core\.py TestCrossSurfaceVersions|python3 scripts/.skip-stub.py|' "$MUT"; then
  SKIPPED_OUT=$'Ran 7 tests in 0.010s\n\nOK (skipped=1)'
  OUT=$(SUITE_OUT="$SKIPPED_OUT" TRUTH_ALLOW_NO_JSONSCHEMA=1 \
        TRUTH_BATTERY_SCOPE="docs/x.md" bash "$MUT" 2>&1); RC=$?
  CLEAN_OUT=$'Ran 7 tests in 0.010s\n\nOK'
  OUT2=$(SUITE_OUT="$CLEAN_OUT" TRUTH_ALLOW_NO_JSONSCHEMA=1 \
         TRUTH_BATTERY_SCOPE="docs/x.md" bash "$MUT" 2>&1)
  rm -f "$MUT"
  if printf '%s' "$OUT" | grep -q "FAIL  version lockstep" \
     && printf '%s' "$OUT" | grep -q "skipped=1" && [ "$RC" != "0" ] \
     && printf '%s' "$OUT2" | grep -q "ok    version lockstep -- 7 pinned surfaces agree"; then
    ok "a skipped pinned surface fails the lockstep arm, and the same 7 surfaces pass when none is skipped"
  else
    miss "lockstep accepted 'OK (skipped=1)' as 7 surfaces agreeing (rc=$RC) -- a renamed pinned doc would ship silently"
  fi
else
  miss "ARM 7 could not mutate the lockstep invocation -- the pattern drifted, so this arm was checking nothing"
fi

echo "ARM 8: the core-suite skip tolerance is the jsonschema baseline, and nothing wider"
MUT="scripts/.arm8-core.sh"
if mutate 's|python3 template/scripts/test-truth-core\.py 2>&1|python3 scripts/.skip-stub.py 2>\&1|' "$MUT"; then
  WIDE=$'Ran 293 tests in 1.000s\n\nOK (skipped=4)'
  OUT=$(SUITE_OUT="$WIDE" TRUTH_ALLOW_NO_JSONSCHEMA=1 \
        TRUTH_BATTERY_SCOPE="docs/x.md" bash "$MUT" 2>&1); RC=$?
  BASE=$'Ran 293 tests in 1.000s\n\nOK (skipped=3)'
  OUT2=$(SUITE_OUT="$BASE" TRUTH_ALLOW_NO_JSONSCHEMA=1 \
         TRUTH_BATTERY_SCOPE="docs/x.md" bash "$MUT" 2>&1)
  rm -f "$MUT"
  if ! printf '%s' "$OUT" | grep -q "FAIL  core suite" || [ "$RC" = "0" ]; then
    miss "the core suite skipped 4 tests beyond the baseline and the battery called it green (rc=$RC)"
  elif python3 -c "import jsonschema" >/dev/null 2>&1; then
    ok "a skip past the baseline fails (the baseline half is unexercisable: jsonschema IS installed here, so ANY skip must fail)"
  elif printf '%s' "$OUT2" | grep -q "ok    core suite" \
       && printf '%s' "$OUT2" | grep -q "jsonschema-gated skip"; then
    ok "4 skips fail; the 3 jsonschema-gated skips pass and are NAMED as the disclosed baseline"
  else
    miss "the tolerated jsonschema baseline (3 skips, jsonschema absent) did not pass, or passed without naming itself"
  fi
else
  miss "ARM 8 could not mutate the core-suite invocation -- the pattern drifted, so this arm was checking nothing"
fi

echo "ARM 9: ANY skip in the v04 suite must fail (no baseline there)"
MUT="scripts/.arm9-v04.sh"
if mutate 's|python3 template/scripts/test-truth-v04\.py|python3 scripts/.skip-stub.py|' "$MUT"; then
  SKIPPED_OUT=$'Ran 40 tests in 0.100s\n\nOK (skipped=1)'
  OUT=$(SUITE_OUT="$SKIPPED_OUT" TRUTH_ALLOW_NO_JSONSCHEMA=1 \
        TRUTH_BATTERY_SCOPE="docs/x.md" bash "$MUT" 2>&1); RC=$?
  CLEAN_OUT=$'Ran 40 tests in 0.100s\n\nOK'
  OUT2=$(SUITE_OUT="$CLEAN_OUT" TRUTH_ALLOW_NO_JSONSCHEMA=1 \
         TRUTH_BATTERY_SCOPE="docs/x.md" bash "$MUT" 2>&1)
  rm -f "$MUT"
  if printf '%s' "$OUT" | grep -q "FAIL  v04 suite" && [ "$RC" != "0" ] \
     && printf '%s' "$OUT2" | grep -q "ok    v04 suite"; then
    ok "a skipped fold invariant fails the v04 arm, and an unskipped run still passes"
  else
    miss "the v04 arm accepted a skipped fold invariant (rc=$RC) -- the fold contract would ship unexamined"
  fi
else
  miss "ARM 9 could not mutate the v04 invocation -- the pattern drifted, so this arm was checking nothing"
fi
rm -f "$STUB"

echo "ARM 10: every suite the battery wired must be judged by its OWN arm count"
# The 2026-08-02 defect in one line: four gates existed and no root ran
# them. The battery now runs them and reads their "N caught, M missed"
# summary -- so a suite that dies before printing one, or reports 0
# caught, must FAIL rather than pass quietly.
MUT="scripts/.arm10-emptysuite.sh"
if mutate 's|bash scripts/test-session-digest\.sh|true|' "$MUT"; then
  OUT=$(TRUTH_ALLOW_NO_JSONSCHEMA=1 TRUTH_BATTERY_SCOPE="docs/x.md" bash "$MUT" 2>&1); RC=$?
  rm -f "$MUT"
  if printf '%s' "$OUT" | grep -q "FAIL  session-digest gate" && [ "$RC" != "0" ]; then
    ok "a wired suite that prints no summary fails the battery instead of passing silently"
  else
    miss "a suite that examined nothing passed the battery (rc=$RC) -- the arm reports pass/fail, not what it examined"
  fi
else
  miss "ARM 10 could not mutate the session-digest invocation -- is the suite still wired into the battery?"
fi

echo "ARM 11: the reachability sweep must ride the battery, and a dark check must block"
OUT=$(TRUTH_ALLOW_NO_JSONSCHEMA=1 TRUTH_BATTERY_SCOPE="docs/x.md" bash "$B" 2>&1)
DARK="scripts/test-zz-dark-arm.sh"        # an orphan nothing invokes
printf '#!/usr/bin/env bash\n# temporary orphan planted by test-release-battery ARM 11\nexit 0\n' > "$DARK"
OUT2=$(TRUTH_ALLOW_NO_JSONSCHEMA=1 TRUTH_BATTERY_SCOPE="docs/x.md" bash "$B" 2>&1); RC=$?
rm -f "$DARK"
if ! printf '%s' "$OUT" | grep -qE "ok    reachability -- [0-9]+ checks examined"; then
  miss "the battery does not run the reachability sweep, or the sweep examined nothing"
elif printf '%s' "$OUT2" | grep -q "FAIL  reachability" && [ "$RC" != "0" ]; then
  ok "the sweep rides the battery and a planted orphan check blocks the push"
else
  miss "a check no root invokes passed the battery (rc=$RC) -- the sweep is decorative"
fi

echo "ARM 12: the battery must run THIS gate when the battery moves -- and only then"
# Exercised through a stub, because the honest version (letting the arm
# run the real gate) is this file calling itself. The stub stands in for
# the gate's summary line, which is what the arm actually judges.
META="scripts/.arm12-metastub.sh"
printf '#!/usr/bin/env bash\nprintf "test-release-battery: %%s caught, 0 missed\\n" "${STUB_CAUGHT:-6}"\n' > "$META"
MUT="scripts/.arm12-meta.sh"
if mutate 's|bash scripts/test-release-battery\.sh|bash scripts/.arm12-metastub.sh|' "$MUT"; then
  ON=$(env -u TRUTH_BATTERY_NO_META TRUTH_ALLOW_NO_JSONSCHEMA=1 \
       TRUTH_BATTERY_SCOPE="scripts/release-battery.sh" bash "$MUT" 2>&1)
  OFF=$(env -u TRUTH_BATTERY_NO_META TRUTH_ALLOW_NO_JSONSCHEMA=1 \
        TRUTH_BATTERY_SCOPE="docs/x.md" bash "$MUT" 2>&1)
  DARKRUN=$(env -u TRUTH_BATTERY_NO_META TRUTH_ALLOW_NO_JSONSCHEMA=1 STUB_CAUGHT=0 \
            TRUTH_BATTERY_SCOPE="scripts/release-battery.sh" bash "$MUT" 2>&1); RC=$?
  GUARDED=$(TRUTH_ALLOW_NO_JSONSCHEMA=1 \
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
  miss "ARM 12 could not mutate the meta-gate invocation -- is this file still wired into the battery?"
fi

printf '\ntest-release-battery: %d caught, %d missed\n' "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ] || exit 1
echo "ALL BATTERY ARMS CAUGHT."
