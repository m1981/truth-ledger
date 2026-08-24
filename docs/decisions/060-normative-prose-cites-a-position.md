# ADR-060: Normative prose cites a position, and the citation is freshness-checked

Status: **PROPOSED** (2026-08-24, agent-authored). The sorting rule applies at
the point of pain, never retroactively; half two is implemented separately and
is the binding half.

Amends: **ADR-057** — not in substance, but in what its implementation exposed

## Context

Under ADR-057 `kernel.py` derives expiry from `now_dt`. The paper's §1 says:

> The clock's effect is **frozen into a record, never recomputed on read**
> (ADR-019).

That sentence is false today. The draft of this decision assumed the cause was
a missing address — that normative prose names no position, so nothing can
check it. **Measurement killed that:**

```
§1: 18 paragraphs | carrying a normative modal: 13 | citing no position: 3
```

The clock sentence **cites ADR-019**. The address existed and was correct when
written. The divergence arose because ADR-057 changed what the cited position
means, and **nothing marked the prose that cites it**.

This is the class suspect links (`834b210`) closed for row↔arm links: a link
that still resolves is not therefore fresh.

## Decision

Two halves. The second is the binding one.

**1. The sorting rule.** A sentence carrying a falsifier is an **article** — it
belongs in a position with a `Gate`. A sentence without one is a **recital**:
it stays prose and nothing polices it. Applied **at the point of pain**: when a
normative sentence turns out to be false, it is not corrected in prose, it is
promoted to a position. Not retroactively, not as a rewriting project.

**2. Citation freshness.** A citation from normative prose obeys the same rule
as a row↔arm link: when what the cited position *means* changes, the citing
paragraph becomes **SUSPECT** until a human confirms it. Mechanically this
extends `suspect_links` from table rows to paragraphs.

The trigger is deliberately not the cited file's own bytes. ADR-019 was never
edited; ADR-057 superseded it from outside. So the hashed target is the cited
position **together with the set of positions that amend or supersede it** —
the thing that actually moved.

## Rejected

- **A meaning-based detector.** Recognising "normative sentences" with a model
  breaks a rule this repository already holds: *"No NLP, by design — the moment
  a gate needs a model to fire, it is a review, not a refusal."* A surface lint
  over modals plus citation presence over-reports by construction and is
  baseline-gated; a model does neither.
- **Rewriting §1 as a table of positions.** 13 of 18 paragraphs already cite;
  the cost is high and the gain covers three paragraphs. §8 item 2 measures
  churn as the dominant cost, and this would add to it without proportional
  return.
- **The sorting rule alone.** It would not have caught the clock sentence,
  which has an address. Half one without half two is a norm shaped like a
  mechanism.

## Consequences

- The three uncited paragraphs in §1 are promotion candidates, not defects.
- The clock sentence needs a decision this ADR does not make: ADR-057 is
  `PROPOSED` and unreviewed, so here **the code may be ahead of the record**
  rather than the record behind the code. Repairing the prose before the status
  is settled would freeze an unaccepted state.
- Residue R1/R2 in `.local/warstwy-mechanizmow.md` shrinks only once half two
  ships. Until then prose↔code is uncovered, and that is a declared state
  rather than an oversight.

**Falsifier:** if, after half two ships, a normative paragraph again outlives a
change to the position it cites, this decision is wrong — the drift does not
live in citation freshness.
