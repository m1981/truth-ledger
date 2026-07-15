# Field notes — multi-agent worktree deployment (kuchnie pilot, 2026-07-15/16)

> Reader: anyone revising the paper (v3 input) or hardening the template
> for concurrent-agent regimes | Enables: citing observed ledger behavior
> under a NEW deployment shape — several agent sessions in git worktrees
> of one repository, merged by a supervising session | Update-trigger:
> v3 absorbs these, or a later run contradicts one

Provenance: the pilot repo's first supervised multi-agent run (four
implementation/investigation agents + one dispatched verifier, one
supervisor). Same operator as the paper — §8 item 1's caveat extends to
everything here. Pilot-side retro:
`kuchnie/docs/reviews/multi-agent-supervision-retro-2026-07-16.md`.

## Observations with paper relevance

1. **Filer≠verifier produced a productive deadlock (ADR-010 consequence,
   unanticipated).** A session filed a successor claim, then a later
   commit in the same session edited a watched path — the claim
   self-staled, and the session-separation gate correctly refused its own
   filer's re-affirmation. The only exit was dispatching an independent
   verifier session. Consequence worth stating in v3: in a
   claims-intensive session, verifier dispatch is structurally required
   at close, not a hygiene nicety. The dispatched verifier also
   self-corrected on the record (filed diverge, re-read the diff,
   filed a reasoned corrective agree) — dispatch-only context did not
   prevent it from reasoning about supersession lineage.
2. **Merge-order semantics under worktrees.** An agent re-affirmed staled
   claims inside its worktree; the supervisor's later merge into main
   fired the invalidate-scan with a LATER timestamp, so the union-merged
   agree events were correctly outranked and the claims re-staled. The
   `(ts, id)` fold behaved exactly per spec — but the operational lesson
   is non-obvious: worktree-side re-affirmations near merge time are
   wasted work; re-verify on main after merging. Candidate one-liner for
   the operating conventions (§9).
3. **Two §9 conventions recurred as live defects** in pre-convention
   claims: a claim watching a GENERATED artifact (restaled on every
   regeneration of it; the pilot codified "watch sources, never generated
   artifacts" as a local rule) and a claim whose evidence used `grep -n`
   (line numbers shifted under an additive edit → mechanical divergence,
   ADR-012's class, resolved on the record). Both suggest §9 items may
   deserve intake-time warnings rather than prose: flag `-n` in evidence
   commands; flag paths matching a repo-declared generated-artifact list.
4. **Six sessions interleaving one ledger again held** (four agents +
   supervisor + verifier; appends via CLI in worktrees and main, merged
   by union) — zero corruption, fold confluent after merges. Extends §2's
   concurrency evidence to the worktree topology, same machine, same
   operator.
5. **Decaying satisfaction observed in the wild.** The pilot's
   requirements-completeness gauge (R7, two-ledger concept Phase 1)
   showed a completion claim degrade to non-live and recover within one
   day — the "satisfaction is derived and decays" behavior the two-ledger
   RFC (nd-/satisfies) proposes to make first-class. Named v3 trigger
   material: this plus the deadlock above are two of the trigger
   conditions listed in the pilot's concept doc Part III.
6. **Gate refusals concentrated on the most-capable actor.** The
   supervising session (largest model in the run) tripped more intake and
   commit gates than the subordinate agents — consistent with the
   paper's thesis that the regime targets honest-actor error rates, and a
   caution against exempting "senior" sessions from any gate.

## Not evidence

Agent stall/restart behavior (four watchdog/API interruptions) says
nothing about the ledger — noted only because interrupted sessions left
the ledger consistent every time: the failure mode was omission (a
missing handoff message), never corruption, matching the loophole map's
bottom line.
