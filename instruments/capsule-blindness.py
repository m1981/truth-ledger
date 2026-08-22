#!/usr/bin/env python3
"""capsule-blindness -- Tier C instrument for the fail-open capsule class.

Commissioned by the operator ruling of 2026-08-22 (RULING 8), after
`tr-38d32bc7` was found to have reproduced GREEN FOR FOUR DAYS while
being false.

THE DEFECT, stated once so this file is readable without the journal.
That claim asserted the release battery carried TEN numbered arms, with
the capsule `grep -oE '^# --- [0-9]+[.] [a-z]+' scripts/release-battery.sh`.
At its anchor commit the recipe was EXACT. Eight hours later a naming
form its regex cannot see -- `5b.`, then `8b.` -- entered the file, and
from that moment the capsule reported 10 while the battery carried 11,
then 12. Nothing noticed. It broke only when a later section happened to
be numbered `11.` with a dot, a form the regex does match: detection
depended on a naming choice made by someone who did not know the capsule
existed. That is a lottery, not a gate.

The general shape: A CAPSULE THAT ENUMERATES BY PATTERN COUNTS WHAT IT
RECOGNISES, NOT WHAT EXISTS. Its blind spot cannot shrink and grows every
time the repository invents a form the pattern predates. A green capsule
then means "my pattern still matches the same subset", not "the fact
still holds" -- and ADR-051's whole value rests on those being one
sentence. `reproduce` cannot see this class by construction: it re-runs
the recipe and compares hashes, and a recipe blind to a new form
reproduces its own blindness perfectly.

WHAT THIS MEASURES, and what it deliberately does not.

  ENUMERATING   the recipe selects by PATTERN (`grep -c/-o/-E`, `sed -n
                '/re/p'`, `awk '/re/'`). Vulnerable: a form invented later
                is invisible, silently.
  CARDINAL      the recipe counts ENTITIES rather than their spelling
                (`wc -l <file>`, `ls <dir> | wc -l`, `git ls-files | wc -l`).
                Not vulnerable in the same way -- a new naming form still
                occupies a line or a directory entry.
  GUARDED       an enumerating recipe that also asserts its own complement
                is empty (a `grep -v` of the recognised forms, counted).
                This is the fail-closed pairing; it converts an unseen form
                from silence into a failure.
  DIGEST        hash/checksum over whole bytes -- sees everything, and is
                brittle for the opposite reason.
  OTHER         anything else, listed so the population is not silently
                truncated.

The direction of failure is the point, and it is why ENUMERATING is
called out rather than merely noted. This class fails OPEN: it reports
FEWER things than exist, which looks reasonable and invites no question.
`gate-reachability.sh` states the opposite property as a design choice --
"a variable-built path reads as unreachable, never as reached" -- because
a counter that fails toward the alarm gets fixed and one that fails toward
silence does not.

REPORT ONLY, NEVER A GATE, and deliberately so at this stage. The ruling
commissioned a measurement, not a refusal: the population is unknown, an
enumerating capsule is often the honest recipe for its fact, and a gate
built before the number is known would be the very thing ADR-047 refuses
(a gate shipped without a metric). It is also not in the CHECKS globs of
gate-reachability.sh, so it is not a dark gate -- it is not a gate at all.

Tier C wiring (ADR-046): meta-repo driver over truthlib, stdlib only.

Usage: python3 instruments/capsule-blindness.py [--json]
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "template"))

LEDGER = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                      "..", ".truth", "claims.jsonl")

# ORDER MATTERS and the boundaries are the whole instrument. A first cut
# of this file reported 59 of 68 live claims as vulnerable, which was
# wrong in the same direction as the defect it measures -- an
# unreliable counter, in an instrument commissioned because a counter
# was unreliable. The error was treating every `grep` as an enumeration.
#
# `grep -q 'def fold_key' kernel.py` ASSERTS EXISTENCE. Rename the
# symbol and it fails, loudly, immediately. It cannot go blind to a form
# invented later, because it never claimed to enumerate a set -- it
# claimed one string is present. That is fail-CLOSED and belongs
# nowhere near this report.
#
# The dangerous shape is a recipe whose OUTPUT IS A SET OR ITS SIZE:
# `-c` (count), `-o` (emit matches), `-rl`/`-l` (list files), a bare
# listing grep, `sed -n '/re/p'`, or a pattern piped into `wc -l`. There
# a form the pattern predates simply does not appear, the number stays
# plausible, and nothing raises a hand.
GUARD_RE = re.compile(r"grep\s+(-\w*v\w*|--invert-match)")
COUNT_RE = re.compile(r"\|\s*wc\s+-l|\bgrep\s+-\w*c")

# Enumerating: grep whose output is a set or a size. `-q` is excluded by
# construction -- a quiet grep emits nothing and asserts presence.
ENUM_GREP_RE = re.compile(r"\bgrep\b(?=[^|;&]*\s-\w*[colL])")
ENUM_OTHER_RE = re.compile(r"\bsed\s+-n\s+['\"]?/|\bawk\s+['\"]?/|"
                           r"grep[^|;&]*\|\s*wc\s+-l")
EXISTENCE_RE = re.compile(r"\bgrep\b[^|;&]*\s-\w*q")
CARDINAL_RE = re.compile(r"\bwc\s+-l\b|\bls\b|\bgit\s+ls-files\b")
DIGEST_RE = re.compile(r"sha\d*sum|shasum|md5|cksum")

def classify(cmd):
    """One recipe -> one bucket. A recipe may contain several shapes; the
    bucket is the WORST one present, because a capsule is only as sound as
    its weakest clause."""
    if not cmd:
        return "no-recipe"
    if GUARD_RE.search(cmd) and COUNT_RE.search(cmd):
        return "guarded"
    if ENUM_GREP_RE.search(cmd) or ENUM_OTHER_RE.search(cmd):
        return "enumerating"
    if DIGEST_RE.search(cmd):
        return "digest"
    if EXISTENCE_RE.search(cmd):
        return "existence"
    if CARDINAL_RE.search(cmd):
        return "cardinal"
    return "other"


def fold_status():
    """Statuses via the CLI's own fold and the CLI's own loader -- never a
    hand-rolled reimplementation (the drift class this repository exists to
    refuse). Same pair every Tier C instrument uses."""
    from truthlib.shellio import load_events               # noqa: E402
    from truthlib.kernel import fold                       # noqa: E402
    events = load_events()
    claims, _premises = fold(events)
    return claims, events


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)

    try:
        folded, events = fold_status()
    except Exception as exc:                      # environment, not governance
        print(f"capsule-blindness: cannot fold the ledger: {exc}",
              file=sys.stderr)
        return 2

    claims = {}
    for _, ev in events:
        if ev.get("kind") == "claim":
            claims[ev["id"]] = ev.get("payload") or {}

    rows, buckets = [], {}
    for cid, payload in claims.items():
        entry = folded.get(cid) or {}
        st = entry if isinstance(entry, str) else entry.get("status")
        if st != "live":
            continue
        ev = payload.get("evidence") or {}
        cmd = ev.get("command") or ""
        bucket = classify(cmd)
        buckets[bucket] = buckets.get(bucket, 0) + 1
        rows.append({"id": cid, "bucket": bucket, "tier": payload.get("cost_tier"),
                     "class": payload.get("evidence_class"), "command": cmd})

    vulnerable = [r for r in rows if r["bucket"] == "enumerating"]
    rows.sort(key=lambda r: (r["bucket"], r["id"]))

    if a.json:
        print(json.dumps({"buckets": buckets, "live_examined": len(rows),
                          "vulnerable": len(vulnerable), "claims": rows},
                         indent=2))
        return 0

    for r in rows:
        if r["bucket"] == "enumerating":
            print(f"  ENUMERATING  {r['id']}  {r['command'][:96]}")
    for b in sorted(buckets):
        print(f"  {b:12s} {buckets[b]}")
    print(f"capsule-blindness: {len(rows)} live claim(s) with a recipe -- "
          f"{len(vulnerable)} enumerate by pattern and can go blind to a form "
          f"invented later [report only, never a gate]")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
