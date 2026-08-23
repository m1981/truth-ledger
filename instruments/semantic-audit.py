#!/usr/bin/env python3
"""semantic-audit -- Tier C EXTRACTOR for the asynchronous semantic audit
(ADR-059). Emits the JUSTIFICATION SENTENCES carried by active claims and their
verdicts -- plus `orphan_basis` from retracted ones, which is the single
sentence that outlives its subject -- as flat JSON on stdout. It judges
nothing.

WHY AN EXTRACTOR AND NOT A CHECKER. Every override in this system is
admitted on a SENTENCE: `--scope-ok` says why a quantifier may stand,
`--paths-ok` why a freehand watch set may exceed the budget,
`--generated-ok` why a generated artifact may be watched, `--exit-ok` why a
failing probe still proves something, `--orphan-ok` why citations may be
left dangling, and ADR-051's `--refresh-evidence` why a moved output is
still the same fact. The gates check that a sentence EXISTS and is
non-empty. Nothing in the repository has ever checked whether it MEANS
anything -- "reviewed", "ok", "see above" and a genuine argument are
identical to every mechanism here.

That check needs a reader, and ADR-059 puts the reader outside: an LLM
running in CI, at L2. This script is the L1 half, and its entire job is to
hand L2 the text.

EPI-305, mechanically enforced: the machine measures, the human (or the
L2 oracle) judges. A "semantic gate" that ran a language model inside the
CLI and refused a filing on its output would be L1 grading meaning, which
is the one thing L1 cannot do honestly -- and it would make every intake
depend on a non-deterministic remote service. So:

    NO NETWORK I/O. NOT requests, NOT http.client, NOT urllib, NOT socket.

That is a hard contract, not a preference. This process reads the ledger
and writes JSON to a pipe; the send lives in CI, where a human wrote the
workflow and can see what leaves the machine. TestTierCInstruments pins
the absence of those imports, so a future edit that "just posts the
result" fails a gate rather than shipping the repository's justification
text to a third party silently.

Tier C wiring (ADR-046): meta-repo driver over truthlib (sys.path
bootstrap to template/). Stdlib only.

Usage: python3 instruments/semantic-audit.py
Gate:  template/scripts/test-integrations.py (TestTierCInstruments)
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "template"))

from truthlib.kernel import fold  # noqa: E402
from truthlib.registry import ACTIVE_STATUSES  # noqa: E402
from truthlib.shellio import load_events, now_dt  # noqa: E402

# Basis fields carried by the CLAIM record's payload. Each is a plain
# string: the sentence an intake gate accepted in place of a refusal.
CLAIM_BASIS_FIELDS = (
    "scope_basis",           # ADR-007  --scope-ok
    "paths_basis",           # FAZA 3   --paths-ok
    "generated_ok_basis",    # ADR-037  --generated-ok
    "evidence_exit_basis",   # ADR-035  --exit-ok
)

# Basis fields carried by a VERDICT record's payload, for claims that are
# still ACTIVE. ADR-051 nests its sentence inside an object, hence the pair.
VERDICT_NESTED_BASIS = (
    ("evidence_refresh", "basis"),   # ADR-051  --refresh-evidence
)

# ADR-036's orphan sentence, which needs its own scope and is the reason
# this extractor has two of them. `orphan_basis` is valid ONLY on a
# `retracted` verdict (kernel.validate_events refuses it anywhere else),
# and a retracted claim is by definition never active -- so under an
# active-only scope this field would read 0 on every ledger, forever.
#
# It is extracted anyway, from RETRACTED claims only, by operator ruling.
# The justification is different in kind from the others and that is why
# it survives its subject's death: the other sentences defend a fact that
# is still being relied on, and stop mattering when the fact dies. This
# one defends a DELIBERATE ACT -- leaving citations dangling at the moment
# of retraction. The act is permanent, the dangling references are still
# out there in the corpus, and "why was it acceptable to orphan them" is a
# question that only becomes answerable after the retraction has happened.
ORPHAN_FIELD = "orphan_basis"
ORPHAN_STATUSES = frozenset(("retracted",))


def _row(claim_id, record_id, kind, basis):
    """One extraction. `id` is the CLAIM the sentence is defending, which
    is what an auditor needs to act on; `record` is the record the
    sentence physically lives in, since a claim can carry several verdicts
    and the two would otherwise be indistinguishable."""
    return {"id": claim_id, "record": record_id,
            "type": kind, "basis": basis}


def extract(events, now=None):
    """Pure: (events, clock) -> list of extraction rows, sorted.

    TWO SCOPES, deliberately, and the split is the whole subtlety of this
    function:

      * ACTIVE claims (live, unverified) for the sentences that defend a
        fact still in use. A diverged or retracted claim's `scope_basis` is
        history -- nobody is relying on it, so asking an LLM to judge it
        spends tokens on a finding no one can act on.
      * RETRACTED claims for `orphan_basis` alone. That sentence defends
        an ACT rather than a fact (see ORPHAN_STATUSES above), the act
        outlives the claim, and it is unauditable under any active-only
        scope because the field cannot legally appear on a live claim.

    The clock is passed through to fold() because ADR-057 derives TTL
    expiry at read time -- without it, an expired override would still be
    extracted as if it were load-bearing, which is exactly the stale
    reading this audit exists to catch.

    Sorted by (claim id, type, record id) so two runs over one ledger
    produce byte-identical output and a CI diff means the LEDGER moved,
    not that a dict iterated differently."""
    claims, _ = fold(events, now_dt=now)
    active = {cid for cid, e in claims.items()
              if e["status"] in ACTIVE_STATUSES}
    orphaning = {cid for cid, e in claims.items()
                 if e["status"] in ORPHAN_STATUSES}

    rows = []
    for cid in active:
        payload = claims[cid]["claim"].get("payload") or {}
        for field in CLAIM_BASIS_FIELDS:
            value = payload.get(field)
            if isinstance(value, str) and value.strip():
                rows.append(_row(cid, cid, field, value))

    for _n, ev in events:
        if ev.get("kind") != "verdict":
            continue
        p = ev.get("payload") or {}
        cid = p.get("claim")
        if cid in active:
            for outer, inner in VERDICT_NESTED_BASIS:
                obj = p.get(outer)
                if isinstance(obj, dict):
                    value = obj.get(inner)
                    if isinstance(value, str) and value.strip():
                        rows.append(_row(cid, ev.get("id"), outer, value))
        elif cid in orphaning:
            # The ONLY field read off a dead claim. Guarding on the status
            # rather than on the field alone matters: a retraction that was
            # later superseded, or a record forged with an orphan_basis on
            # a live claim, must not reach the audit through this branch.
            value = p.get(ORPHAN_FIELD)
            if isinstance(value, str) and value.strip():
                rows.append(_row(cid, ev.get("id"), ORPHAN_FIELD, value))

    rows.sort(key=lambda r: (r["id"], r["type"], r["record"] or ""))
    return rows


def census(rows):
    """Per-type counts, for stderr. The battery's law is that every arm
    reports WHAT IT EXAMINED, and it applies to an extractor too: a type
    that yields 0 rows forever is a dark arm, and the only way anyone
    notices is if the number is printed.

    `orphan_basis` used to be a GUARANTEED zero here: it is legal only on
    a `retracted` verdict, and the first cut of this extractor read active
    claims only, so the type was structurally unreachable. The operator
    ruled the scope widened rather than the field dropped, and the census
    is how that ruling stays checkable -- if this number returns to a
    permanent 0, the retracted branch in extract() has stopped firing."""
    counts = {f: 0 for f in CLAIM_BASIS_FIELDS}
    counts[ORPHAN_FIELD] = 0
    counts.update({o: 0 for o, _ in VERDICT_NESTED_BASIS})
    for r in rows:
        counts[r["type"]] = counts.get(r["type"], 0) + 1
    return counts


def main(argv):
    rows = extract(load_events(), now_dt())
    print(json.dumps(rows, indent=2, ensure_ascii=False, sort_keys=True))
    c = census(rows)
    print("semantic-audit: %d basis sentence(s) -- active claims, plus "
          "orphan_basis from retracted ones -- %s"
          % (len(rows), ", ".join("%s=%d" % kv for kv in sorted(c.items()))),
          file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
