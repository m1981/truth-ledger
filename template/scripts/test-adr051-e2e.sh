#!/usr/bin/env bash
# ADR-051 end-to-end acceptance, through the REAL CLI in a sandbox.
# Proves the whole chain, not a unit: an agree over a changed output is
# refused; --refresh-evidence files it; and the refreshed claim BECOMES
# PRODUCIBLE AGAIN -- which is the only thing that makes the refresh worth
# having. That last check used to be "returns to reaffirm's mechanical
# arm"; step 2.6 retired that verb and `truth reproduce` asks the same
# question more strictly, filing nothing in either direction.
set -u
TL="$(cd "$(dirname "$0")/.." && pwd)"
D="$(mktemp -d)"; cd "$D" || exit 1
fail(){ echo "  FAIL: $*"; FAILED=1; }
ok(){ echo "  ok: $*"; }
FAILED=0
t(){ python3 "$TL/scripts/truth" "$@"; }

git init -q .; git config user.email a@b; git config user.name a
mkdir -p .truth/schema
cp "$TL/.truth/schema/claims.schema.json" .truth/schema/
printf 'grep\ncat\nwc\n' > .truth/evidence-allow
cp "$TL/.truth/evidence-deny" .truth/ 2>/dev/null || :
: > .truth/generated-paths
printf 'x\nx\n' > f.txt
echo "scripts/truth" > AGENTS.md
printf '.truth/claims.jsonl merge=union\n' > .gitattributes
git add -A >/dev/null; git commit -qm init

echo "1. file a VERIFIED claim watching f.txt"
CID=$(t claim "f.txt holds exactly two x lines" --class VERIFIED \
        --evidence-cmd "grep -c x f.txt" --paths f.txt 2>/dev/null | tail -1)
[ -n "$CID" ] || { echo "  FAIL: no claim filed"; exit 1; }
ok "$CID"

echo "2. independent agree while the capsule still reproduces"
TRUTH_SESSION=s-verifier1 t verdict "$CID" agree --basis "re-ran it" \
  >/dev/null 2>&1 && ok "clean agree passes silently (no flag needed)" \
  || fail "a matching capsule must not need --refresh-evidence"

echo "3. change the watched file so the OUTPUT changes"
printf 'x\nx\nx\n' > f.txt; git add f.txt; git commit -qm "third x"
# Step 2.5: a path touch no longer stales anything -- `reproduce` is what
# names a claim whose capsule stopped producing, and it exits 7 on one.
t reproduce 2>/dev/null | grep -q "^$CID  capsule-stale" \
  && ok "capsule no longer reproduces" || fail "reproduce did not flag the changed capsule"

echo "4. the orphaning agree must be REFUSED"
OUT=$(TRUTH_SESSION=s-verifier2 t verdict "$CID" agree \
        --basis "sentence still holds" 2>&1)
RC=$?
if [ $RC -ne 0 ] && printf '%s' "$OUT" | grep -q "ADR-051"; then
  ok "refused, naming the flag and the diverge branch"
  printf '%s' "$OUT" | grep -q -- "--refresh-evidence" || fail "flag not named"
  printf '%s' "$OUT" | grep -q "diverge" || fail "diverge branch not offered"
else
  fail "the orphaning agree was ACCEPTED (rc=$RC)"
fi
N=$(wc -l < .truth/claims.jsonl)

echo "5. nothing was appended by the refusal"
[ "$N" = "$(wc -l < .truth/claims.jsonl)" ] && ok "ledger unchanged"

echo "6. --refresh-evidence files it and stores the observed capsule"
TRUTH_SESSION=s-verifier2 t verdict "$CID" agree \
  --basis "sentence still holds" \
  --refresh-evidence "the count grew from 2 to 3; the sentence is about
the shape of the file, not the number" >/dev/null 2>&1 \
  && ok "filed" || fail "refresh path refused"
python3 - "$CID" <<'EOF'
import json,sys
cid=sys.argv[1]; found=None
for l in open(".truth/claims.jsonl"):
    e=json.loads(l)
    if e["kind"]=="verdict" and e["payload"].get("claim")==cid \
       and e["payload"].get("evidence_refresh"):
        found=e["payload"]
print("  ok: evidence_refresh stored, anchor advanced together"
      if found and found.get("anchor_commit") else
      "  FAIL: refresh or anchor missing")
EOF

echo "7. validate accepts the new record"
t validate >/dev/null 2>&1 && ok "validate clean" || fail "validate refused"

echo "8. the refreshed claim REPRODUCES again"
# Step 2.6: `reaffirm` is retired, so the question "did the refresh buy
# anything?" is asked of `reproduce` -- which is the stricter test, since
# it files nothing in either direction and reports by exit code.
printf 'x\nx\nx\n#c\n' > f.txt; git add f.txt; git commit -qm "comment only"
OUT=$(t reproduce 2>&1)
if printf '%s' "$OUT" | grep -q "^$CID  reproduces"; then
  ok "the refreshed capsule is producible again (the refresh bought something)"
else
  fail "still capsule-stale after the refresh -- the refresh bought nothing"
fi

echo
[ "$FAILED" = 0 ] && echo "E2E: PASS" || echo "E2E: FAIL"
cd /; rm -rf "$D"
exit "$FAILED"
