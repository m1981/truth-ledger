#!/usr/bin/env bash
# spec-health: judge every feature spec by the ledger status of the ids it cites.
# Convention: .truth/README.md § Feature specs. A fact appears in a spec only
# as an id; this script is the tripwire that makes that rule pay rent.
#
# Judges cited claims by the ADR-001 matrix: live ok; unverified warns;
# cannot_verify fails P0 / warns otherwise; stale/diverged/retracted/
# disputed/missing fail. Cited issues: cancelled/missing fail. Every id cited ANYWHERE in a
# spec is tripwired (non-goals included) — refer by title to opt out.
# Zero-id specs WARN only (pre-convention legacy prose, wire when next touched).
#
# Ledger-derived JSON travels by FILE (see the CLAIMS_FILE note below). It used
# to travel by environment variable under a comment promising headroom until
# "ARG_MAX (~1MB on macOS)" — the wrong constant. The binding limit is
# MAX_ARG_STRLEN, 128 KiB on Linux, and this gate died at 142 KiB.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# J-018: ledger-derived JSON travels by FILE, never by environment variable.
# The header note above used to promise headroom until "ARG_MAX (~1MB on
# macOS)" and that measured the WRONG CONSTANT: the binding limit is
# MAX_ARG_STRLEN, 128 KiB on Linux (32 pages), 16x smaller. This gate died
# with `Argument list too long` at 223 claims / 4555 records -- loudly, but
# dead. Only fixed-size payloads (the vocabulary) may stay in the env.
CLAIMS_FILE="$(mktemp)"
ISSUES_FILE="$(mktemp)"
trap 'rm -f "$CLAIMS_FILE" "$ISSUES_FILE"' EXIT
scripts/truth list --json > "$CLAIMS_FILE"
# P2 contract layer: the citation-blocking set comes from the CLI at
# runtime (CITATION_BAD via `truth vocab`), never hand-copied -- the R1
# `disputed` drift class is structurally impossible. Fail LOUD: a sweep
# run against a guessed vocabulary would be the drift re-armed (F1 rule).
if ! VOCAB_JSON="$(scripts/truth vocab --json)"; then
  echo "spec-health: 'truth vocab --json' failed -- the citation-blocking set is unavailable; refusing to sweep with a guessed vocabulary (exit 2: environment, not governance)" >&2
  exit 2
fi
if ! scripts/truth issues --json > "$ISSUES_FILE" 2>/dev/null; then
  echo "spec-health: 'truth issues --json' failed; treating issue records as absent (wk- ids will report missing)" >&2
  printf '[]' > "$ISSUES_FILE"
fi
SPEC_FILES="$(find . \( -path ./attic -o -path "*/node_modules" -o -path "*/.venv" -o -name archive \) -prune \
                   -o -type f -path "*docs/specs/*.md" -print | sort)"

export CLAIMS_FILE VOCAB_JSON ISSUES_FILE SPEC_FILES

python3 - <<'PY'
import json, os, re, sys

with open(os.environ["CLAIMS_FILE"], encoding="utf-8") as _cf:
    claims = {r["id"]: r for r in json.load(_cf)}
with open(os.environ["ISSUES_FILE"], encoding="utf-8") as _if:
    issues = {r["id"]: r for r in json.load(_if)}

# Sourced from the CLI's own CITATION_BAD (truth vocab --json), fetched
# above -- one contract, consumed at runtime (P2 contract layer).
CLAIM_BAD = set(json.loads(os.environ["VOCAB_JSON"])["citation_bad"])
ID_RE = re.compile(r"\b(?:tr|wk)-[0-9a-f]{8}\b")

failures = warnings = 0
specs = [p for p in os.environ["SPEC_FILES"].splitlines() if p.strip()]
if not specs:
    print("spec-health: no spec files found under */docs/specs/")
    sys.exit(0)

for path in specs:
    with open(path, encoding="utf-8") as f:
        ids = sorted(set(ID_RE.findall(f.read())))
    print(f"{path}")
    if not ids:
        print("  WARN  no ledger ids cited (unwired prose -- wire per the spec convention, .truth/README.md § Feature specs)")
        warnings += 1
        continue
    spec_trs = [i for i in ids if i.startswith("tr-")]
    spec_wks = [i for i in ids if i.startswith("wk-")]
    for rid in spec_trs:
        rec = claims.get(rid)
        if rec is None:
            print(f"  FAIL  {rid}  missing from ledger")
            failures += 1
            continue
        status, tier = rec["status"], rec.get("tier", "P1")
        if status in CLAIM_BAD:
            print(f"  FAIL  {rid}  {status} -- spec stands on a dead fact; renegotiate before coding")
            failures += 1
        elif status == "cannot_verify":
            if tier == "P0":
                print(f"  FAIL  {rid}  cannot_verify on a P0 fact (ADR-001: blocks)")
                failures += 1
            else:
                print(f"  WARN  {rid}  cannot_verify ({tier}) -- passes, but the ground is soft")
                warnings += 1
        elif status == "unverified":
            print(f"  WARN  {rid}  unverified -- dispatch a verifier before leaning on it")
            warnings += 1
        else:
            print(f"  ok    {rid}  {status}")
    covered = set()
    for rid in spec_wks:
        rec = issues.get(rid)
        if rec is None:
            print(f"  FAIL  {rid}  missing from ledger")
            failures += 1
            continue
        covered.update(rec.get("premises", []))
        status = rec["status"]
        if status == "cancelled":
            print(f"  FAIL  {rid}  cancelled -- spec cites a dead intention")
            failures += 1
        else:
            print(f"  ok    {rid}  {status}")
    # Ground truths not carried as premises on any cited issue are invisible
    # to `truth ready` -- only this script would catch their death.
    if spec_wks:
        for rid in sorted(set(spec_trs) - covered):
            if rid in claims:
                print(f"  WARN  {rid}  cited as ground truth but premise of no cited issue -- `truth ready` won't protect it (truth premise <wk-id> {rid})")
                warnings += 1

print(f"\nspec-health: {failures} failure(s), {warnings} warning(s) across {len(specs)} spec(s)")
sys.exit(1 if failures else 0)
PY
