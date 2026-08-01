#!/usr/bin/env bash
# fact-health: this repository's own citation tripwire. META-REPO ONLY —
# deliberately not shipped by the template (ADR-003 placement test: this
# encodes this repo's doc-corpus policy, so it stays consumer-side; the
# template repo is a consumer of its own discipline).
#
# One home per fact: a load-bearing fact appears in live prose as a
# ledger id, never as a restated count or contract. This sweep judges
# every tr- id cited in LIVE markdown by its ledger status — spec-health's
# judgment matrix, applied to the whole prose corpus instead of specs.
#
# ok: live | WARN: unverified, cannot_verify | FAIL: stale, diverged,
# retracted, missing. Zero-citation docs pass silently: prose is not
# obliged to cite, only forbidden to stand on dead citations.
#
# --- SCOPE, recalibrated 2026-08-01 -------------------------------------
# The sweep judges only what it can act on. Before this, 108 of 108
# failures were ~93% noise, and a tripwire nobody can act on is a
# tripwire nobody reads.
#
# 1. FROZEN REFERENCE is excluded. A record of a past event correctly
#    names the ids that were live THEN; re-judging it against today's
#    ledger is a category error, not a finding. docs/archive/ was already
#    excluded; docs/reviews/, docs/roadmap-v3.md and docs/growth-gate/ are
#    the same character (operator decision, 2026-08-01) — a review record,
#    a history log, and shelved designs. docs/field-notes* is excluded on
#    the SAME reasoning but was NOT in the operator's list: they are dated
#    session records whose citations narrate what was live during that
#    session ("successors tr-… and tr-…"). Flagged as an extension, not a
#    ruling — drop the line to put them back in scope.
#    Only prose that a reader is meant to ACT on today stays in scope.
#
# 2. FOREIGN ids are not ours to judge. A deployment (kuchnie) keeps its
#    own truth in its own repo; this ledger answers for itself only. Cite
#    another repo's record as `<repo>:tr-xxxxxxxx` and this sweep reports
#    it as INFO without judging it. That is what makes the MISSING class
#    mean something again: after this, a BARE tr- id absent from this
#    ledger is a genuine defect (a typo, or a citation of a record that
#    never existed here), not 25 cross-references to the pilot.
#
# 3. FENCED BLOCKS are skipped. A ``` block is illustrative or verbatim --
#    a sample CLI transcript, mermaid diagram source. Its ids are
#    fabricated examples (the tutorial's `truth claim` walkthrough prints
#    one) or decoration. This is not a preference: a tutorial CANNOT show
#    realistic output without inventing an id, so judging fences would
#    manufacture a permanent, unfixable failure -- the precise alarm
#    fatigue this recalibration exists to end. A fact's home is prose; a
#    fence is a rendering, not an assertion.
set -euo pipefail
cd "$(dirname "$0")/.."

CLAIMS_JSON="$(python3 template/scripts/truth list --json)"
# Frozen reference (see SCOPE above): excluded from the live corpus.
FILES="$(git ls-files 'README.md' 'docs/*.md' 'docs/**/*.md' \
  | grep -v '^docs/archive/' \
  | grep -v '^docs/reviews/' \
  | grep -v '^docs/growth-gate/' \
  | grep -v '^docs/roadmap-v3\.md$' \
  | grep -v '^docs/field-notes' \
  | sort -u)"
export CLAIMS_JSON FILES

python3 - <<'PY'
import json, os, re, sys

claims = {r["id"]: r for r in json.loads(os.environ["CLAIMS_JSON"])}
BAD = {"stale", "diverged", "retracted"}
# A citation is `tr-xxxxxxxx` (ours) or `<repo>:tr-xxxxxxxx` (foreign).
# The optional prefix is what keeps another repo's ids out of our verdict.
ID_RE = re.compile(r"\b(?:(?P<repo>[A-Za-z][\w.-]*):)?(?P<id>tr-[0-9a-f]{8})\b")

failures = warnings = cited = foreign = 0
for path in os.environ["FILES"].splitlines():
    if not path.strip():
        continue
    with open(path, encoding="utf-8") as f:
        prose, fenced = [], False
        for line in f:
            if line.lstrip().startswith("```"):
                fenced = not fenced
                continue
            if not fenced:
                prose.append(line)
    # key= is load-bearing: `repo` is None for our own ids, and a bare
    # tuple sort compares None against a str the moment one foreign
    # citation exists.
    hits = sorted({(m.group("repo"), m.group("id"))
                   for m in ID_RE.finditer("".join(prose))},
                  key=lambda t: (t[0] or "", t[1]))
    if not hits:
        continue
    print(path)
    for repo, rid in hits:
        if repo:
            foreign += 1
            print(f"  INFO  {repo}:{rid}  foreign ledger -- not judged here")
            continue
        cited += 1
        rec = claims.get(rid)
        if rec is None:
            print(f"  FAIL  {rid}  missing from ledger -- a bare id must be OURS; "
                  f"if it belongs to a deployment, cite it as <repo>:{rid}")
            failures += 1
        elif rec["status"] in BAD:
            print(f"  FAIL  {rid}  {rec['status']} -- live prose stands on a dead fact")
            failures += 1
        elif rec["status"] in ("unverified", "cannot_verify"):
            print(f"  WARN  {rid}  {rec['status']} -- dispatch a verifier before leaning on it")
            warnings += 1
        else:
            print(f"  ok    {rid}  {rec['status']}")

print(f"\nfact-health: {failures} failure(s), {warnings} warning(s), "
      f"{cited} citation(s), {foreign} foreign (not judged)")
sys.exit(1 if failures else 0)
PY
