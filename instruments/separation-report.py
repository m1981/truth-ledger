#!/usr/bin/env python3
"""separation-report -- Tier C instrument for the ADR-010 separation
evidence (ADR-046: moved out of `truth stats` and `truth doctor`).

Reports what the records CAN prove about verifier independence: how long
each claim existed before its first agree (pairs, median, the
SEPARATION_FLOOR_SECONDS floor, same-session regressions, and the
currently-LIVE claims whose first agree landed inside the floor -- the
"named a verifier, evidenced nothing" class the paper's section 8 item
1a discloses). Advisory instrument, never a gate: a refusal keyed on
elapsed time is defeated by `sleep` and would teach that bypass.

Tier C wiring (ADR-046): instruments live in the meta-repo beside the
template, so this driver imports truthlib directly (sys.path bootstrap
to template/) and reads the ledger of the repo it runs in via
truthlib.shellio.load_events. The pure report itself
(truthlib.advisory.separation_report) never moved. Stdlib only.

Usage: python3 instruments/separation-report.py [--json]
Gate:  scripts/test-instruments.sh
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "template"))

from truthlib.advisory import separation_report  # noqa: E402
from truthlib.kernel import fold  # noqa: E402
from truthlib.shellio import load_events, now_dt  # noqa: E402


def main(argv):
    events = load_events()
    sp = separation_report(events, now_dt(), folded=fold(events))
    if "--json" in argv:
        print(json.dumps(sp, indent=2))
        return 0
    if not sp["pairs"]:
        print("separation: no first-agree pairs yet")
        return 0
    # Render preserved verbatim from the retired `truth stats` section.
    print(f"separation: {sp['pairs']} first-agree pair(s), median "
          f"{sp['median_seconds']}s; {sp['unevidenced']} inside the "
          f"{sp['floor_seconds']}s floor"
          + (f" (fastest {sp['fastest'][0]}s, {sp['fastest'][1]})"
             if sp["fastest"] else ""))
    if sp["same_session"]:
        print(f"  advisory: {sp['same_session']} agree(s) share the "
              "author's session -- ADR-010 should have refused these; "
              "the gate has regressed")
    if sp["live_unevidenced"]:
        print("  advisory: currently-LIVE claims whose first agree "
              "landed inside the floor, so the ledger holds no evidence "
              "a separate session ever read them: "
              + ", ".join(sp["live_unevidenced"])
              + " -- re-dispatch to earn the verification, or accept "
              "that 'live' here means 'named a verifier' (ADR-010)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
