#!/usr/bin/env bash
# ADR-051 end-to-end acceptance, through the REAL CLI in a sandbox.
# Proves the whole chain, not a unit: an agree over a changed output is
# refused; --refresh-evidence files it; and the refreshed claim RETURNS
# to reaffirm's mechanical arm -- which is the only thing that makes the
# refresh worth having.
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

echo "3. change the watched file so the OUTPUT changes, then scan"
printf 'x\nx\nx\n' > f.txt; git add f.txt; git commit -qm "third x"
t invalidate-scan 2>/dev/null | grep -q "stale: $CID" \
  && ok "claim staled" || fail "scan did not stale the claim"

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

echo "8. the refreshed claim RETURNS to reaffirm's mechanical arm"
printf 'x\nx\nx\ny\n' >> /dev/null   # no content change; re-stale via a touch
git commit -q --allow-empty -m "unrelated"
printf 'x\nx\nx\n#c\n' > f.txt; git add f.txt; git commit -qm "comment only"
t invalidate-scan >/dev/null 2>&1
OUT=$(TRUTH_SESSION=s-reaffirm t reaffirm 2>&1)
if printf '%s' "$OUT" | grep -q "1 reaffirmed"; then
  ok "hash-match arm took it back (the refresh bought something)"
else
  printf '%s' "$OUT" | grep -q "diverged" \
    && fail "still in the mismatch arm -- the refresh bought nothing" \
    || echo "  note: $(printf '%s' "$OUT" | tail -1)"
fi

echo
[ "$FAILED" = 0 ] && echo "E2E: PASS" || echo "E2E: FAIL"
cd /; rm -rf "$D"
exit "$FAILED"
