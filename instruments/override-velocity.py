#!/usr/bin/env python3
"""override-velocity -- Tier C instrument for the ADR-033 override
report (ADR-046: moved out of `truth stats`).

Counts every stored override the intake gates admit (scope-ok filings,
ADR-032 decay expiries, duplicate overrides, unscreened filings,
exit-ok, orphan-ok, generated-ok, the hollow-warned population, max
scope TTL) and voices the verbatim-repeat advisory -- the data ADR-007's
adoption gate and the monthly hand-audit read. Report only, never a
gate.

Tier C wiring (ADR-046): meta-repo driver over truthlib (sys.path
bootstrap to template/); the pure report itself
(truthlib.reports.override_report) moved there with A2. Stdlib only.

Usage: python3 instruments/override-velocity.py [--json]
Gate:  scripts/test-instruments.sh


FAZA 4 (2026-08-17): this is now a META-REPO-LOCAL VIEW, not the
only one. `truth health` composes override_report() into a section that
SHIPS to consumers -- which is the point, since instruments/ is not
templated and a generated repo could never see this number. There is
still exactly ONE implementation: both call override_report() in
truthlib/reports.py. Keep it that way; a second computation here
would drift from the shipped one and both would look authoritative.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "template"))

from truthlib.reports import override_report  # noqa: E402
from truthlib.kernel import fold  # noqa: E402
from truthlib.shellio import load_events, now_dt  # noqa: E402


def main(argv):
    events = load_events()
    o = override_report(events, now_dt(), folded=fold(events))
    if "--json" in argv:
        print(json.dumps(o, indent=2))
        return 0
    # Render preserved verbatim from the retired `truth stats` section.
    mx = o["max_scope_ttl_days"]
    print(f"overrides: scope-ok={o['scope_basis_filings']} "
          f"decay-expiries={o['decay_expiries']} "
          f"dup-overrides={o['overridden_duplicates']} "
          f"unscreened={o['screened_false_filings']} "
          f"exit-ok={o['evidence_exit_filings']} "
          f"orphan-ok={o['orphan_filings']} "
          f"generated-ok={o['generated_ok_filings']}"
          + (f", max scope ttl {mx}d" if mx is not None else ""))
    print(f"hollow: warned={o['hollow_warned']} "
          f"(overridden -> overrides exit-ok)")
    for r in o["repeats"]:
        print(f"  advisory: {r['claim']} re-files the scope justification "
              f"of {r['prior']} (now {r['prior_status']}) verbatim -- same "
              "scope justification re-filed unchanged after expiry -- "
              "review whether the scope judgment was ever real (ADR-033)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
