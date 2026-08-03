# ADR-049: a retraction records WHY, and the why owes a successor

Status: Accepted (2026-08-03, operator) — prompted by a measurement of
75 real retractions in the pilot ledger (2026-08-03) and 96 in this
repo's own. Implemented in CLI v0.9.34, schema `$id` v0.17. Core tests
TestRetractionCause + TestRetractionCauseValidateMirror; canary FAULT
RX (10 arms incl. a negative control, two ordering arms and the
validate mirror).
Date: 2026-08-03
Amends: — . Extends: ADR-011 (the tombstone ceremony gains a
pre-ceremony argument check — deliberately *before* the typed-id
confirmation, and the refusal keeps ADR-011's surface rule: it names
no env-var ritual, and there is no override for it to name),
ADR-012 (the mechanical-divergence subtype is what a drifted *recipe*
records; this ADR deliberately does not duplicate it as a cause),
ADR-036 (the second gate on the same verb; the pure check precedes the
git-consuming sweep), ADR-043 (the decision is a pure core predicate,
`retraction_cause_error`, beside `supersede_error` — the shell
gathers, calls, exits), ADR-046 (envelope admission: the field is
admitted because a blocking gate reads it), ADR-047 (ships with a
named metric, a Tier C data source, and a review date). Cites:
ADR-026 (`$id` v0.17 — the verdict shape changed), ADR-027 (the
cross-field rules are mirror-only), ADR-013 (`--successor` is
CLAIM-level and does not touch per-issue premise redirection).
Supersedes: —

## Context

`verdict <id> retracted --basis "<prose>"` accepted any sentence. What
the field actually wrote, measured over the pilot's 75 retractions:

* **49 (65 %) record no readable cause at all** — boilerplate, including
  one batch of 18 byte-identical bases and another of 21
  (`"superseded; successor in verdict trail"`).
* **39 of 75 name no ledger id**, while claiming in words that a
  successor exists. "In the verdict trail" is not followable: nothing
  can resolve it, so the pointer is decoration.
* Of the 26 that do carry a cause, four flavours were visible by hand:
  never-true (10), recipe-pointed-at-the-old-place (7),
  the-defect-was-repaired (6), a-version-pin-moved-on (3).

This is what a required field with no obligation degrades into. It is
the ADR-032 shape one level up: a judgment that is never re-asked and
never checked becomes background ceremony. And it is expensive in a
specific way — retraction is the system's strongest promise (G12,
terminal, human-only), so the ledger's *most consequential* event is
the one with the least recoverable record of its reason.

## Decision

**1. The vocabulary is a truth table, not a survey.** `--cause` takes
one of exactly three values, derived from two yes/no questions about
the retracted *sentence*:

| | ever true? no | ever true? yes |
|---|---|---|
| **still true? yes** | *impossible* | `restated` |
| **still true? no** | `wrong` | `expired` |

2 × 2 minus the impossible cell = **three values, exhaustive and
mutually exclusive by construction**, decided by two questions that
need only the sentence in front of you. A core test pins the set at
three: a fourth value means the *questions* changed, which is an ADR,
not a constant edit.

* `restated` — the sentence still holds; a successor states it better.
* `expired` — it was true and the world moved past it.
* `wrong` — it was never true, or its evidence never demonstrated it.

**2. `restated` must name a successor — the one blocking rule.**
`--successor <tr-id>` must be a ledger id, differ from the retracted
claim, exist, and not itself be retracted (a tombstone cannot carry a
fact forward). Under `expired`/`wrong` a successor is *optional*: 10 of
the pilot's causal retractions are `wrong` **with** a corrected
successor ("overstated scope; superseded by tr-b270996f"), and refusing
that would be a false refusal.

This rule is the point of the whole ADR. A claim that is still true is
a **live belief**; killing it with nothing carrying the fact forward is
a silent deletion, and it was invisible under prose. It is also what
admits the field under ADR-046: `cause` is not report-only metadata — a
blocking gate reads it.

**3. Refuse, not warn — and the argument, because ADR-037 went the
other way.** ADR-037's recipe lints are warnings on principle ("a gate
refusing legitimate filings teaches its own bypass" — ADR-014's
confused-deputy lesson). Three properties make this gate the other
case, and all three are the reasons ADR-037 gave:

* *Volume.* The lints fire on every filing; this fires on 75 events in
  a 2,135-record ledger (3.5 %), on a verb that is already interactive
  and already ceremonial. There is no fatigue budget to spend.
* *Decidability.* The lints are heuristic — a `-n` may be legitimate, a
  version literal may be a deliberate pin — so they can be *wrong about
  the world*, and a refusal that is wrong teaches its own bypass. This
  gate judges nothing about whether the cause is *correct*; it only
  requires that one be stated, and the question is always answerable by
  the only actor permitted to run the verb. It cannot produce a false
  refusal, so it cannot teach one.
* *Evidence.* The warn-equivalent has already been run as an
  experiment. "Say why you retracted" was a documented convention with
  no teeth for 75 trials and produced no readable cause in 65 % of
  them. ADR-037's warnings have not been measured to fail; this
  convention has. ADR-035 is the precedent for hardening a measured-
  failing advisory into a gate over the decidable slice.

**No override flag.** No `--cause-ok`. Unlike ADR-036's sweep — which
consults the world and can be wrong about it — this gate asks a
question the retracting human can always answer, so an override would
be the invisible opt-out ADR-032 declined for `--no-ttl`. The canary
asserts the flag's *absence* as a property (RX2).

**4. Position: before the ceremony.** `retraction_cause_error` is pure
(no I/O; the fold is already in hand) and runs **first** — before
`human_ack_error`, before the ADR-036 sweep. A malformed invocation
must never consume a typed-id confirmation: being told "you forgot a
flag" *after* typing the id back would degrade exactly the deliberation
ADR-011 exists to create. This is `verdict`'s own ordering rule — cheap
argument checks precede the tombstone ceremony — the one ADR-043's
L2-F6 propagated to `done`. The human gate is otherwise untouched:
every rung of the ADR-011 ladder still refuses with a valid `--cause`
present (RX3), and `TRUTH_HUMAN_ACK` still authorizes exactly one id.

**5. Back-compat: required at intake, tolerated by validate, visible in
the report.** Absent `cause` on a retraction is valid **forever**, in
both contract surfaces. Three reasons, in order of force:

* `validate` runs *inside* the pre-commit gate. A mirror that refused
  history would not "flag old records" — it would wedge every commit in
  every consumer repo holding one, permanently, with no legal repair
  (the ledger is append-only; rewriting it is forbidden).
* Intake-stricter-than-validate is the **safe** direction. v0.9.32
  fixed the unsafe one: intake weaker than validate let a normal verb
  append a line the commit gate then rejected. Everything intake now
  produces, validate accepts.
* ADR-046 already established the pattern in the other direction
  (`concerns`: legacy-admitted, closed to new records). This is the
  same permanence with the polarity reversed.

Legacy records are **not** silently dropped: `retraction_cause_report`
counts them under a fourth, never-stored key, `unrecorded`. That is the
F1 fail-loud rule applied to a denominator — during the crossover the
readable number is "how many retractions still have no cause", and it
is only readable if the legacy population stays in the report. At
adoption it reads 96 of 96 here and 75 of 75 in the pilot.

`validate` does refuse, on new records: a `cause` outside the enum, a
`successor` that is not a `tr-` id (both shared with the schema and
carried by the FS-2 corpus), and — mirror-only, ADR-027, the
`orphan_basis` precedent — a `cause` or `successor` on a non-retracted
verdict, `restated` with no successor, and either field on an
`issue_event`.

## Explicit non-goals — residuals owned

**`moved` is not a cause, and that is the deliberate difference from
the four labels the measurement named.** A claim whose *recipe* drifted
while the fact held is, by the two questions, **still true** — so it
lands in `restated` and owes a successor, which is precisely the
correct operation: fix the recipe on a new claim, then retire the
predecessor. All four mechanically-diverged retractions in the pilot
already did exactly this, naming a live successor. A `moved` cause
would have blessed the other branch — tombstoning a live belief because
its measuring command went stale — and that is the deletion this ADR
refuses. It is not refused by *name* (a rejected label teaches nothing;
the author simply picks another), but structurally: the successor
requirement is what makes the misuse impossible to file.

**`fixed` and `version` are one value.** Both say the sentence was true
and is no longer; they differ only in *who* moved the world — us, or
the calendar. Nothing in the fold, any gate, `ready`, the queue, or any
report reads that difference, so under ADR-046's admission rule it is
not a distinction this system may store. The measurement agrees on the
weak side: `version` appeared 3 times in 75.

**No fifth cause.** The truth table has no free cells. What the
measurement *did* miss is not a cause but a *refusal*: a retraction of a
still-true claim with nothing succeeding it was unnameable in prose and
is therefore uncounted in the 75 — it could be hiding anywhere in the
49 unrecorded, and from v0.9.34 it cannot be filed at all.

**The `wrong`/`expired` split is not read by any gate today** — only
`restated` is. It is admitted as part of the same gate-read field
because it is what makes the gate's own question decidable (an author
who cannot say whether the sentence was ever true cannot reliably say
whether it is true now), and because it is the ADR-047 metric that
tells the *rest* of the gate table whether it pays: `wrong` counts
filings that should never have passed intake, which is the adoption
number ADR-035/007/INV-M have never had. If a review finds the split
unread and unused, it collapses to two values by narrowing the enum —
no schema shape change, no migration.

**Out of scope:** `done --cancel`. A cancelled issue is work abandoned,
not a belief killed; "was the sentence ever true" has no referent. The
mirror refuses both fields on an `issue_event` so they cannot creep
onto the other tombstone verb without an ADR. Also out of scope: any
new obligation on ADR-013's premise redirect — a `wrong`-caused premise
arguably deserves harder treatment than an `expired` one, but that is a
change to ADR-013's contract and needs its own argument.

**Not enforced:** that the stated cause is *true*. A `restated` on a
fact that actually died is a lie the system cannot detect, and the
successor pointer is the attack surface a verifier reads — the same
posture as every `--basis` in this ledger.

## Adoption gate (ADR-047)

Metric: **`unrecorded` share of retractions**, and **`successors_missing`
under `cause=restated`** (which must be structurally zero — a non-zero
value means a raw append bypassed intake). Data source:
`instruments/retraction-causes.py --json` (Tier C, over the raw
ledger). Next review: **2026-11-03**, in the R11 monthly slot.
Retirement test: if `unrecorded` has stopped growing *and* `restated`
is never chosen across two consecutive reviews, the successor
requirement is guarding nothing observed and the gate drops to two
values plus an advisory.

## Consequences

The ledger's most consequential event stops being its least legible
one, and the 65 % boilerplate class dies at intake rather than at a
future reader's expense. The `wrong` tally becomes the first honest
answer to "does the gate table pay?" — a number nobody could count
before. Record shape changed (`cause`, `successor`) → `$id` v0.17,
mirror rules, and the shape-fingerprint pin moved in the same diff
(ADR-026). Cost: one flag on a verb run ~75 times in a year, and one
genuinely new refusal — retiring a still-true claim now requires
filing its replacement first.

**Canary faults (FAULT RX).** RX1: a causeless retraction refuses,
prints the two-question tree, appends nothing. RX2: the refusal names
no env-var ritual and no `--cause-ok` exists to name (ADR-011's surface
rule; override-absence as a property). RX3: every ADR-011 rung still
refuses with a valid `--cause`, and a missing cause refuses *before* the
ceremony. RX4: `restated` with no successor is refused, nothing
appended. RX5: successor integrity — shape, self-reference, unknown id,
and a successor that is itself a tombstone. RX6: the happy path stores
both fields. RX7 (**negative control**): a clean `expired` retraction
files silently, exit 0, empty stderr, no `successor` key. RX8: both
flags refused on a recoverable verdict. RX9 (**ordering**): a
retraction that is both causeless *and* cited refuses on ADR-049, not
exit 6 — the pure check precedes the git sweep and nothing ran. RX10:
`validate` still admits a causeless LEGACY retraction, and refuses
`restated`-without-successor, `cause`-on-agree, and `cause` on an
`issue_event`.

Falsifier: a retraction filed with a cause that a verifier, reading the
claim and its successor, would call the wrong one — at a rate showing
the two questions are not in fact cheap to answer correctly.
