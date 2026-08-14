#!/usr/bin/env bash
# Re-prove the VERB sweep added for wk-24db9abe -- the second half of the
# fingerprint's red proof, kept in its own file.
#
# WHY IT IS SEPARATE. reprove-fingerprint.sh proves four CLASSES of change are
# visible (a gate reorder, a refusal's wording, an exit code, an advisory line)
# and its four-row output is quoted as an expected value in
# docs/reviews/architecture-repairs-2026-08-13.md. This file proves something
# narrower and larger: that each of the ~50 probes appended for wk-24db9abe can
# actually FAIL. That distinction earned its own file the hard way -- eight
# verbs went unprobed for the whole A1-A4 series precisely because the four-row
# proof read PROVEN and nobody asked "of what?".
#
# Same discipline: seed ONE behaviour change, run the fingerprint, diff against
# the committed baseline, restore. A row that prints MISSED means the probe it
# targets cannot fail and is filler. A row that prints SEED FAILED means the
# mutation never landed -- which is NOT evidence about the probe, and is the
# mistake this harness refuses to let you make silently: it asserts the anchor
# text is present before writing, and asserts the write changed the file.
#
# It mutates truthlib in place, so do NOT pipe it into `head` or anything that
# closes the pipe early; the trap catches PIPE and restores, but a run that
# ends mid-sweep proves nothing.
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TPL="$ROOT/template"
FP="$ROOT/instruments/fingerprint.sh"
BASE="$ROOT/instruments/fingerprint-baseline.txt"
TMP="$(mktemp -d)"
CLEANED=0
cleanup() {
  [ "$CLEANED" = 1 ] && return 0
  CLEANED=1
  for b in "$TMP"/*.bak; do
    [ -e "$b" ] || continue
    m="$(basename "$b" .bak)"
    cp "$b" "$TPL/truthlib/$m.py"
    echo "redproof: ROLLED BACK truthlib/$m.py" >&2
  done
  rm -rf "$TMP"
}
trap 'cleanup; exit 130' INT TERM HUP PIPE
trap cleanup EXIT
FAILED=0

row() {  # row <label> <module> <old> <new>
  local label="$1" mod="$2" old="$3" new="$4" n
  cp "$TPL/truthlib/$mod.py" "$TMP/$mod.bak"
  MOD="$TPL/truthlib/$mod.py" OLD="$old" NEW="$new" python3 - <<'EOF' || { echo "  $label  SEED FAILED (mutation did not land)"; FAILED=1; rm -f "$TMP/$mod.bak"; return; }
import os, sys
p, old, new = os.environ["MOD"], os.environ["OLD"], os.environ["NEW"]
s = open(p).read()
if old not in s:
    sys.exit(1)
s2 = s.replace(old, new, 1)
assert s2 != s, "replacement was a no-op"
open(p, "w").write(s2)
EOF
  bash "$FP" > "$TMP/out.txt" 2>&1
  if diff -q "$BASE" "$TMP/out.txt" >/dev/null 2>&1; then
    printf '  %-34s MISSED   <-- BLIND\n' "$label"
    FAILED=1
  else
    n=$(diff "$BASE" "$TMP/out.txt" | grep -c '^[<>]')
    printf '  %-34s DETECTED (%s lines)\n' "$label" "$n"
  fi
  cp "$TMP/$mod.bak" "$TPL/truthlib/$mod.py"; rm -f "$TMP/$mod.bak"
}

echo "Red-proving the wk-24db9abe probes against $BASE"
echo

row "M-B  tracker refusal bytes" shellio \
  'tracker command failed ({cmd!r}, exit {r.returncode})' \
  'tracker command exploded ({cmd!r}, code {r.returncode})'
row "M-B2 tracker not-JSON refusal" shellio \
  'output is not JSON -- tracker contract may ' \
  'output is not json -- tracker contract may '
row "M-B3 tracker not-array refusal" shellio \
  'output is JSON but not an array' \
  'output is JSON but not a list'
row "M-F  ADR-037 generated refusal" gates \
  'restales on every regeneration' \
  'restales on each regeneration'
row "M-F2 SI-1 pathspec-magic refusal" shellio \
  'pathspec magic is refused' \
  'pathspec magic is rejected'
row "M-A  events_at_ref exit 2 -> 3" cli \
  '        sys.exit(2)' \
  '        sys.exit(3)'
row "M-G  baseline exit 5 -> 0" cli \
  'sys.exit(5 if disappeared else 0)' \
  'sys.exit(0)'
row "M-H  dispatch unknown-claim" cli \
  'truth: unknown claim {a.claim_id}' \
  'truth: no such claim {a.claim_id}'
row "M-I  dispatch prompt-missing" cli \
  'truth: verifier prompt missing at {PROMPT_REL}' \
  'truth: verifier prompt absent at {PROMPT_REL}'
row "M-J  G11 envelope integrity header" contract \
  'numbered rules and ends with the ' \
  'numbered rules, ending with the '
row "M-K  list row format" cli \
  "print(f\"{r['id']}  {r['status']:<13} {r['tier']:<3} \"" \
  "print(f\"{r['id']}  {r['status']:<14} {r['tier']:<3} \""
row "M-L  E1 --ready-json contract" cli \
  'print(json.dumps(native_ready_issues(issues)))' \
  'print(json.dumps([{"id": i["id"]} for i in native_ready_issues(issues)]))'
row "M-M  ready HELD line" cli \
  "print(f\"HELD {i.get('id')}  broken premises: \"" \
  "print(f\"HOLD {i.get('id')}  broken premises: \""
row "M-N  invalidate-scan summary" cli \
  'print(f"invalidate-scan: {len(hits)} claim(s) marked stale")' \
  'print(f"invalidate-scan: {len(hits)} claim(s) staled")'
row "M-O  invalidate-scan stale row" cli \
  'print(f"stale: {cid} ({why})")' \
  'print(f"STALE {cid} ({why})")'
row "M-P  reaffirm same-session arm" evidence \
  'skipped -- authored by this session; reaffirm ' \
  'skipped -- authored by THIS session; reaffirm '
row "M-Q  reaffirm mismatch arm" evidence \
  'diverged evidence -- dispatch for judgment' \
  'diverged evidence -- dispatch for review'
row "M-R  REAFFIRM_BASIS (filing arm)" evidence \
  'REAFFIRM_BASIS = "reaffirm: hash-match, no judgment re-run"' \
  'REAFFIRM_BASIS = "reaffirm: hash-match, no judgment rerun"'
row "M-S  reaffirm self-verdict warning" cli \
  'truth: WARNING: TRUTH_SELF_VERDICT=1 override active -- ' \
  'truth: WARNING: TRUTH_SELF_VERDICT=1 override on -- '
row "M-T  queue reason (stale P0/P1)" reports \
  'reason = "evidence invalidated"' \
  'reason = "evidence went stale"'
row "M-U  stats verdicts line" cli \
  "print(f\"verdicts: agree={v['agree']} diverge_genuine=\"" \
  "print(f\"verdicts: agrees={v['agree']} diverge_genuine=\""
row "M-V  baseline text arm" cli \
  "print(f\"baseline {a.ref} ({snap_a['commit']}): \"" \
  "print(f\"baseline of {a.ref} ({snap_a['commit']}): \""
row "M-W  baseline --diff born block" cli \
  "print(f\"{kind} born: {len(d['born'])} \"" \
  "print(f\"{kind} new: {len(d['born'])} \""
row "M-X  issues row premises" cli \
  "extra += f\"  premises: {','.join(r['premises'])}\"" \
  "extra += f\"  premise: {','.join(r['premises'])}\""

row "M-Y  impact --inverse exit 4 -> 0" cli \
  'sys.exit(4 if rep["dark"] else 0)' \
  'sys.exit(0)'
row "M-Z  reproduce exit 7 -> 0" cli \
  'sys.exit(REPRODUCE_EXIT_STALE)' \
  'sys.exit(0)'
row "M-Z2 verdict success echo" cli \
  'f"{a.claim_id} -> {verdict}"' \
  'f"{a.claim_id} => {verdict}"'
row "M-Z3 reproduce capsule-stale shape" cli \
  'capsule-stale shapes: ' \
  'capsule-stale kinds: '

echo
[ "$FAILED" = 0 ] && echo "ALL NEW PROBES RED-PROVEN" || echo "SOME ROWS MISSED"
exit "$FAILED"
