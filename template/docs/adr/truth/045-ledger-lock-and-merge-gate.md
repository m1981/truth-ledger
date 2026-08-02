# ADR-045: Write verbs serialize on a ledger lock; merge commits join the gate

Status: Accepted (2026-08-02, operator) — decisions D2 and D3 of the
migration plan, the P4 "write path + hooks" phase. Implemented in CLI
v0.9.29: no verb, flag, schema, or fold change; every existing refusal
message and exit code byte-identical.
Date: 2026-08-02
Supersedes: — (extends ADR-008/031's order coherence and ADR-025's
gate decidability; no prior decision reopened)

## Context

**R10 — the intake-gate TOCTOU catalogue.** Every write verb loads the
ledger, decides against the fold, then appends. `O_APPEND` keeps the
*bytes* safe under concurrent appends (paper §1), but nothing kept the
*decisions* coherent: between one process's fold and its append, a
second same-machine writer could land the duplicate the G8 screen had
just ruled out, flip the live/dormant state `contradicts` had just
read, or advance the issue state machine under a transition check.
Each gate was sound against the ledger it read and unsound against the
ledger it wrote to.

**R5 — the ungated merge commit.** git runs `pre-merge-commit`, never
`pre-commit`, when a merge auto-commits — and a merge auto-commit is
exactly what the union-merge sync story produces when two sessions'
branches meet. install-hooks.sh wired only pre-commit and post-merge,
so the one commit class the sync path guarantees was the one class
INV-A/INV-B never screened. The P0 union-merge canary arm pinned the
ungated behavior and deferred its gate assertion to this phase.

## Decision

**D2 — one `flock` around the whole verb.** `main()` wraps
`args.fn(args)` for every verb in `WRITE_VERBS` in
`shellio.ledger_lock()`: an exclusive `fcntl.flock` on
`<git-dir>/truth-ledger.lock` (`LEDGER_LOCK_NAME`), held from before
the load to after the append. Load→gates→append is one critical
section; the read verbs (including `validate --stdin`, which runs
inside the commit gate) never touch the lock. Blocking acquire, no
timeout: flock state is kernel-owned and dies with its holder's
process, so a crashed holder cannot orphan the lock, and the wait is
bounded by the FS-3-priced critical section. The lock target is a
separate file — never the ledger fd, so the audited single-`write(2)`
O_APPEND path (TestAppendSingleWrite) is untouched — and lives in the
git dir like `.git/truth-whisper.seen`, deliberately not beside the
ledger: the `.truth/.claims.lock` draft dirtied every `git status` and
red-flagged the session-close survival gate at first canary contact.

**D3 — the third hook.** install-hooks.sh writes `pre-merge-commit`
with the same `exec bash scripts/check-truth.sh` body as pre-commit
(and its hooksPath-refusal guidance names it for hook-manager users).
`doctor` WARNs — never FAILs, adoption-gated: pre-v0.9.29 installs
lack the hook blamelessly — when a local pre-commit gate hook exists
without a check-truth pre-merge-commit; CI-arm repos are exempt, their
gate runs server-side on push/PR where merge commits arrive like any
other. Union-merged ledgers *are* prefix extensions of `ours`, so the
gate passes honest merges and blocks tampered ones — canary UM5-UM7
verify both directions through the real installer: the honest
bidirectional sync auto-commits through the gate; a branch that
rewrites an early committed line (landed with `--no-verify`) is
refused at the merge commit.

## Consequences

* Same-machine writers are now *gate-coherent*, not merely
  corruption-safe: no append can slip between a gate's fold and its
  write. Disclosure updated in paper §1 and loophole-map §E.
* Disclosed, not solved: **multi-machine** concurrency is unchanged
  and untested (§8 item 4 stands — flock is per-filesystem, and git
  sync between machines was never inside the lock's reach); an
  ADR-014 acceptance oracle that itself runs a write verb against the
  *same* repo would self-deadlock (oracles are suites by design;
  canary sandboxes are separate repos and unaffected); and the hook,
  like every local hook, is conditional on installation — the ADR-025
  posture, now decidable for this hook too via doctor's WARN.
* Red-proven at adoption: the lock commented out of `main()` reddened
  FAULT LK; the hook deleted from the sandbox let the tampered merge
  land and reddened UM7; the doctor check removed reddened the WARN
  arms.
