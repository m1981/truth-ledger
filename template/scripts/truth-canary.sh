#!/usr/bin/env bash
# truth-canary.sh v0.4 -- seeded-fault acceptance suite (22 checks: seeded faults + adapter seam).
set -u
HERE="$(cd "$(dirname "$0")" && pwd)"
PASS=0; FAIL=0
say()  { printf '%s\n' "$*"; }
ok()   { PASS=$((PASS+1)); say "  CAUGHT: $*"; }
miss() { FAIL=$((FAIL+1)); say "  MISSED: $*"; }

TMP1="$(mktemp -d)"; TMP2="$(mktemp -d)"; TMP3="$(mktemp -d)"
cleanup() { rm -rf "$TMP1" "$TMP2" "$TMP3"; }
trap cleanup EXIT

mkrepo() {
  cd "$1"
  git init -q -b main .
  git config user.email canary@truth.local
  git config user.name  truth-canary
  mkdir -p scripts .truth prompts
  touch .truth/claims.jsonl
  cp "$HERE/truth" scripts/truth
  cp "$HERE/check-truth.sh" scripts/check-truth.sh
  chmod +x scripts/truth scripts/check-truth.sh
}
T="python3 scripts/truth"
export TRUTH_ACTOR=canary TRUTH_SESSION=s-canary

# ======================================================= sandbox 1 (main)
mkrepo "$TMP1"
echo "hello" > watched.txt
echo "v1"    > fabricated.txt
printf 'verifier header\n---\nVERIFIER BODY\n' > prompts/truth-verifier.md
git add -A && git commit -qm "canary: init"

say "DOCTOR (G4): must FAIL on an unwired repo, PASS after wiring"
if $T doctor >/dev/null 2>&1; then
  miss "doctor passed a repo with no hooks, no gitattributes, no discovery"
else
  ok "doctor failed the unwired repo"
fi
echo ".truth/claims.jsonl merge=union" >> .gitattributes
printf '#!/usr/bin/env bash\nexec bash scripts/check-truth.sh\n' > .git/hooks/pre-commit
printf '#!/usr/bin/env bash\npython3 scripts/truth invalidate-scan --quiet\n' > .git/hooks/post-merge
chmod +x .git/hooks/pre-commit .git/hooks/post-merge
printf '# Agents\nTruth ledger: use scripts/truth (see .truth/README.md)\n' > AGENTS.md
git add -A && git commit -qm "canary: wire installation" --no-verify
if $T doctor >/dev/null 2>&1; then
  ok "doctor passed the wired repo"
else
  miss "doctor failed a correctly wired repo"; $T doctor || true
fi

say "FAULT B (INV-C): commit touching evidence paths must mark the claim stale"
CID_B=$($T claim "watched.txt says hello" --class VERIFIED \
        --evidence-cmd "cat watched.txt" --paths "watched.txt" --tier P0)
$T verdict "$CID_B" --recheck >/dev/null
git add .truth/claims.jsonl && git commit -qm "canary: claim B" --no-verify
echo "changed" >> watched.txt
git add watched.txt && git commit -qm "canary: mutate evidence" --no-verify
$T invalidate-scan --quiet
if $T list --stale --json | grep -q "$CID_B"; then
  ok "claim $CID_B stale after evidence path changed"
else
  miss "claim $CID_B still trusted after its evidence changed"
fi

say "FAULT C (T1): recheck must diverge when reality no longer matches"
CID_C=$($T claim "fabricated.txt says v1" --class VERIFIED \
        --evidence-cmd "cat fabricated.txt" --paths "fabricated.txt" --tier P1)
echo "v2" > fabricated.txt
if $T verdict "$CID_C" --recheck | grep -q diverge; then
  ok "recheck flagged hash mismatch on $CID_C"
else
  miss "recheck accepted stale evidence on $CID_C"
fi

say "FAULT D (G10): claim past its ttl_days must expire to stale"
CID_D=$(TRUTH_NOW="2026-06-01T00:00:00+00:00" $T claim \
        "external API allows 100 req/min" --class INFERRED \
        --basis "vendor docs read 2026-06-01" --ttl-days 7 --tier P1)
$T invalidate-scan --quiet
if $T list --stale --json | grep -q "$CID_D"; then
  ok "claim $CID_D expired after ttl elapsed"
else
  miss "ttl_days is still a dead field: $CID_D outlived its ttl"
fi

say "FAULT G (G6): nondeterministic evidence command must be refused"
if $T claim "the clock ticks" --class VERIFIED \
     --evidence-cmd "date +%s%N" --paths "watched.txt" --tier P2 2>/dev/null; then
  miss "intake accepted nondeterministic evidence"
else
  ok "intake refused nondeterministic evidence"
fi

say "FAULT H (G12): a verdict after retraction must not resurrect the claim"
CID_H=$($T claim "this claim is simply wrong" --tier P2)
TRUTH_HUMAN=1 $T verdict "$CID_H" retracted --basis "human: factually wrong, tombstoned" >/dev/null
if $T verdict "$CID_H" agree --basis "resurrection attempt" >/dev/null 2>&1; then
  miss "tool accepted a verdict on a retracted claim"
else
  ok "tool refused a verdict on retracted $CID_H"
fi
if $T list --retracted --json | grep -q "$CID_H" && \
   ! $T list --live --json | grep -q "$CID_H"; then
  ok "fold holds $CID_H as retracted (terminal)"
else
  miss "retracted claim $CID_H changed status"
fi

say "FAULT I (G8): near-duplicate of an active claim must be refused"
$T claim "the payments module handles all currency conversion logic" --tier P2 >/dev/null
if $T claim "the payments module handles currency conversion" --tier P2 2>/dev/null; then
  miss "intake accepted a near-duplicate active claim"
else
  ok "intake refused the near-duplicate"
fi
if DUP=$($T claim "the payments module handles currency conversion" \
         --tier P2 --duplicate-ok 2>/dev/null); then
  ok "--duplicate-ok override works ($DUP)"
else
  miss "--duplicate-ok override rejected a legitimate refile"
fi

say "FAULT J (ADR-001): issue premised on a stale claim must be HELD"
cat > bd <<'EOF'
#!/usr/bin/env bash
if [ "${1:-}" = "ready" ]; then
  echo '[{"id":"bd-x1","title":"issue on stale premise"},{"id":"bd-x2","title":"issue on live premise"}]'
fi
EOF
chmod +x bd
CID_L=$($T claim "watched.txt now says hello changed" --class VERIFIED \
        --evidence-cmd "cat watched.txt" --paths "watched.txt" --tier P1 --duplicate-ok)
$T verdict "$CID_L" --recheck >/dev/null
$T premise bd-x1 "$CID_B" >/dev/null
$T premise bd-x2 "$CID_L" >/dev/null
READY_OUT=$(PATH="$PWD:$PATH" $T ready)
if echo "$READY_OUT" | grep -q "^HELD bd-x1" && echo "$READY_OUT" | grep -q "^bd-x2"; then
  ok "bd-x1 held on stale premise; bd-x2 passed on live premise"
else
  miss "ready join wrong: $READY_OUT"
fi
# v0.4.1 -- the adapter seam is a property, not a promise:
READY_ENV=$(PATH="/usr/bin:/bin" TRUTH_TRACKER_CMD="$PWD/bd ready --json" $T ready)
if echo "$READY_ENV" | grep -q "^HELD bd-x1" && echo "$READY_ENV" | grep -q "^bd-x2"; then
  ok "TRUTH_TRACKER_CMD adapter joins identically (no bd on PATH)"
else
  miss "TRUTH_TRACKER_CMD adapter wrong: $READY_ENV"
fi
READY_STDIN=$(./bd ready | $T ready --stdin)
if echo "$READY_STDIN" | grep -q "^HELD bd-x1" && echo "$READY_STDIN" | grep -q "^bd-x2"; then
  ok "--stdin adapter joins identically (tracker-agnostic pipe)"
else
  miss "--stdin adapter wrong: $READY_STDIN"
fi
if PATH="/usr/bin:/bin" TRUTH_TRACKER_CMD="definitely-not-a-tracker --json" $T ready >/dev/null 2>&1; then
  miss "ready succeeded with a nonexistent tracker command"
else
  if PATH="/usr/bin:/bin" TRUTH_TRACKER_CMD="definitely-not-a-tracker --json" $T ready 2>&1 | grep -q "Traceback"; then
    miss "missing tracker produced a raw traceback, not guidance"
  else
    ok "missing tracker degrades with guidance, no traceback"
  fi
fi

# ---- FAULT K (v0.4): duplicate-id append must not resurrect a tombstone ----
say "FAULT K (INV-G'): appending a duplicate claim id must not reset status"
python3 - "$CID_H" <<'PYEOF'
import json, sys
rec={"id":sys.argv[1],"kind":"claim","actor":"agent-x","session":"s-evil",
     "ts":"2099-01-01T00:00:00+00:00",
     "payload":{"text":"resurrection via duplicate id","evidence_class":"UNVERIFIED",
                "cost_tier":"P0","ttl_days":None,"evidence_paths":[]}}
open(".truth/claims.jsonl","a").write(json.dumps(rec,sort_keys=True)+"\n")
PYEOF
if $T list --retracted --json | grep -q "$CID_H" && \
   ! $T list --unverified --json | grep -q "$CID_H"; then
  ok "duplicate-id append ignored; $CID_H stays retracted"
else
  miss "duplicate-id append resurrected retracted $CID_H"
fi

# ---- FAULT L (v0.4): re-verification must survive the next scan ----------
say "FAULT L: re-verified claim must stay live across a subsequent scan"
CID_R=$($T claim "watched.txt has multiple lines" --class VERIFIED \
        --evidence-cmd "wc -l < watched.txt" --paths "watched.txt" --tier P1 --duplicate-ok)
echo "another line" >> watched.txt
git add watched.txt && git commit -qm "canary: touch evidence again" --no-verify
$T invalidate-scan --quiet
$T verdict "$CID_R" agree --basis "human re-verified at new HEAD" >/dev/null
$T invalidate-scan --quiet
if $T list --live --json | grep -q "$CID_R"; then
  ok "re-verified $CID_R stayed live (anchor advanced)"
else
  miss "re-verified $CID_R re-staled on the frozen anchor"
fi

# ---- FAULT M (v0.4): retraction without human confirmation refused --------
say "FAULT M (G12 enforced): retraction without TRUTH_HUMAN=1 must be refused"
CID_M=$($T claim "a claim a verifier wants dead" --tier P2)
if $T verdict "$CID_M" retracted --basis "verifier overreach" >/dev/null 2>&1; then
  miss "non-human retraction accepted"
else
  ok "retraction refused without TRUTH_HUMAN=1"
fi
if TRUTH_HUMAN=1 $T verdict "$CID_M" retracted --basis "human confirms" >/dev/null 2>&1; then
  ok "human-confirmed retraction accepted"
else
  miss "human-confirmed retraction refused"
fi

# ---- FAULT N (v0.4): mid-file insertion must block the commit -------------
say "FAULT N (INV-A strict): mid-file insertion (pure addition) must be blocked"
git add -A && git commit -qm "canary: settle before insertion" --no-verify
python3 - <<'PYEOF'
import json
lines=open(".truth/claims.jsonl").readlines()
forged={"id":"tr-deadbeef","kind":"claim","actor":"agent-x","session":"s-evil",
        "ts":"2020-01-01T00:00:00+00:00",
        "payload":{"text":"forged backdated record","evidence_class":"UNVERIFIED",
                   "cost_tier":"P2","ttl_days":None,"evidence_paths":[]}}
lines.insert(0, json.dumps(forged,sort_keys=True)+"\n")
open(".truth/claims.jsonl","w").writelines(lines)
PYEOF
git add .truth/claims.jsonl
if bash scripts/check-truth.sh >/dev/null 2>&1; then
  miss "gate accepted a mid-file insertion (additions-only tampering)"
else
  ok "gate blocked the mid-file insertion"
fi
git checkout -q -- .truth/claims.jsonl

say "FAULT A (INV-A): mutating a historical ledger line must block the commit"
git add -A && git commit -qm "canary: settle ledger" --no-verify
sed -i '1s/claim/CLAIM_TAMPERED/' .truth/claims.jsonl
git add .truth/claims.jsonl
if bash scripts/check-truth.sh >/dev/null 2>&1; then
  miss "check-truth.sh allowed a mutated historical record"
else
  ok "check-truth.sh blocked the tampered ledger"
fi
git checkout -q -- .truth/claims.jsonl

# ======================================================= sandbox 2 (G1)
say "FAULT F (G1): VERIFIED claim in a zero-commit repo must be refused"
mkrepo "$TMP2"
echo x > f.txt
if $T claim "f.txt exists" --class VERIFIED --evidence-cmd "cat f.txt" \
     --paths "f.txt" --tier P0 2>/dev/null; then
  miss "intake anchored a claim in a repo with no commits"
else
  ok "intake refused: no commits, no anchor"
fi

# ======================================================= sandbox 3 (G14)
say "FAULT E (G14): erased anchor commit must invalidate, with reason"
mkrepo "$TMP3"
echo data > g.txt
git add -A && git commit -qm "canary: init"
CID_E=$($T claim "g.txt says data" --class VERIFIED \
        --evidence-cmd "cat g.txt" --paths "g.txt" --tier P0)
$T verdict "$CID_E" --recheck >/dev/null
git checkout -q --orphan rewritten
git add -A && git commit -qm "canary: history rewritten"
git branch -D main -q
git reflog expire --expire=now --expire-unreachable=now --all
git gc --prune=now -q
$T invalidate-scan --quiet
if $T list --stale --json | grep -q "$CID_E" && \
   grep -q "anchor unreachable" .truth/claims.jsonl; then
  ok "claim $CID_E stale with reason 'anchor unreachable'"
else
  miss "history rewrite left $CID_E trusted or unexplained"
fi

say ""
say "canary result: $PASS caught, $FAIL missed"
if [ "$FAIL" -gt 0 ]; then
  say "CANARY FAILED -- the immune system has a hole."
  exit 1
fi
say "ALL CANARIES CAUGHT."
