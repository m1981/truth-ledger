#!/usr/bin/env bash
# fact-health: this repository's own citation tripwire. META-REPO ONLY —
# deliberately not shipped by the template (ADR-003 placement test: this
# encodes this repo's doc-corpus policy, so it stays consumer-side; the
# template repo is a consumer of its own discipline).
#
# One home per fact: a load-bearing fact appears in live prose as a
# ledger id, never as a restated count or contract. This sweep judges
# every tr- id cited in live markdown (README.md and docs/, excluding
# docs/archive/) by its ledger status — spec-health's judgment matrix,
# applied to the whole prose corpus instead of specs.
#
# ok: live | WARN: unverified, cannot_verify | FAIL: stale, diverged,
# retracted, missing. Zero-citation docs pass silently: prose is not
# obliged to cite, only forbidden to stand on dead citations.
set -euo pipefail
cd "$(dirname "$0")/.."

CLAIMS_JSON="$(python3 template/scripts/truth list --json)"
FILES="$(git ls-files 'README.md' 'docs/*.md' 'docs/**/*.md' | grep -v '^docs/archive/' | sort -u)"
export CLAIMS_JSON FILES

python3 - <<'PY'
import json, os, re, sys

claims = {r["id"]: r for r in json.loads(os.environ["CLAIMS_JSON"])}
BAD = {"stale", "diverged", "retracted"}
ID_RE = re.compile(r"\btr-[0-9a-f]{8}\b")

failures = warnings = cited = 0
for path in os.environ["FILES"].splitlines():
    if not path.strip():
        continue
    with open(path, encoding="utf-8") as f:
        ids = sorted(set(ID_RE.findall(f.read())))
    if not ids:
        continue
    print(path)
    for rid in ids:
        cited += 1
        rec = claims.get(rid)
        if rec is None:
            print(f"  FAIL  {rid}  missing from ledger")
            failures += 1
        elif rec["status"] in BAD:
            print(f"  FAIL  {rid}  {rec['status']} -- live prose stands on a dead fact")
            failures += 1
        elif rec["status"] in ("unverified", "cannot_verify"):
            print(f"  WARN  {rid}  {rec['status']} -- dispatch a verifier before leaning on it")
            warnings += 1
        else:
            print(f"  ok    {rid}  {rec['status']}")

print(f"\nfact-health: {failures} failure(s), {warnings} warning(s), {cited} citation(s)")
sys.exit(1 if failures else 0)
PY
