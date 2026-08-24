# ADR-061: DONE requires a gate that can go red for a named reason

Status: **PROPOSED** (2026-08-24, agent-authored). Applies to roadmap batches
and to the open items in `docs/reviews/mechanism-layers-brief-2026-08-24.md`.

## Context

The repository has a plan. `docs/roadmap-v3.md` carries batches with effort
estimates, `DONE` markers and a settled-constraints section; the paper adds §10
future work and four growth gates. What the plan does not carry is a way for
`DONE` to become false again.

The evidence is one line of that roadmap:

> **Batch 3 — self-consistency (effort S) — DONE**

A single session reading the repository cold then found, inside that same
scope: four Appendix A rows describing retired machinery (`ee2f541`),
`arm-index` reading four of nine declared sources for nine days (`dc6099c`),
and 20 of 183 backtick paths across live docs pointing at files that no longer
exist. Self-consistency was marked done and decayed with nothing to notice.

This is not a planning failure. It is the same class this repository already
mechanises for claims about code: a sentence true at the time, with no
mechanism to demote it. The plan is the one register where that discipline was
never applied to itself.

## Decision

**An item is DONE when a gate exists that can go red for that item's named
reason, and someone has demonstrated it going red.**

Three parts, none optional:

1. **A named failure condition.** Not "the check is written" — the sentence
   that, if observed, means the item regressed.
2. **A gate that observes it.** Something that runs without being remembered.
3. **A demonstration.** The gate was made to fail on purpose and did.

The third part is what separates this from a checklist. Every mechanism landed
this session was demonstrated: a row naming `FAULT QQ` (`c905656`), an inverted
`FAULT B` header (`834b210`), a deleted `Amends: ADR-019` line (`d786552`).
Each proved the gate fires; none proved it merely compiles.

**Where no gate is possible, the item is not DONE — it is DECLARED**, with the
residue named. `L4(c)` (proof-test interval) can never be DONE: it is recurring
by construction. Its terminal state is "an interval is declared and the last
run is on record".

## Rejected

- **DONE by assertion.** The current form. Batch 3 is the counter-example.
- **DONE by date or effort burn-down.** Measures expenditure, not the property.
- **DONE by test-suite green.** ADR-057's own status line already refuses this:
  *"The suites, the canary and the Tier C instruments are green … which this
  repository has ruled repeatedly is not sufficient evidence."*
- **A definition of done for the whole programme.** §8 item 2 measures efficacy
  as unknown and cost as unfavourable; "the system is consistent" has no
  falsifier and no date. The nearest defensible whole-programme criterion is
  temporal and bounded: *none of findings 1–6 in the mechanism-layers brief
  recurs within three months*.

## Consequences

- Roadmap batches gain a red-gate column, retroactively for `DONE` ones. Where
  none can be named, the marker becomes `DECLARED` and the residue is written
  down. This is bookkeeping, not re-litigation of settled constraints.
- Open items in the mechanism-layers brief already carry their conditions:
  L1(a) a new dead backtick path turns `doc-health` red; L0 a relocation with
  no forwarding entry fails, as does an entry pointing nowhere; L3 a row can
  carry `Retired` and the sweep honours it; canary arms each declare a fixture
  and `arm-index` enforces it as it enforces the subject.
- An item whose gate cannot be demonstrated failing is **not** blocked. It is
  DECLARED, and the reason a demonstration is impossible is the interesting
  part of the record.

**Falsifier:** if an item marked DONE under this rule regresses without its
gate going red, the rule is wrong — the named condition did not describe the
property it claimed to.
