# ADR-043: The status vocabulary and satellite blocking sets are one exported contract

Status: Accepted (2026-08-02, operator) — the P2 "contracts before
carving" layer of the migration plan, prompted by the architecture
review's converged findings R13 (registry gaps), R14 (refusals escaping
the gate-table contract), R7 (hand-copied intake flag surface) and R6
(impure advisory orchestrator). Implemented in CLI v0.9.27 (no schema
change; refusal messages, exit codes and derived statuses byte-identical
— the licensed additions are `truth vocab` and `done --json`, plus the
L2-F6 check reorder in `done`).
Date: 2026-08-02
Supersedes: — (extraction and export; no fold or gate semantics change)

## Context

The R1 incident is the natural experiment: when `disputed` joined
STATUSES, every gated copy of the status vocabulary stayed correct and
both hand copies drifted — spec-health and fact-health kept passing prose
that stood on disputed facts. The review then counted the copies: six
bare `("live", "unverified")` tuples, three inline verdict→status maps
with three different unknown-verdict behaviors, two satellite blocking
sets maintained by eye. Separately, two policy-file loaders `sys.exit`ed
two frames below a gate table whose stated contract is "gate fns return a
refusal string"; the ADR-013 supersede and issue-#4 contradicts intakes
decided inline in shell verbs under a "makes no decisions" banner; and
`intake_advisories` ran subprocesses under the "PURE CORE" banner while
re-probing facts the gate rows had already gathered.

## Decision

**One exported contract, consumed at runtime; decisions in the core.**

1. **Registry constants** (R13): `ACTIVE_STATUSES` and `VERDICT_STATUS`
   replace every hand copy. Unknown-verdict behavior stays deliberately
   split per consumer (fold KeyError, half-life silent skip, stats
   uncounted): unifying it is a semantics change, out of scope here.
2. **`truth vocab [--json]`** exports the machine vocabulary. The
   premise sets are DERIVED by evaluating `premise_check` over
   STATUSES × TIERS — the vocab cannot drift from the ADR-001 matrix
   because it is the matrix, evaluated. `CITATION_BAD` is exported as
   the satellites' blocking contract and consumed by nothing else in
   the CLI. Read verb: not in WRITE_VERBS, no banner.
3. **Satellites consume at runtime**: spec-health's `CLAIM_BAD` and
   fact-health's `BAD` are fetched via one `truth vocab --json` call per
   sweep, failing LOUD (exit 2) when the call fails — never a silent
   fallback to a hardcoded set (the F1 rule).
4. **Loaders return errors** (R14a): `load_citation_scope` and
   `load_generated_globs` return `(globs, source, err)`; the generated
   gate returns the error per the gate-table contract and the citation
   verbs exit it at the cli level, bytes unchanged.
5. **Non-claim intakes decide in the core** (R14b): `supersede_error`
   (with the `RETRACTED_NEEDS_ACK` sentinel — the ADR-011/017 human ack
   is I/O and stays in the shell) and `contradicts_intake_error`; the
   verbs are thin gather-call-exit shells.
6. **`intake_advisories` is pure** (R6): the shell gathers
   `generated_source` / `porcelain` / `shallow_state` once, reusing the
   gate rows' own ctx stashes; `add_claim_intake_flags` deduplicates the
   `claim` / `done --claim` flag surface (R7), `done` gains `--json`
   (SI-3 at claim-at-death), and `done` checks `--basis`/transition
   before the tombstone ceremony (L2-F6, `verdict`'s order).

## Evidence

Removing `disputed` from `CITATION_BAD` in the red-run reddened canary
VC1, the S2D spec-health arm, and the fact-health disputed case
together — the drift that R1 caught by hand is now caught by three
independent gates sourcing one constant. Core suite 257→286 (each new
class mutation-reddened once); canary 240→243 (FAULT VC ×2, GS6).

## Consequences

- The R1 class is structurally closed for the satellites; a future
  status joins every consumer by joining STATUSES and the registry.
- Satellites now depend on the CLI answering `vocab` — a broken CLI
  stops the sweeps loudly instead of letting them judge from memory.
- P3 (the package split) can move these functions as files: every
  contract this phase extracted is named, exported, and pinned.
