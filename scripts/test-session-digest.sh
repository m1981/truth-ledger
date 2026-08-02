#!/usr/bin/env bash
# Regression gate for the consumer-side session-start digest
# (scripts/truth-session-digest.py, FS-4). META-REPO ONLY, like the
# whisper gate: harness wiring is consumer policy (ADR-003 rule 2), so
# the template canary cannot carry these arms. Closes R11/L4-F6: the
# digest had zero regression gate, and a failing CLI degraded to an
# empty digest with NO stderr line -- the doc-vs-code drift class this
# repo treats as a defect. Three arms: the happy path emits, a dead CLI
# is loud but still exit 0 (advisory machinery fails OPEN, visibly),
# and an empty ledger stays silent (silence is the default).
set -u
DIGEST="$(cd "$(dirname "$0")" && pwd)/truth-session-digest.py"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PASS=0; FAIL=0
ok()  { PASS=$((PASS+1)); printf '  CAUGHT: %s\n' "$*"; }
bad() { FAIL=$((FAIL+1)); printf '  MISSED: %s\n' "$*"; }
say() { printf '%s\n' "$*"; }

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

say "CASE 1 (happy path): this repo's ledger yields a digest with content"
OUT=$(cd "$ROOT" && python3 "$DIGEST" 2>"$TMP/c1.err"); RC=$?
if [ "$RC" -eq 0 ] && printf '%s' "$OUT" | grep -q "truth-ledger digest" \
   && printf '%s' "$OUT" | grep -qE "^  (ATTENTION|LIVE) "; then
  ok "digest emitted header plus at least one ATTENTION/LIVE line (rc=$RC)"
else
  bad "happy path wrong (rc=$RC): $(printf '%s' "$OUT" | head -c 160) err=$(head -c 120 "$TMP/c1.err")"
fi

# --- sandbox factory: a git repo with scripts/truth and a seeded ledger --
mksb() {  # mksb <dir>
  mkdir -p "$1/scripts" "$1/.truth"
  git -C "$1" init -q -b main .
  git -C "$1" config user.email sd@test.local
  git -C "$1" config user.name sd-test
  cp "$ROOT/template/scripts/truth" "$1/scripts/truth"
  cp -R "$ROOT/template/truthlib" "$1/truthlib"  # ADR-044: entry resolves ../truthlib
}

say "CASE 2 (dead CLI): corrupt ledger -> exit 0, empty stdout, ONE loud stderr line"
SB1="$TMP/dead"
mksb "$SB1"
echo 'this is not json' > "$SB1/.truth/claims.jsonl"
if (cd "$SB1" && python3 scripts/truth queue --json >/dev/null 2>&1); then
  bad "fault injection failed: the CLI still serves queue --json over a corrupt ledger"
else
  OUT=$(cd "$SB1" && python3 "$DIGEST" 2>"$TMP/c2.err"); RC=$?
  ERRN=$(grep -c . "$TMP/c2.err")
  if [ "$RC" -eq 0 ] && [ -z "$OUT" ] && [ "$ERRN" -eq 1 ] \
     && grep -q "truth session digest unavailable" "$TMP/c2.err"; then
    ok "dead CLI: exit 0, empty digest, one stderr line naming the failure"
  else
    bad "dead-CLI degradation wrong (rc=$RC, stderr lines=$ERRN): $(head -c 160 "$TMP/c2.err")"
  fi
fi

say "CASE 3 (empty ledger): exit 0, empty stdout, empty stderr -- silence is the default"
SB2="$TMP/empty"
mksb "$SB2"
: > "$SB2/.truth/claims.jsonl"
OUT=$(cd "$SB2" && python3 "$DIGEST" 2>"$TMP/c3.err"); RC=$?
if [ "$RC" -eq 0 ] && [ -z "$OUT" ] && [ ! -s "$TMP/c3.err" ]; then
  ok "empty ledger produced nothing on either stream at exit 0"
else
  bad "empty-ledger silence wrong (rc=$RC): out=$(printf '%s' "$OUT" | head -c 80) err=$(head -c 80 "$TMP/c3.err")"
fi

printf '\nsession-digest gate: %d caught, %d missed\n' "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ] && echo "ALL SESSION-DIGEST CASES CAUGHT." || exit 1
