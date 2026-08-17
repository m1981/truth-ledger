# ADR-047: Every blocking gate carries an adoption metric and a review date

Status: Accepted (2026-08-02, operator) — decision D5 of the migration
plan, the P6 "gate governance" phase and its close. Docs-only
(v0.9.31): no CLI, schema, or gate-semantics change. The registry this
ADR mandates lives meta-repo-side at docs/governance/gate-metrics.md
(operational review state, not shipped machinery — the ADR-003
placement test); the rule itself is template policy and binds every
future gate ADR in this series.
Date: 2026-08-02
Extends: ADR-032 (the precedent: re-ask a judgment on a schedule),
ADR-033/046 (the Tier C instruments the metrics read), ADR-034 (the
gate table being governed). Supersedes: —

## Context

The standing question after the gates adoption (ADR-034–039) and the
migration is "is this overengineered?" — eleven Tier B refusal/advisory
surfaces now stand between an agent and the ledger, each shipped on an
argument, none carrying an obligation to keep justifying itself. The
repo already knows what happens to judgments with no expiry: ADR-032
made `--scope-ok` bases decay on a date, because an override that is
never re-asked degrades into background permission. A gate is the same
object one level up — a judgment that some failure mode is worth
refusing — and it degrades the same way: a gate that never fires is
either working perfectly or guarding nothing, and without a metric
nobody can tell which, so the table only ever grows. Tier C exists
precisely to answer this (ADR-046: instruments are "the research half
that judges whether B pays"), but nothing obliged Tier B to consult it.

## Decision

**1. Metric or it doesn't ship.** Every Tier B blocking gate and every
counted override carries, in the gate-metric registry: a **named
adoption metric**, a **data source** (a Tier C instrument or a `truth
stats --json` key — never a hand count), and a **next-review date**.
The registry row is part of the gate's definition of done.

**2. New gates enter PROPOSED with a metric or not at all.** The
growth-gate discipline applied to the gate table itself: a gate ADR
that cannot name what number would prove it pays (or prove it dead) is
not ready to be a gate. ADR-039 already modeled this — its refusal
half deliberately did not ship, deferred to "a field window of
forecast-vs-observed data"; that posture is now the rule.

**3. Reviews ride the existing R11 monthly hand-audit slot.** Zero new
ceremony: the audit that is already due opens with the registry table,
pulls current values from the instruments, and writes its minutes into
the registry. No new meeting, no new report format, no new schedule —
a gate review that needed its own ceremony would itself fail this ADR.

**4. The retirement test is three questions.**

1. Has the gate had a real opportunity to fire?
2. When it fired, did anyone act on it?
3. Does the failure it guards still exist in the declared regime?

Retire on a **mature "never"** to 1–2 (mature: the opportunity window
has actually elapsed — a detector waiting on decay cycles that cannot
have completed yet gets a dated probation, not a verdict) or on a
**"no"** to 3. A gate that fires and is acted on stays; a gate that
fires into silence is alarm fatigue being manufactured; a gate whose
failure mode left the regime is dead weight regardless of its history.

## Evidence

The first review (2026-08-02, minutes in the registry) exercised every
branch of the test on live data: ADR-033's verbatim-repeat detector
drew the dated-probation arm (0 decay expiries yet — its firing
opportunity cannot have occurred before the first 30-day TTLs lapse,
so "never fired" is immature by construction, reviewable 2026-10-08);
G8 drew the keep arm with data (11 overrides across 198 filings, 5.6%,
far under ADR-007's ~50% recalibration line, and the override cluster
is a single legitimate re-anchoring batch — the gate firing correctly);
and the 3650-day scope-TTL outlier was traced to a specific retracted
claim, converting a standing "someone should look at that number" into
one queued operator action. Three different verdicts from one table is
the process working — a debate produces none of them.

## Consequences

- "Is it overengineered?" now has a standing, dated, data-fed answer
  process instead of a recurring argument: every gate is either
  justified by its row or on a clock toward retirement.
- The registry is meta-repo review state; consumers receive the gates
  and this rule, not the minutes. A consumer adopting the discipline
  starts its own table over the instruments' pure cores
  (truthlib/advisory.py).
- Known gaps become findings, not folklore: the first review recorded
  `--single-run` (G6) as the one uncounted override — a
  registry-tracked item, not a new gate. The cost is one row per gate
  and one audit agenda item per month; if that ever feels heavy, the
  table is telling you which gates to retire.
