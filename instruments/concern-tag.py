#!/usr/bin/env python3
"""concern-tag -- Tier C READER for the legacy 42010 concern tags
(D4/ADR-046: the concerns surface left the template CLI).

Reports concern-tag counts over the ledger: per-tag totals across
non-retracted claims (stale/diverged still carry their stakeholder's
interest; only retraction kills it -- the impact --inverse convention)
plus the untagged-ACTIVE count, where ACTIVE is fetched from the CLI's
own vocabulary (`truth vocab --json`) at runtime and never hand-copied
(ADR-043; see active_statuses below). Statuses come from
`scripts/truth list --json`; the tags come
from a raw ledger read, because `list` rows do not carry payload
concerns. Stdlib only; no truthlib import -- this instrument exercises
the same public surfaces any external reader has.

FILING IS CLOSED (the admission rule, ADR-046): a payload field is
admitted only if the fold or a blocking gate reads it, and nothing ever
read `concerns`. The `--concern` flag is gone from `claim` and `list`;
the field is legacy-admitted for records filed pre-ADR-046 and CLOSED
to new records. There is NO tagging path any more -- in particular,
hand-editing `concerns` into .truth/claims.jsonl is FORBIDDEN: the
ledger is append-only history, and a hand-edit would both rewrite it
and smuggle a field past the admission rule. If concern triage is ever
worth having again, it re-enters as its own Tier C sidecar store, never
as claim-payload metadata.

Usage: python3 instruments/concern-tag.py [--json]
Gate:  template/scripts/test-integrations.py (TestTierCInstruments),
       run at push by scripts/release-battery.sh. Until 2026-08-28 this
       line named scripts/test-instruments.sh, retired at 32022c6 -- the
       same dead pointer field-consumers.py had already recorded in its
       own header.
"""
import json
import os
import subprocess
import sys

LEDGER_REL = ".truth/claims.jsonl"


def cli(truth, *args):
    """Run the CLI and return stdout, or die loudly."""
    r = subprocess.run([sys.executable, truth, *args],
                       capture_output=True, text=True,
                       cwd=os.path.dirname(os.path.dirname(truth)))
    if r.returncode != 0:
        sys.exit(f"concern-tag: `truth {' '.join(args)}` failed "
                 f"(rc={r.returncode}): {r.stderr.strip()}")
    return r.stdout


def active_statuses(truth):
    """The ACTIVE set, fetched from the CLI's own vocabulary at runtime.

    Never hand-copied. A literal ("live", "unverified") sat here until
    2026-08-02 and was the exact contract-copy drift class ADR-043 closed
    with `truth vocab --json`: the day the CLI's notion of active moves,
    a copy keeps counting yesterday's answer and calls it a measurement.
    Fail LOUD if the vocabulary is unavailable (the F1 rule, and the same
    shape as scripts/fact-health.sh) -- tallying against a guessed
    vocabulary is the drift re-armed, dressed as a report.
    """
    vocab = json.loads(cli(truth, "vocab", "--json"))
    active = vocab.get("active")
    if not isinstance(active, list) or not active \
       or not all(isinstance(s, str) for s in active):
        sys.exit("concern-tag: `truth vocab --json` carries no usable "
                 "'active' set -- refusing to tally against a guessed "
                 "vocabulary")
    return frozenset(active)


def repo_root():
    r = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("concern-tag: not inside a git repository")
    return r.stdout.strip()


def claim_concerns(payload):
    """Legacy tags as read-side data (the truthlib.reports contract,
    restated here so this reader stays truthlib-free): string items of a
    well-formed list, else [] -- degrade, never crash (red-team F2)."""
    cs = payload.get("concerns")
    if not isinstance(cs, list):
        return []
    return [t for t in cs if isinstance(t, str)]


def main(argv):
    root = repo_root()
    truth = os.path.join(root, "scripts", "truth")
    active = active_statuses(truth)
    status = {row["id"]: row["status"]
              for row in json.loads(cli(truth, "list", "--json"))}
    tags_by_id = {}
    with open(os.path.join(root, LEDGER_REL), encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except ValueError:
                continue  # validate's finding, not this reader's
            if ev.get("kind") == "claim" and ev.get("id") in status:
                tags = claim_concerns(ev.get("payload") or {})
                if tags:
                    tags_by_id.setdefault(ev["id"], tags)
    counts, untagged = {}, 0
    for cid, st in status.items():
        tags = tags_by_id.get(cid, [])
        if st != "retracted":
            for t in tags:
                counts[t] = counts.get(t, 0) + 1
        if st in active and not tags:
            untagged += 1
    if "--json" in argv:
        print(json.dumps({"concerns": counts,
                          "concerns_untagged_active": untagged,
                          "legacy_note": "field closed to new records "
                                         "(ADR-046 admission rule)"},
                         indent=2))
        return 0
    # Render preserved verbatim from the retired `truth stats` section.
    print("concerns: " + (", ".join(
        f"{k}={v}" for k, v in sorted(counts.items())) or "none")
        + f", untagged-active={untagged}")
    print("  note: legacy tags (pre-ADR-046); the field is closed to new "
          "records -- there is no tagging path, and hand-editing the "
          "ledger is forbidden")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
