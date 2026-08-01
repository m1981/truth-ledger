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
cd "$(dirname "$0")/.."
PASS=0; FAIL=0
ok()   { PASS=$((PASS+1)); printf '  CAUGHT: %s\n' "$*"; }
miss() { FAIL=$((FAIL+1)); printf '  MISSED: %s\n' "$*"; }
# BATTERY is overridable so the arms can be pointed at a deliberately
# mutated copy — that is how each one was proven capable of failing.
B="${BATTERY:-scripts/release-battery.sh}"

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

printf '\ntest-release-battery: %d caught, %d missed\n' "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ] || exit 1
echo "ALL BATTERY ARMS CAUGHT."
