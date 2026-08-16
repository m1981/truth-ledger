# ADR-042: Check liveness — coverage is part of every verdict

Status: **PROPOSED** (2026-08-01, drafted) — NOT accepted, NOT implemented.

> **Amended 2026-08-02 (post-audit).** This record's own acceptance
> preconditions are now met: the independent adversarial pass exists
> (three sessions, `docs/reviews/migration-audit-2026-08-02.md`) and the
> simulation ran (`scripts/gate-reachability.sh`'s first sweep, which
> found five dark checks — four orphaned suites plus this battery's own
> mutation gate). Of the five rules below, **1** (report what you
> examined) and **2** (zero coverage fails) are now enforced for every
> wired suite by the battery's `gate_arm` helper, and **5** (an arm is
> not credited until seen red) was practiced throughout the 2026-08-02
> remediation. Rules **3** (doctor as the armed-versus-dark auditor) and
> **4** (every audit field names its consumer) remain unimplemented, so
> this ADR stays PROPOSED rather than being accepted on partial
> delivery — recording more than shipped is the defect that round
> existed to close. The reachability half, which this record does not
> name, shipped as its own decision: **ADR-048**.
Written after a coverage audit and a mechanics review found that six of
twelve observed failure modes share one shape. Requires an independent
adversarial pass and a simulation against the existing checks before it
can be accepted. The first arm of it shipped ahead of the ADR, in
`scripts/release-battery.sh` (meta-repo, 2026-08-01), where every arm
already reports what it examined; this ADR asks whether that rule should
become general.
Date: 2026-08-01
Supersedes: — (generalizes the F1 audit law from ADR-004's audit round)

## Context

The 2026-08-01 review catalogued twelve failure modes actually observed in
one working session. Six of them are the same defect wearing different
clothes — **a mechanism that reports success while examining nothing**:

- **The dark gate.** ADR-036's citation gate reported "clean" for every id
  from v0.9.22 until 2026-08-01, because `.truth/citation-scope` was never
  committed and the built-in default `docs/specs/**` matches no tracked
  file here. ADR-037's generated-paths check was dark the same way. Both
  were built, tested, canary-pinned and documented.
- **The dark sweep.** `spec-health.sh` resolves zero files in this repo.
  `doc-health.sh` runs rooted at `template/`, so the meta-repo's own
  `docs/` tree — where every drift this month lived — is outside its view.
  Both exit 0.
- **The vacuous arm.** A canary arm added on 2026-08-01 grepped doctor's
  output for `grey-zone`, which matches its OK line as readily as its WARN
  line. The arm could never report a miss. Caught by an independent
  reviewer, not by the suite.
- **The unrun check.** The core suite was failing at HEAD, unnoticed,
  because nothing ran it.
- **The write-only audit.** `reaffirm_cleared` records what each of 595
  auto-agrees buried. It is written and read by nothing.

Each was patched individually. That is the wrong altitude: the repo has
now built five bespoke pins for one problem (the lockstep tests, the
schema `$id` fingerprint, fact-health, doc-health, the pre-push tag check)
and is about to build a sixth. The F1 audit law already states the right
principle — *a sensor that cannot work must scream, not fall silent* — but
it is applied by hand, per incident, wherever someone remembered.

## Decision (proposed)

**A check's result is a pair, not a boolean: `(verdict, coverage)`. A
check that examined nothing FAILS.** Concretely:

**1. Every check reports what it examined.** Not "ok" but "ok — 21
citations swept", "ok — 228 seeded faults caught", "ok — 6 pinned surfaces
agree". The number is the check's own claim about its reach, and it is the
only thing that distinguishes *passed* from *did not look*.

**2. Zero coverage is a failure, not a pass.** `fact-health` sweeping zero
citations, a canary reporting success over zero arms, a scope file
matching zero tracked files, a lockstep arm running zero tests — each is a
red result stating that the instrument is dark. This is the F1 law made
uniform instead of remembered.

**3. `doctor` becomes the auditor of armed-versus-dark.** It already
answers "is this repo correctly wired". It gains one table — check name,
its coverage probe, its expected floor — and fails when a shipped gate's
policy file is absent or resolves to nothing. An absent
`.truth/citation-scope` would have been a doctor failure from the day
ADR-036 shipped, rather than a silent default. Note the deliberate
asymmetry with ADR-037's existing convention: an EMPTY policy file is a
conscious statement and passes; an ABSENT one is dark and fails.

**4. Every audit field names its consumer.** A field written for
auditability with no reader is decoration. `reaffirm_cleared` is the
existing instance; `stats` should consume it, or it should not be written.
The rule binds future work too: any mechanism proposing a new recorded
field states what reads it.

**5. A test arm is not credited until it has been seen red.** The
mutation discipline used for `scripts/test-release-battery.sh` — each arm
verified against a deliberately broken copy — becomes the standard for new
canary arms. An arm nobody has seen fail is an arm that may be unable to.

## Consequences (anticipated — none of this is measured yet)

- The dark-gate class closes structurally rather than instance by
  instance, and the closure is visible in `doctor`'s output where the
  operator already looks.
- Some currently-green checks go red on adoption. That is the point, and
  it is also the risk: `spec-health` resolving zero files here is a true
  finding, but it will read as a regression. Adoption must therefore
  distinguish "dark because misconfigured" from "dark because genuinely
  not applicable to this repo", and the second needs a committed,
  conscious empty policy — the ADR-037 pattern.
- No fold change, no schema change, no new record kind. This is
  deliberately the cheapest structural fix on the table: it touches
  reporting and `doctor`, not the ledger's semantics.

## Non-goals

Not judging whether a check's coverage is *sufficient* — only whether it
is non-zero. "Is this the right corpus?" needs a model and is therefore a
review, not a gate (the house rule). Not replacing the individual checks.
Not addressing the failure modes that are genuinely different in kind:
sentence-outruns-evidence (ADR-007's genus, procedural — see the verifier
protocol), version literals forcing generation-rolling, the enumeration
problem behind ADR-041, or fleet-state facts having no trigger.

## Sequencing of the wider findings (not part of this ADR's decision)

Recorded here so the order is legible; each item is its own decision.

1. **Done 2026-08-01.** Guard-rail sentinels on the control surfaces;
   `.truth/citation-scope` and `.truth/generated-paths` committed; the
   release battery at the push boundary.
2. **This ADR** — the liveness rule, cheapest structural item, no fold
   change.
3. **ADR-041** (shell-free evidence execution) — the highest-leverage
   security item, and the prerequisite for any design that widens
   automatic execution. Its three demonstrated channels remain open.
4. **Version-literal intake refusal + formal supersession** — the largest
   attention win (half of claims carry a version literal; 44 of 49
   retractions are supersession bookkeeping), but supersession changes the
   fold and needs the full ADR-016 confluence treatment.
5. **The refs sweep** — one table-driven resolver for every typed token,
   replacing five bespoke pins. Report for one calibration release before
   it becomes a gate; fact-health's 108-to-0 recalibration is the
   precedent for why.
6. **Fleet state** — deployment facts have only a TTL, which is a timer,
   not a detector. A watchable in-repo artifact would give them a trigger.
   No design yet.
