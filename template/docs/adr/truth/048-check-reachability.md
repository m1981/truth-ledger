# ADR-048: Check reachability — a check no scheduled root invokes is prose

Status: **Accepted** (2026-08-02)
Date: 2026-08-02
Parent: ADR-042 (check liveness — coverage is part of every verdict);
this record implements the half ADR-042 did not name and leaves the rest
of ADR-042 PROPOSED (see *Relationship to ADR-042* below).
Evidence: the 2026-08-02 migration audit,
`docs/reviews/migration-audit-2026-08-02.md`.

## Context

Three independent adversarial audits of the P0–P6 migration found that
the repository — whose whole thesis is mechanized detection — had added
four test suites that **nothing invoked**: `scripts/test-fact-health.sh`,
`scripts/test-session-digest.sh`, `scripts/test-instruments.sh` and
`scripts/test-whisper-hook.sh`. Worse, the tiering release (ADR-046) had
*retired six proven canary arms into* one of them by name — an honest
ceremony pointing at an unreachable destination. Every reported number
went up while automated coverage went down.

ADR-042 already names the adjacent defect — a check that runs and
examines nothing — and the release battery already enforces its first
rule. Neither covers this one. A suite that passes when a human runs it
by hand is not a measurement of the repository's health; it is a
**statement about** the repository's health sitting in a file. That is
the same category error §5 of the paper identifies in restated facts:
*facts restated in prose rot; facts cited by id stay checkable*. The
generalization the audit forced:

> **Passing and being scheduled are independent properties, and only the
> first was ever measured.**

## Decision

**A check that no scheduled root invokes FAILS, the same way a check that
examined nothing fails.** Concretely:

1. **`scripts/gate-reachability.sh`** enumerates every git-tracked
   executable check mechanically (never a hardcoded list, which silently
   falls behind), enumerates the **scheduled roots** — this repo's active
   `.githooks/*`, the harness hooks in `.claude/settings.json`, and
   `template/scripts/install-hooks.sh` as a *template* root because the
   hook bodies it writes run on a schedule in every consumer — and
   computes reachability as a **transitive closure to fixpoint** (the
   real chain `pre-push → release-battery → truth-canary → doc-health` is
   three hops; a hop cap would have been a lie).
2. **Unreachable is a failure**, excusable only by a committed entry with
   a stated reason in `.truth/reachability-opt-out`, which follows the
   ADR-037 policy-file semantics exactly: ABSENT is dark and voices a
   loud advisory, committed-EMPTY is a conscious "everything must be
   reachable" and is silent, POPULATED is armed. A *stale* excuse — an
   entry naming a path that is not a check, or one that is now reachable
   — also fails, so the opt-out list cannot rot into permanent cover.
3. **The sweep applies to itself**: it is in its own enumeration, prints
   its own reachability path, and fails if it is not enumerated, not
   reachable, or examined zero checks.
4. **The four orphans were wired, not excused.** The opt-out file ships
   committed-empty: every dark check had a schedule available. Each rides
   the battery through a `gate_arm` helper that judges the suite by its
   own `N caught, M missed` line — no summary is a failure ("died before
   reporting"), zero caught is a failure ("examined nothing", ADR-042
   rule 2), missed>0 or non-zero exit is a failure.
5. **The battery's own mutation gate rides the battery**, scoped to
   pushes that touch it, guarded against re-entry by a variable set at
   exactly one line and announced when it suppresses (`skip battery
   meta-gate -- re-entrant run under the outer battery`). It is not an
   operator skip flag; `git push --no-verify` remains the one honest,
   reflog-visible emergency exit (the ADR-011 lesson: a second, softer
   bypass is the hook teaching its own workaround).

## Relationship to ADR-042

ADR-042 requires "an independent adversarial pass and a simulation
against the existing checks" before acceptance. Both now exist: three
independent audits, and this sweep's first run, which found five dark
checks including the battery's own gate. Of ADR-042's five rules, 1
(report what you examined) and 2 (zero coverage fails) are enforced for
every wired suite by `gate_arm`, and 5 (an arm is not credited until seen
red) was practiced throughout this remediation. Rules **3** (doctor
becomes the armed-versus-dark auditor) and **4** (every audit field names
its consumer) remain unimplemented, so **ADR-042 stays PROPOSED** with a
dated note rather than being accepted on partial delivery — recording
more than shipped is the defect this whole round exists to close.

## Consequences

- The dark-check class closes structurally. Adding a suite and forgetting
  to wire it now fails at the push boundary, in the same run that would
  have shipped it.
- Cost: the battery grows from ~9s to ~17s on an ordinary push, and to
  ~6m19s on pushes that touch the battery, its gate, or the pre-push
  hook. Measured, not estimated.
- Two coarsenesses are accepted and recorded rather than hidden:
  variable-built dispatch reads as unreachable (fail-safe direction), and
  path-tail matching reaches mirrored meta/template files together.
- No fold change, no schema change, no new record kind.

## Non-goals

Not judging whether a check's *schedule* is appropriate — only whether one
exists. "Should this run on every push or only on release?" needs a
judgment and is therefore a review, not a gate. Not deciding sufficiency
of coverage (ADR-042 non-goal, inherited). Not preventing a human from
deleting a root: `doctor` (ADR-025) owns hook wiring, and this sweep
assumes the roots it is told about.
