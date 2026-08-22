# ADR-055: the churn floor refuses, and structural selector targets are exempt from both watch budgets

Status: **ACCEPTED** (2026-08-22, operator ruling) — accepted OVER an unmet
condition, and the record says so rather than tidying it away. ADR-039 made
the advisory→refusal promotion conditional on operator evidence (≥30 days of
forecast-versus-observed churn) that was never produced, and refactor step 2.5
made "observed stalings" unmeasurable, so the condition is not merely pending
but unsatisfiable in its original form. The operator reviewed the code and
ruled that the architectural soundness of the churn floor and the structural
exemption outweighs the missing evidence: *"We accept the residual risk."*

What that leaves open, stated for whoever audits this later: the threshold
itself is still unvalidated by data. Nothing here claims it is calibrated —
only that it is accepted. Superseding this record with a calibrated threshold
remains the honest end state.

Originally filed PROPOSED (2026-08-18, agent-authored) and deliberately not
self-accepted; the agent's refusal to accept its own record stands as written.
Date: 2026-08-18

Amends: **ADR-039** (the blast forecast and the churn report — advisory only),
twice. First by ratifying the advisory→refusal promotion that shipped in FAZA 3
step 3.2 without the record ADR-039 required of it. Second by carving an
exemption class out of that refusal.

Cites: ADR-032 (override decay — the second exit both budgets offer),
ADR-037 (the generated-artifact refusal, whose bypass the same change closed),
ADR-049 (the three-part refusal test, and "a gate must not teach its own
bypass"), ADR-030 (judgment laundering).

---

## Context

**ADR-039 severed a refusal gate and said what would bring it back.** The
rev-1 proposal shipped a refusal above a fixed threshold of 15; measured then,
**82 of 96 path-carrying claims would have refused**. ADR-039 severed it,
shipped the forecast as an advisory, and wrote the condition verbatim:

> The refusal gate deliberately does not ship. It returns only as its own
> future ADR after ≥30 days of forecast-vs-observed data.

**The refusal shipped anyway, without that ADR.** FAZA 3 step 3.2 (`79750ed`,
`0dbfc87`; J-038, J-039) promoted the floor to a blocking gate,
`paths-churn-budget`, alongside a cardinality budget of one freehand path. Two
things about how that landed are on the record and belong here:

* The seeded-fault suite **detected the contract change and was changed to
  match it**. J-039: *"Canary BF1 padł: arm oczekiwał advisory ADR-039, a
  dostał odmowę."* The immune system fired; the response was to update the arm.
* No record was written, and at that moment none **could** be: the ADR corpus
  had been archived and the runbook forbade new ADR files. `docs/decisions/`
  reopened that possibility on 2026-08-18, which is why this record is
  possible now and was not then. The gap is a consequence of the corpus split,
  not of anyone ignoring the practice.

**Why the promotion is nonetheless defensible, measured 2026-08-18 on this
ledger.** The population argument that killed rev-1 does not hold against the
self-calibrating floor:

| | threshold | refused | of | share |
|---|---|---|---|---|
| ADR-039 rev-1, fixed floor | 15 | 82 | 96 | **85%** |
| today, calibrated P90 floor | 46 | 14 | 79 | **17%** |

Of those 14, two already carry a policy or a stated basis, so **12 claims would
be refused on a re-file today**. A gate refusing 85% of its population is a gate
nobody can comply with; one refusing 17%, with two recorded exits, is a gate.
The calibration is what changed the answer — not a softer opinion about churn.

**The second half: sub-tree targets.** FAZA 3's structural anchors (`be0b4da`)
let a watch target name part of a file: `package.json#/dependencies/stripe`.
Both budgets then face a question ADR-039 could not have had: how do you price
a target that is *narrower* than a path?

---

## Decision

**1. Ratify the churn floor as a refusal** (`paths-churn-budget`), with the two
exits step 3.2 gave it — `--watch-policy <name>` and `--paths-ok "<sentence>"`
— and with the ADR-032 decay on the second. Conditional on the operator
resolving ADR-039's evidence clause (see Open question).

**2. A watch target carrying a `#selector` is exempt from both budgets:** it is
not counted against `MAX_FREEHAND_WATCH_PATHS`, and the churn refusal is
decided over the selector-free subset of the watch set only.

The exemption is argued, not granted:

* **The cardinality budget prices accumulation.** It exists because 75 claims
  held 60 distinct watch sets — sets accumulated rather than chosen. You cannot
  accumulate `/dependencies/stripe` by accident: the author names an exact key
  path or heading, and INV-M reads the file at intake to confirm it resolves.
  That is a narrower review than `--paths-ok` asks for, performed mechanically,
  one target at a time.
* **The churn floor measures the wrong object for a sub-tree.** `blast_forecast`
  counts commits touching the FILE. For `package.json#/dependencies/stripe` that
  is an upper bound so loose it is nearly noise: every dependency bump in the
  repo is inside it and approximately none move the sub-tree. Refusing on it
  would refuse the very narrowing the gate asks for — the author narrows a hot
  glob to the key their recipe reads, and the gate that demanded the narrowing
  then refuses the narrowed version because the file underneath is still hot.
  By ADR-049 that is a gate teaching its own bypass, and the bypass it teaches
  is "go back to the wide glob".
* **The costs differ in kind.** A freehand path costs a whisper line on every
  edit AND a false `capsule-stale` whenever any byte of the file moves. A
  selector target costs the whisper line but not the false stale, because
  `truth reproduce` compares the sub-tree digest. Charging both at one rate
  prices precision like breadth.

**3. A selector-free path in the same set is still judged, on both arms.** The
exemption attaches to the target, never to the claim. A mixed set
`package.json#/deps/stripe, template/**` is judged on `template/**` exactly as
if the selector target were absent.

**4. ADR-039's advisory keeps the file-level number.** The refusal is decided
over the selector-free subset; `ctx["blast_forecast"]` is deliberately not
modified. The wide number is still TRUE as an upper bound, and a selector claim
on a genuinely hot file is worth a line of prose. It is not worth a refusal.

---

## Consequences

* The exemption class is **currently empty in this repository**: measured
  2026-08-18, 0 of 79 active path-claims carry a selector. This repo's recipes
  grep whole documents (`grep -q 'A' doc && grep -q 'B' doc`), so anchoring
  them to a section would make the watch narrower than the evidence. The
  exemption is forward-looking here and pays in consumer repos that have a
  `package.json`. Recorded so nobody reads the empty column as a defect.
* A selector target that stops resolving is refused at INTAKE, not at first
  read, by three INV-M arms (selector-on-a-glob, unsupported format, resolves
  to nothing today). The last one reads file content — the only INV-M arm that
  does — and costs one read per selector target.
* Closing the same change: appending `#/a/b` to a generated path was a
  one-character bypass of ADR-037, because `_gate_generated` matched
  `evidence_paths` as the subject. Fixed with a regression test.
* **The floor self-tightens.** It is a percentile of the live population, so as
  wide sets are narrowed the floor falls and the bar rises. A set legal today
  can be refused next month with no code change. The two exits are what keep
  that survivable: a reviewed policy is never re-litigated, and a stated basis
  is re-asked on the ADR-032 clock rather than at random.

## Open question for the operator

ADR-039 conditioned the refusal on **≥30 days of forecast-vs-observed data**.
That comparison has not been produced; what exists is the population
measurement above, which answers a different question (how many claims the
floor refuses) than the one ADR-039 asked (how well the forecast predicts
observed stalings). Two honest resolutions:

1. **Waive it with a reason.** Step 2.5 retired path-invalidation, so "observed
   stalings" no longer exist as a series to compare against — the metric
   ADR-039 asked for was made unmeasurable by a later decision, not skipped.
   If that is the operator's reading, this record moves to Accepted saying so.
2. **Satisfy a successor metric.** Compare forecast against `truth reproduce`'s
   `watched-moved` arm over 30 days, which is the surviving observable.

Until one is chosen, this record stays PROPOSED and the gate keeps running —
that state is disclosed here rather than hidden, which is the point of writing
the record late instead of not at all.

## Alternatives considered and rejected

* **Leave the exemption undocumented, as code comments only.** It lived that
  way from `be0b4da` until this record. Rejected: an exemption from a refusal
  is exactly the kind of decision a reader needs to find from the outside, and
  `gates.py`'s comments are only visible to someone already reading the gate.
* **Refuse selector targets on the file-level forecast anyway.** Rejected under
  ADR-049: it makes the gate unsatisfiable in the direction it points.
* **Exempt the whole claim when any target carries a selector.** Rejected: it
  would let one precise target launder an arbitrarily wide glob beside it.
* **Write this as an amendment to ADR-037 instead.** Rejected: ADR-037's
  subject is generated artifacts; the bypass fix belongs to it, but the budget
  exemptions are ADR-039's subject.
