# Work in flight — 2026-08-26

Status: **operator's ordering, not a decision.** No measurement produced this
order; it is an argument about what decays and what blocks what, and it is
meant to be overruled. Lives here because `docs/reviews` is the briefs
register's location, so it needs no new register row.

## How to use it, and the rule that stops it rotting

An item leaves this file only when its **done condition** has been
demonstrated — not when it feels finished. Demonstrating it means the
condition's command was run and its output read.

Removing an item is not enough. The demonstration goes somewhere durable
first: a commit, or a row in `docs/governance/catch-log.md`. A plan whose
completed items evaporate cannot be audited later, and this repository has
been defeated by hand-maintained lists four times.

Each item also carries a **decay condition**: what would make it wrong to
still be on this list. An item nobody can decay is an item nobody can drop.

---

## In flight right now

| # | what | where |
|---|---|---|
| R1 | reviewer on the plan-mode change, dispatched 2026-08-26, working | prompt `template/prompts/review-plan-mode-2026-08-26.md`; tree in a scratchpad copy |
| R2 | reviewer on the `AGENTS.md` redraft — handoff written, **not dispatched** | `docs/reviews/agents-md-review-handoff-2026-08-26.md` |

R1's tree is a disposable copy under the session scratchpad and **will not
survive the session**. It is regenerable:

```
SRC=~/PycharmProjects/truth-ledger
cp -R "$SRC" <dest> && cd <dest> \
  && git checkout -- AGENTS.md \
  && rm -f docs/reviews/agents-md-review-handoff-2026-08-26.md
```

The prompt is in the repository and does survive. The tree must be COMPLETE:
a curated subset of files is itself a specification, and handing one to a
reviewer destroys ADR-062 rule 1.

---

## Ordered

**1. Today's catch-log entries.** The only item that loses value by the hour:
rule 5 makes a same-day entry `cmd` or `hist`, and the same fact a week later
only `test`.
*Four are owed:* `waiver-index` catching `TRUTH_BATTERY_PLAN` unclassified
minutes after it was written; a timing measurement broken by a `cd` leaking
out of `eval`, whose three zeros were read as results (an L0 error by the
author of the crib, hours after writing it); `reproduce` catching ADR-057's
two orphaned claims, but only at the push boundary two weeks late; and the
structural miss behind it — **there is no decision → dependent-claims
direction**.
*Done when:* the entries are in `docs/governance/catch-log.md` and its two
tables still balance against the census.
*Decays if:* a later session files them from memory — then they are testimony
and rule 5 says so.

**2. Dispatch both reviewers.** R1 is running. R2 is not, and its handoff is
untracked.
*Done when:* both have returned findings.
*Decays if:* either reviewer is given the brief. Then it is a conformance
check wearing a review's name and the finding count means nothing.

**3. Fix and commit the plan-mode change WITH its review.** ADR-062 rule 3 —
the review travels with the change. This is why the three green files sit
uncommitted.
*Files:* `scripts/release-battery.sh`, `.githooks/pre-push`, `docs/waivers.md`.
*Done when:* one commit carries the change and the review document.
*Decays if:* the change is committed alone. Then the evidence against it can
be separated from it, which is the thing rule 3 exists to prevent.

**4. `AGENTS.md`.** The oldest debt here. Read first by every agent, nine
documented defects, **one of them in the committed file** (the `mkrepo`
paragraph, stale in the pessimistic direction).
*Done when:* the redraft is committed with R2's review, and the nine are each
either fixed or recorded as refused with a reason.
*Decays if:* it stays uncommitted much longer — every session that reads it
inherits the defects, so this one breaks all future work rather than one task.

**5. Repoint the thirteen scope arms onto plan mode.** This is where the
measured cost actually falls.
*Measured 2026-08-26:* the whole battery at `SCOPE=ALL` is **666s**; every
named stage sums to **91s**; the battery meta-gate is therefore **575s, 86%
of a push**. Plan mode answers the same scope question in **0.014s**.
*The judgement, per arm:* is its subject the SELECTION (goes to plan) or the
EXECUTION (stays)? The mutation arms that prove a broken battery goes red
must keep executing.
*Done when:* a push under `SCOPE=ALL` is under three minutes AND
`scripts/test-release-battery.sh` still reports every arm proven able to fail.
*Decays if:* item 3 has not landed — this must review a stable base, not a
moving target.

**6. ADR-062 rule 5, proposed not implemented.** *A change that turns red into
green by DECIDING rather than by FIXING is an operator action. An agent may
prepare it; it must mark it as such and may not close it.*
*Why it is owed:* on 2026-08-25 an agent resolved three rulings that had been
named twice as the operator's, and the exit code that made them visible went
green in the same move. The work was good; nothing said stop.
*Done when:* the rule is in ADR-062 with a red-gate condition, or a written
refusal explaining why it cannot be gated.
*Decays if:* written by the agent that overstepped, or by the author of the
open-design section already in that file.

**7. The roof — one assurance case.** A top claim, four to six subclaims,
every existing instrument assigned to a leaf. GSN or CAE, ISO/IEC 15026-2.
Roughly a day.
*Why last, and why it is nonetheless the only item that ADDS anything:*
items 1–6 are debt. This one answers the question the debt cannot: *what is
all of this evidence FOR?* It is last because it describes a tree that today
has five uncommitted changes and two reviews in flight — written now it would
document a state that will not exist in two days, which is the failure it
exists to prevent.
*Done when:* every instrument in `docs/registers.md` names the leaf it serves,
and every leaf carries a **defeat condition** — what would kill it, not what
supports it.
*Decays if:* it acquires a diagram before it acquires defeat conditions. Then
it is theatre and the disorientation returns better documented.

---

## The ordering principle, so a later session need not re-derive it

Two criteria, in this order: **what decays**, then **what blocks what**.

Item 1 decays hourly. Item 2 unblocks 3 and 4 and costs nothing to start.
Item 5 is the largest measured saving but must wait for a stable base. Items
6 and 7 are the only ones with no external dependency, and 7 is deliberately
placed after the debt rather than before it.

## What is deliberately NOT here

* Twelve of fifteen instruments have caught nothing (`docs/governance/catch-log.md`).
  That is not an item until the census has run long enough for zero to mean
  something. Rule 4 of the catch log holds it.
* `docs/STRUKTURALNY-ATLAS-EPISTEMICZNY.md` — resigned by operator ruling
  2026-08-26, removed from the index rather than baselined.
