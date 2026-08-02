# Audit of the P0–P6 target-shape migration — 2026-08-02

> Reader: the truth-ledger operator, and the next session that opens
> `docs/field-notes-migration-p0-p6.md` | Method: three independent
> adversarial sessions, read-only, run at HEAD after the migration
> closed — (A) target-shape conformance, (B) phase-plan conformance,
> (C) unconstrained gap-hunt | Subject: the seven-phase migration
> P0–P6, v0.9.26 → v0.9.32 | Date: 2026-08-02 | Disposition: every
> finding below carries one of *fixed in this pass* / *open* /
> *accepted*, and the code-side fixes landed in the same session as
> this record.

Frozen reference: this file records what was found on 2026-08-02 and
is excluded from the `fact-health.sh` live corpus for that reason (the
`docs/reviews/` scope rule). Do not "update" it as the repo moves —
file a successor record.

## Verdicts, one line each

- **(A) Target-shape conformance.** ~85–90% of the target shape
  delivered as designed or as a *recorded* deviation — the deviations
  that exist are written down, which is the property that was being
  tested.
- **(B) Phase-plan conformance.** The delivery was "rigorous about the
  code it changed and lax about the evidence machinery that was
  supposed to hold it accountable." Fit as a code migration; short as
  a self-audited one.
- **(C) Adversarial gap-hunt.** "I would trust this delivery" — one
  minor finding, no defect that survives contact with the suites.

Three verdicts, one direction: the code is in the shape the plan
describes; the *proof* that it is in that shape was thinner than the
plan promised, and thinner in ways nobody had written down until this
record.

## Method

Each session ran fresh, read-only, with no access to the others'
findings and no expectation seeded by the implementer's own summary.

1. **(A) Target shape.** Diffed the delivered repo against the target
   architecture the migration set out to reach — package boundaries,
   tier placement, gate table, hook wiring — and classified every
   difference as *delivered*, *recorded deviation*, or *unrecorded*.
   The score is the third bucket's size.
2. **(B) Phase plan.** Walked the seven phases in order against what
   each phase committed to produce, including the non-code
   deliverables: ledger issues, acceptance oracles, per-phase claims,
   CHANGELOG entries, canary arms. Re-derived the phase-boundary
   numbers rather than reading them off the summary.
3. **(C) Gap hunt.** No brief beyond "find what is wrong". Attacked
   the fold, the CLI's refusal surface, the distribution path and the
   ledger's own separation discipline directly, by execution and by
   differential, not by reading.

## What the audits verified positive, with the evidence

These are the load-bearing negatives — the places where a migration of
this size usually breaks, checked and found intact.

- **The fold is byte-identical across the migration.** An AST diff over
  the P3 package split found **143 of 143 top-level definitions
  identical**; the single change anywhere in fold territory is the
  licensed substitution of the `VERDICT_STATUS` constant, with the
  `KeyError` behavior on an unknown verdict preserved. The whole point
  of P3 was to move code without moving semantics, and that is what the
  diff says happened.
- **The canary progression corroborates at every phase boundary.**
  231 → 235 → 240 → 243 → 243 → 251 → 245 → 247 arms, each step
  matching the phase that claimed it (the 251 → 245 step is the ADR-046
  tiering retirement, arms named by name, not arms lost; the 245 → 247
  step is v0.9.32's two new arms). Three of those steps are
  independently restatable from `template/CHANGELOG.md` alone
  (240 → 243, 251 → 245, 245 → 247), which is what makes the sequence
  checkable rather than reported.
- **Every headline suite count reproduced** on an independent run — no
  number in the closing summary is a number only its author has seen.
- **Three defenses were re-mutated and observed red.** Not "the arm
  exists" but "the arm fails when the thing it guards is removed" —
  the only version of that claim worth anything (F1).
- **The refusal surface is unchanged where it was supposed to be.** A
  byte-level differential of the pre-migration CLI against HEAD shows
  the G8 near-duplicate, ADR-007 quantifier-scope and INV-M dead-watch
  refusals firing on the same inputs with the same messages. A
  reorganization that quietly softened a gate is the failure mode; it
  did not happen.
- **Separation discipline holds across the whole ledger.** An
  independent scan of **all 1,640 `agree` verdicts** found **0
  same-session agrees** — no claim in this repo has ever been verified
  by the session that filed it. (Re-checked while writing this record:
  `truth stats --json` reports `verdicts.agree: 1640`.)
- **No silently-stale live claim.** All live path-carrying claims were
  re-scanned against their watched paths: **0 silently stale**. (The
  scan counted 66; the fold reports 67 live at this writing, every one
  path-carrying — the population moved by one filing between the scan
  and this record. Stated rather than smoothed: the count is a fact
  about a moment.)
- **Distribution still works.** A copier scaffold simulation produced a
  working consumer repo from the migrated template — the split into
  `truthlib/` did not break the thing the template exists to do.

## Findings, ranked

Each: what it is, which of this repo's own rules it violates, and its
disposition.

### 1. Three test suites invoked by nothing — automated coverage decreased

Three suites exist, pass, and are run by no gate, no battery, no hook.
Six canary assertions were *moved into* one of them during the tiering
phase and named as retired-into-a-satellite — which is the honest
ceremony, except the satellite is not wired to anything. Net effect of
a migration whose stated purpose included strengthening the seams:
automated coverage went **down** while every count went up.

Rule violated: the ADR-046 tiering bargain — an arm may leave the
canary *into a gate*, not into a file. A suite that nothing invokes is
documentation with an exit code.

**Disposition: fixed in this pass** (sibling agent, `scripts/` +
`instruments/`).

### 2. `cli.py` imports `subprocess`, contradicting ADR-044's own module table

ADR-044 publishes a module table stating which layer may touch the
process boundary. The delivered `cli.py` imports `subprocess` anyway.
Small in effect, exact in kind: the decision record and the code
disagree, and the code won silently.

Rule violated: ADR-044's module table, and the general rule that a
decision record is normative or it is decoration.

**Disposition: fixed in this pass** (sibling agent, `template/`).

### 3. `instruments/concern-tag.py` re-introduced a hand-copied status tuple

The exact drift class ADR-043 was written to close — a satellite
carrying its own copy of the status vocabulary, which passes both
sweeps right up until the day the vocabulary changes under it (the
`disputed` episode). Closed by ADR-043 in P2 via the runtime
`truth vocab --json` contract; reopened in a Tier C instrument in the
same migration.

Rule violated: ADR-043 (one contract, consumed at runtime, never
hand-copied) — violated by the migration that shipped it.

**Disposition: fixed in this pass** (sibling agent, `instruments/`).

### 4. The release battery's pass/fail logic changed in P0 with no arm in its own mutation-proof gate

`scripts/release-battery.sh` decides what "green" means for a release.
Its decision logic was edited in P0; its mutation-proof gate
(`scripts/test-release-battery.sh`) gained no arm for the new logic. A
sensor whose judgment changed without a proof that the new judgment can
go red is the dead-sensor shape the repo has already been bitten by
twice (R3 SC, F1).

Rule violated: the F1 rule — a changed sensor is proven red or it is
not proven.

**Disposition: fixed in this pass** (sibling agent, `scripts/`).

### 5. `truth doctor --json` was never built and never acknowledged

The plan carried it; the CLI does not have it; nothing anywhere says
so. This is the cheapest possible failure to avoid — one line in a
CHANGELOG entry converts it from a silent omission into a recorded
deviation, and the difference between those two is the entire subject
of this repository.

Rule violated: the recorded-deviation discipline (a deviation is
legitimate; an *unrecorded* deviation is not).

**Disposition: fixed in this pass** (sibling agent).

### 6. The plan's ledger-discipline promise was dropped entirely — OPEN

The migration plan committed to auditing itself with the machinery it
was migrating: `wk-` issues per phase, acceptance oracles, a completion
claim at each phase boundary. Delivered: **zero `wk-` issues, zero
acceptance oracles, zero per-phase completion claims.** The line "the
migration audits itself with the machinery it migrates" describes
something that did not happen.

This is the one finding that is **not** being fixed by editing code,
and it must not be retro-fitted either: filing seven completion claims
today, after the fact, from the session that did the work, would
manufacture exactly the evidence the discipline exists to prevent
(ADR-010 — the author is not the verifier; a claim filed after the
outcome is known is a claim about a memory).

There is a second-order symptom worth naming: **the plan itself is not
in the repo.** No file under `docs/` or `template/docs/` states what
the seven phases promised, so the only durable record of the promise is
this paragraph. That is why finding 7's "silently corrected premise"
below could not be checked against a source — there is no source.

Rule violated: the plan's own acceptance criteria, and the repo's
first premise — that work is gated on the health of the facts it
depends on, including its own.

**Disposition: OPEN.** Recorded, not repaired. The honest repair is
prospective: the *next* multi-phase change files its issues before it
starts, or the promise is dropped from the plan template instead of
from the delivery.

### 7. Minor — four small ones, mixed disposition

- **A two-versions-stale glossary line in the explainer.** The CLI
  glossary entry in `docs/truth-ledger-explained.md` stated a version
  two releases behind the same file's own Scope header. **Fixed in this
  pass**, and fixed by *removal*: the entry now cites the Scope header
  and the CHANGELOG instead of restating a version (paper §5 — a
  restated fact rots, a cited one stays checkable). Note for the next
  reader: the Scope header is pinned by a ledger sentinel, but the
  glossary line was pinned by nothing — the ADR-026 lockstep test
  covers the README title, the loophole map, the operations guide,
  `check-truth.sh` and `cli.py`, and does **not** cover this page.
- **`text-nonempty` (G0) and `class-precheck` (G4) missing from the
  gate registry**, which claims ADR-047 §1 coverage of "every Tier B
  blocking gate". The first pass enumerated *counted overrides* and
  treated "has an override flag" as the membership rule; two hard,
  override-less refusals fell through. **Fixed in this pass** —
  `docs/governance/gate-metrics.md` now carries both rows, with the
  metric named honestly as *unmeasurable from the ledger by
  construction* (a refusal appends nothing to fold — the ADR-035 note,
  already the precedent for the INV-M row) rather than proxied by an
  invented number. The fix surfaced one further gap, recorded in the
  registry's addendum and left open: `text-nonempty` has no end-to-end
  behavioral arm.
- **No CHANGELOG entries for P0 and P1**, though both changed shipped
  template files. **Not fixed here** — the release ceremony is the
  coordinator's, and a records agent editing a released CHANGELOG entry
  would be the same category error this document is about.
- **The plan's 17% G8-override premise was silently corrected to
  5.6%.** The registry's first-review minutes record the measured
  value (11 `--duplicate-ok` filings across 198 claim filings) and
  reason from it correctly; what no document says is that the plan's
  premise had been *wrong*, by a factor of three, and that the decision
  it justified therefore rested on a number nobody re-derived until the
  review. Being right for a corrected reason is still worth recording.
  **Recorded here** — which is the whole of the available fix, since
  the plan is not in the repo to amend.

## The pattern the phase auditor named

> rigorous about the code it changed, lax about the evidence machinery
> that was supposed to hold it accountable

Every finding above except 6 and 7 is the same shape read at a
different magnification. The fold was diffed at the AST level; the
suites that would have caught a fold regression were left unwired. The
gates were reorganized without softening a single refusal; the registry
that governs the gates shipped missing two of them. Six canary arms
were retired *by name*, with the honest ceremony fully performed — into
a file nothing runs. This is not carelessness about correctness. It is
carelessness about the *second-order* question, and the second order is
the entire product here: a repo whose subject is "prove it" was, in
this migration, better at being right than at being checkable.

## The structural lesson

**Passing and being scheduled are independent properties, and only one
of them was measured.**

Every count this migration reported was a count of *passing* — arms
green, suites green, battery green at full scope. Nothing measured
whether the passing thing is *reached* by anything: no gate enumerates
its own suites, no test asserts that every `test-*.sh` is invoked by
some runner, and so three suites could pass forever without being run
and every reported number would stay true. A green suite that nothing
invokes reports the same colour as a green suite in the critical path.

The generalization, and the thing worth carrying into the next plan:
**an assertion's coverage is the product of its correctness and its
reachability, and the repo only had an instrument for the first
factor.** The same sentence, one level up, is finding 6: the phases
were executed correctly and were reachable by no ledger record, so the
work happened and the *evidence that it happened* did not. Both are the
reachability factor going unmeasured. A future gate that enumerates
every test script and refuses any that no runner names would close the
first; issues filed before the work, not claims filed after it, close
the second.

## What this record does not itself re-verify

Written by the records agent of the remediation session, not by any of
the three auditors. Two of the positives above were re-checked here
against the live ledger (`verdicts.agree: 1640`; the live-claim
population, which had already moved by one) and three of the canary
steps against the CHANGELOG. The remainder — the AST diff, the CLI
byte-differential, the re-mutations, the copier simulation — are
recorded as the auditors reported them, on three independent sessions
agreeing, and are reproducible by their stated methods rather than
re-run here. Where a number could not be traced to a source in the
repo, that is said above instead of smoothed over.
