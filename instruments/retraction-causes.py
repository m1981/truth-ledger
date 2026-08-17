#!/usr/bin/env python3
"""retraction-causes -- Tier C instrument for ADR-049's adoption metric.

Tallies every retraction verdict by its recorded `cause`, plus the
`unrecorded` legacy population (pre-ADR-049 retractions, which carry no
cause and validate forever -- append-only history is never rewritten)
and how often a retraction leaves a followable successor pointer at
all.

The two numbers ADR-047's review reads:
  * `unrecorded` share -- must stop growing; every retraction filed
    from v0.9.34 on records a cause, so a rising count means a raw
    append bypassed intake.
  * successors missing under `cause=restated` -- structurally ZERO
    (the intake gate refuses it), so any non-zero value is the same
    bypass, seen from the other side.

Report only, never a gate. Tier C wiring (ADR-046): meta-repo driver
over truthlib (sys.path bootstrap to template/); the pure report
(truthlib.reports.retraction_cause_report) lives in the template and
is unit-tested there. Stdlib only.

Usage: python3 instruments/retraction-causes.py [--json]
Gate:  scripts/test-instruments.sh


FAZA 4 (2026-08-17): this is now a META-REPO-LOCAL VIEW, not the
only one. `truth health` composes retraction_cause_report() into a section that
SHIPS to consumers -- which is the point, since instruments/ is not
templated and a generated repo could never see this number. There is
still exactly ONE implementation: both call retraction_cause_report() in
truthlib/reports.py. Keep it that way; a second computation here
would drift from the shipped one and both would look authoritative.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "template"))

from truthlib.reports import retraction_cause_report  # noqa: E402
from truthlib.registry import RETRACTION_CAUSES  # noqa: E402
from truthlib.shellio import load_events  # noqa: E402


def main(argv):
    events = load_events()
    r = retraction_cause_report(events)
    if "--json" in argv:
        print(json.dumps(r, indent=2))
        return 0
    total = r["total"]
    by = r["by_cause"]
    print("retractions: " + str(total) + " total ("
          + ", ".join(f"{c}={by[c]}" for c in RETRACTION_CAUSES)
          + f", unrecorded={by['unrecorded']})")
    if total:
        pct = 100.0 * by["unrecorded"] / total
        print(f"  unrecorded share: {pct:.0f}% "
              "(pre-ADR-049 records; this number must stop growing)")
    print(f"  successor named: {r['successors_named']}, "
          f"missing: {r['successors_missing']}")
    # The structural check: intake refuses `restated` without a
    # successor, so a stored one can only come from a raw append.
    orphaned_restated = [
        ev["id"] for _, ev in events
        if ev.get("kind") == "verdict"
        and (ev.get("payload") or {}).get("cause") == "restated"
        and not (ev.get("payload") or {}).get("successor")]
    for rid in orphaned_restated:
        print(f"  ALARM: {rid} records cause=restated with no successor -- "
              "intake refuses this shape, so the record was appended "
              "past the CLI (ADR-049)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
