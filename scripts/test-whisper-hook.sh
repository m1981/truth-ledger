#!/usr/bin/env bash
# Regression gate for the consumer-side pre-edit whisper hook
# (scripts/truth-whisper.py, ADR-005). The hook is deliberately NOT in
# the template canary (ADR-003 rule 2: consumer policy), so it needs its
# own gate here. Covers the two v0.6.2/#11 fixes:
#   - worktree fail-open: in a git worktree root/.git is a FILE; the hook
#     must still emit allow+whisper and not crash (ADR-005: whisper fails
#     OPEN, visibly), with the seen-cache resolved via git, not a
#     hardcoded root/.git join.
#   - deny wording: the deny reason must name a human actor and must NOT
#     teach a bypass ritual (the S2 trial finding).
set -u
HOOK="$(cd "$(dirname "$0")" && pwd)/truth-whisper.py"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# Unique per-run nonce: the hook's fatigue cache dedups on (session, file,
# ledger hash), so a fixed session id would suppress the whisper on the
# second run and the gate would flap. A fresh nonce keeps each run honest.
NONCE="$$-${RANDOM}"
PASS=0; FAIL=0
ok()   { PASS=$((PASS+1)); printf '  CAUGHT: %s\n' "$*"; }
bad()  { FAIL=$((FAIL+1)); printf '  MISSED: %s\n' "$*"; }

# A path the ledger actually watches, so `truth impact` returns exit 3.
WATCHED="template/scripts/truth"

say() { printf '%s\n' "$*"; }

say "CASE 1 (deny stage): a deny-listed path is blocked, human-actor voice, no bypass ritual"
OUT=$(printf '{"session_id":"s-test","tool_input":{"file_path":"%s/docs/archive/x.md"}}' "$ROOT" \
      | python3 "$HOOK")
if printf '%s' "$OUT" | grep -q '"permissionDecision": "deny"' \
   && printf '%s' "$OUT" | grep -q 'human must deliberately lift the freeze' \
   && ! printf '%s' "$OUT" | grep -q 'changed first'; then
  ok "archive edit denied with human-actor reason, no bypass instruction"
else
  bad "deny reason wrong: $(printf '%s' "$OUT" | head -c 200)"
fi

say "CASE 2 (whisper stage, MAIN worktree): watched path emits allow+whisper"
OUT=$(printf '{"session_id":"s-main-%s","tool_input":{"file_path":"%s/%s"}}' "$NONCE" "$ROOT" "$WATCHED" \
      | python3 "$HOOK")
if printf '%s' "$OUT" | grep -q '"permissionDecision": "allow"' \
   && printf '%s' "$OUT" | grep -q 'truth-ledger whisper'; then
  ok "watched path in main tree whispered"
else
  bad "no whisper in main tree: $(printf '%s' "$OUT" | head -c 200)"
fi

say "CASE 3 (whisper stage, WORKTREE): root/.git is a file; hook must NOT crash and still whisper"
WT=$(mktemp -d)/wt
if git -C "$ROOT" worktree add -q --detach "$WT" 2>/dev/null; then
  WT="$(cd "$WT" && pwd -P)"  # canonicalize (macOS /var->/private/var) so the payload path matches git's root
  # Run FROM the worktree cwd -- that is how the harness invokes the hook,
  # and it is what makes `git rev-parse --show-toplevel` resolve to the
  # worktree (whose .git is a FILE, the crash condition being tested).
  # Fresh session id so the fatigue cache does not suppress the whisper.
  OUT=$(cd "$WT" && printf '{"session_id":"s-wt-%s","tool_input":{"file_path":"%s/%s"}}' "$NONCE" "$WT" "$WATCHED" \
        | python3 "$HOOK" 2>"$ROOT/wt.err"); RC=$?
  if [ "$RC" -eq 0 ] && printf '%s' "$OUT" | grep -q 'truth-ledger whisper'; then
    ok "worktree edit whispered without crashing (fail-open preserved)"
  else
    bad "worktree hook crashed or stayed silent (rc=$RC): $(printf '%s' "$OUT" | head -c 120) err=$(head -c 120 wt.err)"
  fi
  # cache must have landed via git --git-path, not under the worktree's .git FILE
  if git -C "$WT" rev-parse --git-path truth-whisper.seen >/dev/null 2>&1; then
    ok "seen-cache path resolves via git in the worktree"
  else
    bad "git could not resolve the cache path in the worktree"
  fi
  git -C "$ROOT" worktree remove --force "$WT" 2>/dev/null
  rm -f wt.err
else
  bad "could not create a worktree to test (git worktree add failed)"
fi

printf '\nwhisper-hook gate: %d caught, %d missed\n' "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ] && echo "ALL WHISPER CASES CAUGHT." || exit 1
