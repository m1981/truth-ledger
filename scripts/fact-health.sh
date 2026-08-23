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
# retracted, disputed, missing. Zero-citation docs pass silently: prose is
# not obliged to cite, only forbidden to stand on dead citations.
#
# --- SCOPE, recalibrated 2026-08-01 -------------------------------------
# The sweep judges only what it can act on. Before this, 108 of 108
# failures were ~93% noise, and a tripwire nobody can act on is a
# tripwire nobody reads.
#
# 1. FROZEN REFERENCE is excluded. A record of a past event correctly
#    names the ids that were live THEN; re-judging it against today's
#    ledger is a category error, not a finding. docs/archive/ was already
#    excluded; docs/reviews/ and docs/roadmap-v3.md are the same character
#    (operator decision, 2026-08-01) — a review record and a history log.
#    docs/growth-gate/ was excluded on that ruling and RE-INCLUDED the same
#    day: its README and spec-coverage-manifests.md declare "Status: PILOT
#    LIVE" and three in-scope docs name the latter a source of truth, so it
#    is not a record of the past. The shelved designs beside them are not
#    frozen either — a design awaiting a trigger is an INSTRUCTION, and a
#    dead citation in one is worse than in live prose because nobody reads
#    it until the day they build from it. docs/field-notes* is excluded on
#    the SAME reasoning but was NOT in the operator's list: they are dated
#    session records whose citations narrate what was live during that
#    session ("successors tr-… and tr-…"). Flagged as an extension, not a
#    ruling — drop the line to put them back in scope.
#    docs/refactor/01-JOURNAL.md joins them on the SAME reasoning and is
#    called out because it is the newest and the least obvious: it is an
#    append-only record of a refactor, and it cites the ids it RETRACTED --
#    naming them is the point, exactly as the field notes name theirs. Its
#    sibling docs/refactor/00-RUNBOOK.md deliberately STAYS in scope: a
#    runbook is an instruction a reader acts on today, so a dead citation
#    in one is a real defect. (That distinction was not theoretical: on
#    2026-08-17 the runbook duplicated a retraction table out of the
#    journal and this sweep blocked the push for it.)
#    docs/diagnosis-2026-08/ joins the excluded set on the same reasoning,
#    2026-08-17. It is a DATED diagnostic dossier -- its own 00-STATE.md
#    header stamps the measurement ("Ostatni pomiar: <date>, HEAD <sha>")
#    and disclaims managing work ("nie zarzadza praca, nie duplikuje
#    statusu"); it answers one decision question with evidence. Its
#    citations narrate what was live AT DIAGNOSIS, and two of them name
#    tr-a8bda1a1 precisely to argue that it was false and should be
#    retracted -- which then happened. Judging that record against
#    today's ledger flags the dossier for having been RIGHT.
#    Flagged as an EXTENSION, not a ruling -- drop the line to put it back
#    in scope. Note the asymmetry that makes this safe to get wrong in
#    only one direction: if a future docs/diagnosis-*/ file turns into an
#    instruction, it must come back into scope, and the test is the same
#    one used above -- is a reader meant to ACT on it today?
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

# J-018: ledger-derived JSON travels by FILE, never by environment variable.
# `truth list --json` crossed MAX_ARG_STRLEN -- 128 KiB on Linux (32 pages),
# NOT the ~1 MB ARG_MAX the sibling comment in spec-health.sh used to cite --
# at 223 claims / 4555 records. execve then refuses the WHOLE environment
# with `Argument list too long` and the sweep is dead, not degraded. Only
# fixed-size payloads (the vocabulary) may stay in the env.
CLAIMS_FILE="$(mktemp)"
trap 'rm -f "$CLAIMS_FILE"' EXIT
python3 template/scripts/truth list --json > "$CLAIMS_FILE"
# P2 contract layer: the blocking set is the CLI's own CITATION_BAD
# (truth vocab --json), fetched at runtime -- never hand-copied (the R1
# `disputed` drift class). Fail LOUD: sweeping with a guessed vocabulary
# would be the drift re-armed (F1 rule).
if ! VOCAB_JSON="$(python3 template/scripts/truth vocab --json)"; then
  echo "fact-health: 'truth vocab --json' failed -- the citation-blocking set is unavailable; refusing to sweep with a guessed vocabulary (exit 2: environment, not governance)" >&2
  exit 2
fi
# --- the corpus, in LOCKSTEP by construction (wk-1d000ad4) ---------------
# INCLUSION comes from .truth/citation-scope, EXCLUSION stays here. That
# split is the operator's ruling and it follows from SI-1: the scope file
# refuses lines beginning ':', '-' or '!', so exclusions cannot be spelled
# there at all. Inclusion states which prose the project stands behind --
# shared with the ADR-036 retraction gate. Exclusion is a property of THIS
# sweep: which of that prose is frozen reference and so cannot go stale.
#
# Until 2026-08-23 the inclusion list was hardcoded here while the scope
# file's own header called the two "kept in LOCKSTEP". They were not: the
# sweep saw 31 files, the gate 21, and the ten in between could be cited
# by a document, block nothing at retraction, then redden the sweep. That
# happened on 2026-08-22. A claim about consistency that nothing checked,
# in the file that says "an armed-looking gate that checks nothing is
# worse than no gate".
#
# The globs are read through the CLI's OWN loader, never re-parsed here: a
# second implementation of the comment/blank/SI-1 rules is the drift this
# repo refuses, and it would drift silently because both copies would look
# right in isolation. chr(10) rather than a backslash escape so this block
# survives being edited through a shell heredoc.
SCOPE_GLOBS="$(python3 -c '
import sys
sys.path.insert(0, "template")
from truthlib.shellio import load_citation_scope
globs, source, err = load_citation_scope()
if err:
    sys.stderr.write(err + chr(10))
    raise SystemExit(2)
if source != "file":
    sys.stderr.write("fact-health: .truth/citation-scope is " + source +
                     " -- the corpus would be EMPTY and the sweep would "
                     "report health having read nothing (exit 2: "
                     "environment, not governance)" + chr(10))
    raise SystemExit(2)
print(chr(10).join(globs))
')" || exit 2

# Frozen reference (see SCOPE above): excluded from the live corpus.
FILES="$(printf '%s\n' "$SCOPE_GLOBS" \
  | while IFS= read -r _g; do [ -n "$_g" ] && git ls-files -- "$_g"; done \
  | grep -v '^docs/archive/' \
  | grep -v '^docs/reviews/' \
  | grep -v '^docs/roadmap-v3\.md$' \
  | grep -v '^docs/field-notes' \
  | grep -v '^docs/refactor/01-JOURNAL\.md$' \
  | grep -v '^docs/diagnosis-' \
  | sort -u)"
export CLAIMS_FILE VOCAB_JSON FILES

python3 - <<'PY'
import json, os, re, sys

with open(os.environ["CLAIMS_FILE"], encoding="utf-8") as _cf:
    claims = {r["id"]: r for r in json.load(_cf)}
# Sourced from the CLI's own CITATION_BAD (truth vocab --json), fetched
# above -- one contract, consumed at runtime (P2 contract layer).
BAD = set(json.loads(os.environ["VOCAB_JSON"])["citation_bad"])
# Known deployments. An ALLOWLIST, not a free prefix: the first cut let
# any word before a colon mean "foreign", so `successor:tr-...` or a
# typo'd `kuchnia:` silently escaped judgment, and a local dead id in a
# table cell could be spoofed foreign by whatever word preceded it.
DEPLOYMENTS = {"kuchnie", "sdk"}
ID_RE = re.compile(r"(?:(?P<repo>[A-Za-z][\w.-]*):)?\b(?P<id>tr-[0-9a-f]{8})\b")
# A near-miss looks like a citation but cannot be one: wrong length, or
# uppercase hex. Silently unmatched before -- a dropped character made a
# citation VANISH from the sweep rather than fail it.
NEARMISS_RE = re.compile(r"\btr-(?![0-9a-f]{8}\b)[0-9a-fA-F]{4,12}\b")

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
    if fenced:
        # An odd fence count leaves the toggle stuck open and every
        # citation below it silently skipped. Never fail quietly on a
        # sensor that has stopped sensing (the F1 audit rule).
        print(f"{path}\n  FAIL  unbalanced ``` fence -- the scan ended inside "
              "a block, so citations after it were NOT swept")
        failures += 1
        continue
    # key= is load-bearing: `repo` is None for our own ids, and a bare
    # tuple sort compares None against a str the moment one foreign
    # citation exists.
    hits = sorted({(m.group("repo"), m.group("id"))
                   for m in ID_RE.finditer("".join(prose))},
                  key=lambda t: (t[0] or "", t[1]))
    # Near-misses gathered BEFORE the skip: a doc whose ONLY citation is
    # a malformed id used to fall through `if not hits: continue` and the
    # near-miss vanished from the sweep -- the precise disappearance this
    # class exists to catch (found by test-fact-health.sh CASE 5).
    near = sorted({m.group(0) for m in NEARMISS_RE.finditer("".join(prose))})
    if not hits and not near:
        continue
    print(path)
    for repo, rid in hits:
        if repo in DEPLOYMENTS:
            foreign += 1
            print(f"  INFO  {repo}:{rid}  foreign ledger -- not judged here")
            continue
        if repo:
            print(f"  FAIL  {repo}:{rid}  unknown prefix {repo!r} -- a foreign "
                  f"citation must name a known deployment ({', '.join(sorted(DEPLOYMENTS))}); "
                  "an unrecognized prefix would silently escape judgment")
            failures += 1
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
    for m in near:
        print(f"  FAIL  {m}  malformed id -- a citation is tr- plus exactly 8 "
              "lowercase hex; this one would otherwise vanish from the sweep")
        failures += 1

print(f"\nfact-health: {failures} failure(s), {warnings} warning(s), "
      f"{cited} citation(s), {foreign} foreign (not judged)")
sys.exit(1 if failures else 0)
PY
