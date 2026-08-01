#!/usr/bin/env bash
# Regression gate for the consumer-side citation tripwire
# (scripts/fact-health.sh). META-REPO ONLY, like the whisper gate:
# fact-health is deliberately untemplated (ADR-003), so the template
# canary cannot carry these arms. Closes R12/L4-F3: the release battery
# proved fact-health RUNS and swept >0 citations; nothing ever seeded a
# dead citation and confirmed the JUDGMENT fires. One sandbox corpus,
# one arm per judgment class -- including the disputed class R1 added.
#
# The sandbox reproduces the exact layout fact-health hardcodes: the
# script cd's to its dir's parent and calls `python3
# template/scripts/truth list --json` plus `git ls-files`, so the
# sandbox is a git repo with scripts/ + template/scripts/ + .truth/.
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PASS=0; FAIL=0
ok()  { PASS=$((PASS+1)); printf '  CAUGHT: %s\n' "$*"; }
bad() { FAIL=$((FAIL+1)); printf '  MISSED: %s\n' "$*"; }
say() { printf '%s\n' "$*"; }

SB="$(mktemp -d)"
trap 'rm -rf "$SB"' EXIT
export TRUTH_ACTOR=fh-test TRUTH_SESSION=s-fh-test
T="python3 template/scripts/truth"

cd "$SB"
git init -q -b main .
git config user.email fh@test.local
git config user.name fh-test
mkdir -p scripts template/scripts .truth docs
cp "$ROOT/scripts/fact-health.sh" scripts/fact-health.sh
cp "$ROOT/template/scripts/truth" template/scripts/truth
cp "$ROOT/template/.truth/evidence-allow" .truth/evidence-allow
cp "$ROOT/template/.truth/evidence-deny" .truth/evidence-deny
cp "$ROOT/template/.truth/generated-paths" .truth/generated-paths
touch .truth/claims.jsonl
echo "live content" > watched.txt
echo "original" > stale-watch.txt
git add -A && git commit -qm "fh: init"

# live: VERIFIED + cross-session agree (ADR-010: never the author's session)
CID_LIVE=$($T claim "watched.txt carries the live sandbox content" \
           --class VERIFIED --evidence-cmd "cat watched.txt" \
           --paths "watched.txt" --tier P1 2>/dev/null)
TRUTH_SESSION=s-fh-verifier $T verdict "$CID_LIVE" agree \
  --basis "fh: verified at filing" >/dev/null 2>&1

say "CASE 1 (green corpus): live citation ok, zero-citation doc silent, exit 0"
printf '# README\nGround truth: %s anchors this corpus.\n' "$CID_LIVE" > README.md
printf '# clean\nprose with no citations at all\n' > docs/clean.md
git add -A && git commit -qm "fh: green corpus"
OUT=$(bash scripts/fact-health.sh 2>&1); RC=$?
if [ "$RC" -eq 0 ] && printf '%s\n' "$OUT" | grep -q "ok    $CID_LIVE  live"; then
  ok "live citation judged ok at exit 0"
else
  bad "green corpus wrong (rc=$RC): $(printf '%s\n' "$OUT" | tail -3)"
fi
if printf '%s\n' "$OUT" | grep -q "docs/clean.md"; then
  bad "zero-citation doc was named -- silent pass is its contract"
else
  ok "zero-citation doc passed silently"
fi

# stale: the FAULT B pattern -- evidence path changes, invalidate-scan stales
CID_STALE=$($T claim "stale-watch.txt still says original" \
            --class VERIFIED --evidence-cmd "cat stale-watch.txt" \
            --paths "stale-watch.txt" --tier P1 2>/dev/null)
TRUTH_SESSION=s-fh-verifier $T verdict "$CID_STALE" agree \
  --basis "fh: verified at filing" >/dev/null 2>&1
git add .truth/claims.jsonl && git commit -qm "fh: stale claim filed"
echo "changed" >> stale-watch.txt
git add stale-watch.txt && git commit -qm "fh: mutate evidence"
$T invalidate-scan --quiet 2>/dev/null

# disputed: contradicts edge on two live claims (R1)
CID_D1=$($T claim "fh-fixture engine reads config from disk" \
         --class UNVERIFIED --tier P1 2>/dev/null)
CID_D2=$($T claim "fh-fixture engine takes config over the network" \
         --class UNVERIFIED --tier P1 2>/dev/null)
TRUTH_SESSION=s-fh-verifier $T verdict "$CID_D1" agree --basis "fh: d" >/dev/null 2>&1
TRUTH_SESSION=s-fh-verifier $T verdict "$CID_D2" agree --basis "fh: d" >/dev/null 2>&1
$T contradicts "$CID_D1" "$CID_D2" --basis "fh: cannot both hold" >/dev/null 2>&1

printf '# dead\nstands on %s and %s\n' "$CID_STALE" "$CID_D1" > docs/dead.md
printf '# fence\n```\nsample transcript citing tr-00000001\nthe fence above never closes; %s sits below it\n' "$CID_LIVE" > docs/fence.md
printf '# nearmiss\nsee tr-DEADBEEF for details\n' > docs/nearmiss.md
printf '# unknown prefix\ncites unknownrepo:tr-12345678\n' > docs/unknown.md
printf '# foreign\npilot fact kuchnie:tr-12345678 lives elsewhere\n' > docs/foreign.md
printf '# missing\nstands on tr-0badf00d\n' > docs/missing.md
git add -A && git commit -qm "fh: bad corpus"

if ! $T list --stale 2>/dev/null | grep -q "$CID_STALE"; then
  bad "fault injection failed: $CID_STALE never went stale"
fi
if ! $T list --disputed 2>/dev/null | grep -q "$CID_D1"; then
  bad "fault injection failed: $CID_D1 never derived DISPUTED"
fi

OUT=$(bash scripts/fact-health.sh 2>&1); RC=$?

say "CASE 2 (R1): a DISPUTED citation must FAIL"
if printf '%s\n' "$OUT" | grep -q "FAIL  $CID_D1  disputed"; then
  ok "disputed citation failed the sweep"
else
  bad "disputed $CID_D1 not failed: $(printf '%s\n' "$OUT" | grep "$CID_D1" || echo '<no line>')"
fi

say "CASE 3: a stale citation must FAIL"
if printf '%s\n' "$OUT" | grep -q "FAIL  $CID_STALE  stale"; then
  ok "stale citation failed the sweep"
else
  bad "stale $CID_STALE not failed: $(printf '%s\n' "$OUT" | grep "$CID_STALE" || echo '<no line>')"
fi

say "CASE 4: an unbalanced fence must FAIL loudly, never skip silently"
if printf '%s\n' "$OUT" | grep -q 'unbalanced ``` fence'; then
  ok "odd fence count reported as a dead sensor"
else
  bad "unbalanced fence in docs/fence.md not reported"
fi

say "CASE 5: a near-miss id must FAIL, not vanish from the sweep"
if printf '%s\n' "$OUT" | grep -q "FAIL  tr-DEADBEEF  malformed id"; then
  ok "malformed tr-DEADBEEF failed the sweep"
else
  bad "near-miss tr-DEADBEEF vanished from the sweep"
fi

say "CASE 6: an unknown foreign prefix must FAIL, never escape judgment"
if printf '%s\n' "$OUT" | grep -q "FAIL  unknownrepo:tr-12345678  unknown prefix"; then
  ok "unknown prefix failed the sweep"
else
  bad "unknownrepo: prefix escaped judgment"
fi

say "CASE 7: a known deployment id is INFO, not judged"
if printf '%s\n' "$OUT" | grep -q "INFO  kuchnie:tr-12345678  foreign ledger -- not judged here" \
   && printf '%s\n' "$OUT" | grep -q "1 foreign (not judged)"; then
  ok "kuchnie: citation reported INFO and counted foreign"
else
  bad "foreign kuchnie: citation handling wrong"
fi

say "CASE 8: a bare id missing from the ledger must FAIL"
if printf '%s\n' "$OUT" | grep -q "FAIL  tr-0badf00d  missing from ledger"; then
  ok "missing bare id failed the sweep"
else
  bad "missing tr-0badf00d not failed"
fi

say "CASE 9: the bad corpus exits non-zero"
if [ "$RC" -ne 0 ]; then
  ok "sweep over the bad corpus exited $RC"
else
  bad "sweep exited 0 over a corpus full of dead citations"
fi

printf '\nfact-health gate: %d caught, %d missed\n' "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ] && echo "ALL FACT-HEALTH CASES CAUGHT." || exit 1
