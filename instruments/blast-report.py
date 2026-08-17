#!/usr/bin/env python3
"""blast-report -- Tier C instrument for the ADR-039 churn report
(ADR-046: moved out of `truth stats`; blast_forecast is no longer
stored -- forecasts are computed on read, here).

Reports observed invalidations vs LIVE-computed forecast per path-claim
(top 5 by observed), the per-path staler ranking read from invalidation
`touched` lists, and the effective advisory floor (P90 self-calibration
over live path-claims, cold-start fallback). One `git log` (the same
cost intake used to pay to stamp the retired stored ints) supplies the
window; every match is pure. Report only, never a gate.

Legacy note (ADR-046): records admitted pre-ADR-046 may still carry a
stored `blast_forecast`; this instrument IGNORES stored values whenever
history is readable (live numbers describe today's window, stored ones
described filing day) and falls back to them only when `git log` is
shallow/unavailable.

Tier C wiring: meta-repo driver over truthlib (sys.path bootstrap to
template/); the pure report itself (truthlib.reports.blast_report)
never moved. Stdlib only.

Usage: python3 instruments/blast-report.py [--json]
Gate:  scripts/test-instruments.sh


FAZA 4 (2026-08-17): this is now a META-REPO-LOCAL VIEW, not the
only one. `truth health` composes blast_report() into a section that
SHIPS to consumers -- which is the point, since instruments/ is not
templated and a generated repo could never see this number. There is
still exactly ONE implementation: both call blast_report() in
truthlib/reports.py. Keep it that way; a second computation here
would drift from the shipped one and both would look authoritative.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "template"))

from truthlib.reports import blast_report  # noqa: E402
from truthlib.kernel import fold  # noqa: E402
from truthlib.shellio import blast_history, load_events  # noqa: E402


def main(argv):
    events = load_events()
    history, state = blast_history()
    b = blast_report(events, folded=fold(events),
                     history=history if state == "ok" else None)
    if "--json" in argv:
        b["history_state"] = state
        print(json.dumps(b, indent=2))
        return 0
    # Render preserved verbatim from the retired `truth stats` section.
    print(f"blast: floor {b['effective_floor']} ({b['floor_source']})"
          + ("; top observed-vs-forecast: " + ", ".join(
              f"{r['claim']}={r['observed']}/{r['forecast']}"
              for r in b["rows"]) if b["rows"] else "")
          + ("; top stalers: " + ", ".join(
              f"{s['path']}={s['invalidations']}"
              for s in b["staler_ranking"]) if b["staler_ranking"] else ""))
    if state != "ok":
        print(f"  advisory: git history {state} -- forecasts fall back to "
              "stored legacy values where present (ADR-039/046)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
