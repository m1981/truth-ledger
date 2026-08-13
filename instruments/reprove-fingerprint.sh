#!/usr/bin/env bash
# Re-prove the fingerprint's SENSITIVITY, in your own tree.
#
# The fingerprint is the acceptance instrument for the A1-A4 refactors. An
# instrument that cannot detect a behaviour change is worse than none, because
# it turns "no diff" into false assurance. So it does not get to assert its own
# red-proof: it gets re-run here, by you, on your machine.
#
# Each row seeds ONE behaviour change, runs the fingerprint, restores, and
# reports. Every row must print DETECTED; the control must print IDENTICAL.
# A MISSED means the instrument is blind for that class and no brief may be
# accepted against it.
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TPL="$ROOT/template"
FP="$ROOT/instruments/fingerprint.sh"
BASE="$ROOT/instruments/fingerprint-baseline.txt"
cd "$ROOT" || exit 1

[ -x "$FP" ] || { echo "FAIL: $FP missing or not executable"; exit 1; }
[ -s "$BASE" ] || { echo "FAIL: $BASE missing"; exit 1; }

TMP="$(mktemp -d)"
# This script deliberately MUTATES truthlib in place, so an interrupted run
# leaves the repository broken -- and the old trap deleted $TMP, destroying
# the backups that were the only way back. Both halves of that bit for real:
# a `| head -6` closed the pipe, SIGPIPE killed the run mid-M3, and
# `CITATIONS_EXIT_CITED -> 1` stayed in cli.py. The canary then read
# 282 caught / 1 missed (FAULT TG6) on a tree whose git status showed one
# stray modified file, and that number was nearly written down as a finding.
#
# So: restore before removing, and catch the signals that skip an EXIT trap.
# EXIT alone does NOT run when the shell is killed by an uncaught SIGPIPE.
CLEANED=0
cleanup() {
  [ "$CLEANED" = 1 ] && return 0      # idempotent: signal path then EXIT
  CLEANED=1
  local b m damaged=0
  for b in "$TMP"/*.bak; do
    [ -e "$b" ] || continue
    m="$(basename "$b" .bak)"
    cp "$b" "$TPL/truthlib/$m.py"
    damaged=1
    echo "reprove: ROLLED BACK a seeded mutation in truthlib/$m.py" >&2
  done
  if [ "$damaged" = 1 ]; then
    echo "reprove: the run did not finish -- the tree was restored, but \
re-run this to completion before trusting any result" >&2
  fi
  rm -rf "$TMP"
}
# The signal handlers must EXIT, not return. A trap on PIPE hands control
# back to the script, so cleanup would fire, delete $TMP, and the script
# would then keep seeding mutations with nowhere to back them up -- one
# stray mutation turned into two when this was written the obvious way.
trap 'cleanup; exit 130' INT TERM HUP PIPE
trap cleanup EXIT
FAILED=0

run_fp() { bash "$FP" > "$TMP/out.txt" 2>&1; }

report() {  # report "<label>" "<expect DETECTED|IDENTICAL>"
  local label="$1" expect="$2" n
  run_fp
  if diff -q "$BASE" "$TMP/out.txt" >/dev/null 2>&1; then
    if [ "$expect" = "IDENTICAL" ]; then
      printf '  %-42s IDENTICAL  ok\n' "$label"
    else
      printf '  %-42s MISSED     <-- INSTRUMENT IS BLIND HERE\n' "$label"
      FAILED=1
    fi
  else
    n=$(diff "$BASE" "$TMP/out.txt" | grep -c '^[<>]')
    if [ "$expect" = "DETECTED" ]; then
      printf '  %-42s DETECTED   (%s lines)\n' "$label" "$n"
    else
      # TWO different faults produce this one symptom, and naming only
      # the rarer one sends the reader hunting a clock leak when the fix
      # is one command. A control that differs means EITHER the
      # instrument is non-deterministic OR -- far more often -- the
      # committed baseline was generated on a different tree than the
      # one you are standing in.
      printf '  %-42s DIFFERS    <-- baseline stale for this tree, or the instrument is non-deterministic (%s lines)\n' \
             "$label" "$n"
      printf '  %-42s            check `git log -1 --format=%%h -- %s` against HEAD; if the baseline predates a DELIBERATE behaviour change, regenerate it in a commit of its own that explains every line\n' \
             "" "${BASE#"$(cd "$(dirname "$0")/.." && pwd)/"}"
      FAILED=1
    fi
  fi
}

seed() {  # seed <module> <python-replace-expression-file>
  cp "$TPL/truthlib/$1.py" "$TMP/$1.bak"
}
# A leftover .bak means a mutation that was never rolled back, so restore
# removes its own backup and the trap treats whatever survives as damage.
restore() { cp "$TMP/$1.bak" "$TPL/truthlib/$1.py"; rm -f "$TMP/$1.bak"; }

echo "Re-proving fingerprint sensitivity against $BASE"
echo

# -- control: unmodified tree must reproduce the baseline exactly ----------
report "control (nothing seeded)" IDENTICAL

# -- M1: two INTAKE_GATES rows swapped ------------------------------------
seed gates
python3 - "$TPL" <<'EOF'
import sys
p = sys.argv[1] + "/truthlib/gates.py"
s = open(p).read()
a = '    ("pre-execution", "near-duplicate-g8", _gate_duplicate),\n    ("pre-execution", "quantifier-scope-adr007", _gate_quantifier_scope),'
b = '    ("pre-execution", "quantifier-scope-adr007", _gate_quantifier_scope),\n    ("pre-execution", "near-duplicate-g8", _gate_duplicate),'
assert a in s, "gates.py shape changed -- update this seed"
open(p, "w").write(s.replace(a, b, 1))
EOF
report "M1  two INTAKE_GATES rows swapped" DETECTED
restore gates

# -- M2: one word in a refusal message ------------------------------------
seed policy
python3 - "$TPL" <<'EOF'
import sys
p = sys.argv[1] + "/truthlib/policy.py"
s = open(p).read()
assert "must record WHY" in s, "policy.py shape changed -- update this seed"
open(p, "w").write(s.replace("must record WHY", "must record why", 1))
EOF
report "M2  one word changed in a refusal" DETECTED
restore policy

# -- M3: a non-trivial exit code ------------------------------------------
seed cli
python3 - "$TPL" <<'EOF'
import sys
p = sys.argv[1] + "/truthlib/cli.py"
s = open(p).read()
a = "sys.exit(CITATIONS_EXIT_CITED if any_cited else 0)"
assert a in s, "cli.py shape changed -- update this seed"
open(p, "w").write(s.replace(a, "sys.exit(1 if any_cited else 0)", 1))
EOF
report "M3  CITATIONS_EXIT_CITED -> 1" DETECTED
restore cli

# -- M4: one CC-1 advisory line dropped -----------------------------------
seed advisory
python3 - "$TPL" <<'EOF'
import sys
p = sys.argv[1] + "/truthlib/advisory.py"
s = open(p).read()
a = '    msgs.extend(recipe_lints((payload.get("evidence") or {}).get("command")))'
assert a in s, "advisory.py shape changed -- update this seed"
open(p, "w").write(s.replace(a, "    pass", 1))
EOF
report "M4  one CC-1 advisory line dropped" DETECTED
restore advisory

# -- control again: restoration must be exact -----------------------------
report "control (after all restores)" IDENTICAL

echo
if [ "$FAILED" = 0 ]; then
  echo "SENSITIVITY PROVEN — the fingerprint may be used as the acceptance"
  echo "instrument for briefs A1-A4."
else
  echo "SENSITIVITY NOT PROVEN — do not accept any brief against this"
  echo "instrument until every row reads DETECTED and both controls read"
  echo "IDENTICAL. A blind instrument turns 'no diff' into false assurance."
fi
exit "$FAILED"
