#!/usr/bin/env python3
"""watch-derivation -- Tier C instrument: does a claim watch what its
recipe reads?

Mechanizes, over the whole live population, the comparison J-040 ran by
hand over eight claims: derive a watch set from the evidence command's
path-like tokens, and diff it against the set the author declared.

EXISTS TO SETTLE A PROPOSAL, AND IT SETTLED IT AGAINST THE PROPOSAL.
The idea was to DERIVE `evidence_paths` from the recipe instead of
letting an author declare it, on the argument that one fact declared
twice must drift. Measured 2026-08-18 (see J-045): 70 of 75 agree
exactly, 0 watch too narrow, 0 drift both ways. The drift the proposal
existed to make impossible is, today, ~93% absent -- so derivation would
replace a working practice to fix a defect that is not there. Kept as an
instrument rather than deleted, so the next person with the same good
idea gets the number in thirty seconds instead of rebuilding the case.

THE FOUR "TOO WIDE" ROWS ARE NOT ALL DEFECTS, and reading them is the
point of the instrument. A claim may legitimately watch the SUBJECT of
its sentence rather than the INPUTS of its recipe: tr-3357082d watches
`template/scripts/truth` because the document it is about describes that
CLI, so a CLI change can falsify the sentence even though the grep never
opens it. That is a real tension with J-022's invariant ("watch exactly
what the recipe reads"), surfaced by mechanizing the invariant, and it
is why this is a REPORT and must never become a gate.

DERIVATION IS SOUND, NOT COMPLETE. A token counts as a path only when
git already tracks it, so nothing is invented -- but a recipe naming a
GLOB (`wc -l template/truthlib/*.py`) derives nothing, and that is the
`derives-nothing` bucket, an artifact of the method rather than a
finding about the claim.

Report only, never a gate. Usage:  python3 instruments/watch-derivation.py
"""
import collections
import json
import os
import shlex
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "template"))

from truthlib.kernel import fold, match_paths          # noqa: E402
from truthlib.registry import ACTIVE_STATUSES          # noqa: E402
from truthlib.shellio import ledger_path, tracked_files  # noqa: E402


def derive(cmd, tracked):
    """Path-like tokens of a recipe that name a TRACKED file, or None
    when the command does not tokenize as a shell word list."""
    try:
        return {t for t in shlex.split(cmd) if t in tracked}
    except ValueError:
        return None


def classify(declared, derived):
    """`missing` = the recipe reads it and nothing watches it (too
    NARROW, the dangerous direction). `unused` = declared and matched by
    nothing derived (too WIDE, which may be deliberate)."""
    missing = {f for f in derived if not match_paths(f, declared)}
    unused = [g for g in declared
              if not any(match_paths(f, [g]) for f in derived)]
    if not missing and not unused:
        return "exact", missing, unused
    if missing and unused:
        return "drift-both-ways", missing, unused
    return ("watch-too-narrow" if missing else "watch-too-wide"), missing, unused


def main():
    tracked = set(tracked_files())
    events = []
    with open(ledger_path(), encoding="utf-8") as fh:
        for n, line in enumerate(fh):
            line = line.strip()
            if line:
                events.append((n, json.loads(line)))
    claims, _ = fold(events)

    buckets = collections.Counter()
    detail = []
    for cid, entry in sorted(claims.items()):
        if entry["status"] not in ACTIVE_STATUSES:
            continue
        payload = entry["claim"]["payload"]
        declared = payload.get("evidence_paths") or []
        cmd = (payload.get("evidence") or {}).get("command")
        if not declared or not cmd:
            continue
        derived = derive(cmd, tracked)
        if derived is None:
            buckets["recipe-unparseable"] += 1
            continue
        if not derived:
            buckets["derives-nothing"] += 1
            continue
        kind, missing, unused = classify(declared, derived)
        buckets[kind] += 1
        if kind != "exact":
            detail.append((cid, kind, sorted(missing), unused, sorted(derived)))

    total = sum(buckets.values())
    if not total:
        sys.exit("watch-derivation: no claim carries BOTH a recipe and a "
                 "watch set -- nothing to compare (ADR-042 rule 2)")
    print(f"watch-derivation: {total} active claim(s) with a recipe and a "
          f"watch set")
    for kind, n in buckets.most_common():
        print(f"  {kind:20s} {n:3d}  ({100 * n // total:2d}%)")
    for cid, kind, missing, unused, derived in detail:
        print(f"\n  {cid}  {kind}")
        if missing:
            print(f"    recipe reads, nothing watches: {missing}")
        if unused:
            print(f"    declared, matched by nothing:  {unused}")
        print(f"    derived from recipe:           {derived}")
    print("\nREPORT ONLY -- 'too wide' is not automatically a defect; a claim "
          "may watch the SUBJECT of its sentence, not just the inputs of its "
          "recipe. See this file's docstring and J-045.")


if __name__ == "__main__":
    main()
