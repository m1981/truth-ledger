# ADR-063: An answer's findings terminate, or the answer is not finished

Status: **PROPOSED** (2026-08-26, agent-authored, from one session's measured
experience). The operational form belongs in `AGENTS.md`; this record carries
the decision and its falsifier. **Not gateable inside this repository** — see
*Rejected*.

Cites: ADR-042 (rule 2 — measuring nothing has not passed), ADR-061 (DONE
requires a gate that can go red), ADR-062 (roles are separated by what each is
not told — this is its sibling: what each must say when it reports).

## Context

An operator complaint — answers carry many observations and close on one —
was measured rather than accepted. An independent auditor, not given the
figures, hand-classified all 51 substantive answers of the 2026-08-26 session
against a definition it stated before counting and calibrated by re-scoring a
random sample (drift +0.9 pp on the aggregate rate).

| | |
|---|---|
| findings raised | **374** |
| terminated in the same answer | **307** |
| rate | **0.821** (median 1.00, bimodal, min 0.00) |

Termination *does* scale with findings raised — `terminated = -0.26 + 0.856 ×
raised`, r=0.80 — so the naive reading was wrong, and so was the assistant's
own first measurement: it reported 718 / 0.7 / 31% by a bold-span proxy that
**does not replicate** (the same method re-run gives 1062 / 1.06 / 43%) and
whose correlation with hand-counted terminations is 0.235.

The defect is real but **localised by answer genre**:

| stratum | n | rate | median |
|---|---|---|---|
| work / review | 41 | 0.914 | 1.00 |
| **expository / advisory** | 10 | **0.423** | **0.33** |

**61% of all orphaned findings live in 20% of the answers**, and the
expository intercept is −2.2: the first two findings of an explanatory answer
are structurally guaranteed to be orphaned. The convention therefore matters
most where it was least applied — when explaining, not when working.

Sixteen escalations to the operator were traced. Nine resolved. **Seven
disappeared with no repository trace**, including a suspected fail-open in
`arm-index --record-links` raised in the session's first answer and never
mentioned again. The assistant's own carry-forward section recovered one item
that had been absent for sixteen consecutive answers — and had **recall ≈45%**
against the auditor's independently compiled list, because it was a
hand-maintained roster: the failure class this repository has been defeated by
four times.

## Decision

Five sections: **Odpowiedź** (the verdict, before the evidence) · **Dowód**
(only what carries it) · **Co z tego wynika** (the implication, not the
observation) · **Domknięcie** (the table) · **Otwarte** (escalations carried
forward). Five rules, each earned:

1. **Every finding raised in the body terminates in exactly one of three:
   `robię`, `Twoja decyzja`, `odpuszczam — z powodem`. Unclassified: zero.**
   A partition, not a search — the move this repository has made against every
   roster it has lost to. Its side effect is the point: *a finding not worth
   terminating is not worth raising*, which cures the ratio at source where an
   instruction to be brief does not.

2. **Provenance per finding — `cmd` / `hist` / `wnioskowanie`.** Earned three
   times in one session, each time by an inference wearing the clothes of a
   measurement: a sortal read where the split was by verb, a predicted
   fail-open a cross-check already covered, and a constant number read as
   staleness where it was blindness.

3. **A warrant is required on every finding marked `wnioskowanie`** — one
   line: on what licence these data yield this claim. All three errors above
   were **warrant failures, not data failures**: the data were right and the
   inference licence was never examined. Backing only where the warrant is
   contested, or where a warrant of the same shape has already failed.
   Measured findings need none — the provenance mark already partitions the
   set, so the requirement lands exactly where the failures were.

4. **Every `robię` carries a defeat condition** — what would make abandoning
   it correct. ADR-061 turned on the assistant's own output.

5. **Every escalation persists in `Otwarte` until resolved, and carries what
   blocks it.** Order is derived from the blocking graph, never re-typed:
   a hand-ordered list is the same roster as a hand-maintained one. Seven
   escalations evaporated; ordering, stated in prose four times, evaporated
   with them.

**Negative rule.** A one-sentence answer skips the skeleton entirely. Four
headers over one sentence is theatre — the same failure this repository names
for an assurance case that acquires a diagram before it acquires defeat
conditions.

## Rejected

- **Gating this inside the repository.** The evidence is the session
  transcript, which lives outside the repo, machine-local and unreproducible
  for any other reader. A gate that cannot run is worse than none (ADR-042
  rule 2). This record says so rather than shipping a check that measures
  nothing.
- **Use/mention markers in prose.** Hand-applied per citation: a forgotten
  marker fires a false failure, a misapplied one silently suppresses a true
  one. Fail-open, and a roster.
- **Self-audit as evidence.** The metric is authored by the party measured. A
  closure table is inflatable three ways — pad it, route everything outward,
  or **suppress the raise**, which the table cannot show. Self-audit is a
  necessary condition, never evidence.
- **A hand-ordered open list.** See rule 5.

## Falsifier

This decision dies if, across **≥10 post-adoption expository/advisory
answers**, the termination rate does not move from the 0.423 baseline — the
work/review stratum cannot carry the argument, being already at 0.914 with no
headroom.

The comparison means nothing unless: the definition is **frozen before** the
post period and applied by **someone who is not the author**, from the raw
transcript, with the per-finding enumeration published; **findings-raised is
reported alongside the rate**, because a rate that improves by raising less is
a loss that looks identical to a gain; and at least one **outcome outside the
author's control** is measured. Two are available and both have a baseline
from this session:

| outcome | baseline |
|---|---|
| escalations reaching a repository artefact | **9 of 16**; 7 evaporated |
| carry-forward recall against an independent list | **≈45%** (5 rows / ~11 live) |
| operator re-asks something already delivered | to be counted |

## Consequences

- `AGENTS.md` gains the operational form — **deferred**: that file is
  mid-review with five false assertions of its own
  (`docs/reviews/agents-md-review-2026-08-26.md`). This record stands alone
  until they land.
- `register-index` will report `adr-unaccounted:ADR-063` until the roadmap
  cites it or a baseline entry excuses it **with a reason**. That is an
  operator ruling of the same shape as ADR-062's, and it is named here rather
  than settled by side effect.
- Rule 5's carry-forward remains a hand-maintained roster until the work
  kernel carries it: `truth issue --deps` gives a blocking graph, and a
  topological order derived from it, which is what rule 5 actually wants.
  **The dependency is stated so that satisfying rule 5 by hand is understood
  as the interim, not the design.** One work item is live in this repository
  today; whether that kernel is dormant or deliberately retired is an open
  operator question.
