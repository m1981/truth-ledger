# AGENTS.md — audit, redraft, and why the redraft is not committed

Three agent passes over the file every agent reads first: an audit (measure
only), a redraft, and an adversarial review of the redraft. The redraft is in
the working tree, **uncommitted**. It should not be committed as it stands.

## What the audit found in the committed file

263 lines, **one heading**, ~26 unlabeled bullets. Four checkably false claims,
and all four stale **in the optimistic direction** — the file described gaps
that had since been closed, telling agents to do by hand what machinery now
does:

- the release battery was said to have no gate since `32022c6`; it was rebuilt
  on 2026-08-21 and now has 17 arms — the paragraph was edited the same day and
  still asserted its absence;
- a retracted number was said to be able to outlive its retraction, with a
  hand-grep instruction; `scripts/retracted-figures.sh` rides the battery;
- four live surfaces were named as still quoting a retracted pair; two no
  longer contain it;
- `fact-health.sh` was said to read a `FILES=` list; it expands
  `.truth/citation-scope`.

Sharpest structural finding: **rules nothing can fail on are written in the
same voice as gated ones** — including "never run the canary from a linked
worktree", which caused measured damage on 2026-08-20 and is still only prose.

## What the review found in the redraft

The redraft fixed all four, added ten headings, and correctly refused to carry
one claim it could not verify. It also introduced nine defects, four of them
worse than what they replaced:

1. **`--exit-ok` does not exist** (the flag is `--evidence-exit-ok`). New prose,
   and it would propagate to every agent. ADR-059 and
   `instruments/semantic-audit.py` carry the same wrong name.
2. **"the `.truth/` policy files are *each* pinned by a claim" is false** — 5 of
   16 are. Two paragraphs earlier the file *instructs* editing
   `.truth/retracted-figures`, which carries no claim, so editing it produces
   no stale and no verdict. **The committed file enumerated the five honestly;
   the redraft generalised that into a falsehood** — and labelled it ENFORCED.
3. "no `invalidation` record" — 1997 exist. ADR-057 makes the kind inert for
   status, not absent.
4. **It cites a "2026-08-24 audit of this file" that exists nowhere.** The audit
   was real but was never written to disk, so the redraft cited a phantom — and
   that citation is what licenses its whole doctrine-vs-status restructuring.

Plus: a line-number citation of the kind ADR-037/ADR-012 lint as a recipe that
diverges mechanically; ARM numbers quoted immediately after instructing the
reader not to quote numbers; and — the sharpest — **"one home per fact" while
restating `v0.10.0`, making AGENTS.md a seventh unpinned version surface**, and
removing the file's last three ledger ids, so `fact-health.sh` now has nothing
to check in the very file it is cited to defend. The redraft reduced the file's
checkability while asserting doctrine about checkability.

## The process defect, and it is the dispatcher's

Finding 4 is not the redrafting agent's fault. A measurement that informs a
change **must be written to disk before it can be cited**; this one lived only
in a task notification, so the next agent cited an event with no record. That
is the same class as everything else here — a true statement with nothing
holding it — reproduced inside the workflow built to prevent it.

**ADR-062 needs a fourth rule: the measure role's output is persisted before
the implement role is dispatched.** This document is that persistence, after
the fact.

## Standing state

`AGENTS.md` is modified and uncommitted. The committed version has four
falsehoods; the redraft has nine, including two mislabelled ENFORCED. Neither
is fit to be the file every agent reads first. The redraft's structure is worth
keeping; its new factual claims need a pass that verifies each against the tree
before any commit.
