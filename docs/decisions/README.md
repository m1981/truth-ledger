# docs/decisions — the live decision register for this repository

> Reader: anyone recording, amending or citing an architectural decision in the meta-repo | Enables: writing a new decision record without touching the frozen archive, and finding the record that amends an archived one | Update-trigger: a record is added here, or a record here amends an archived ADR (add the row to the reverse index below)

This directory is the **live** half of a two-tier decision corpus. Records
numbered **054 and up** live here and are written normally. Records **001-053**
are frozen verbatim at `docs/archive/adr/` and are never edited again.

## Why the corpus is split

On 2026-08-16 the 54 machinery ADRs were moved out of `template/` into
`docs/archive/adr/` (commit `687dbdc`, human-authorized; J-010, J-026, J-027,
J-028). That move was right for the reason it was made: `template/` is the
product copier ships, and decision records about the development of this
machinery are not consumer documentation. The consumer's architecture surface
is `template/docs/ARCHITECTURE.md`.

What the move did **not** intend, and what this directory repairs, is the loss
of the practice. `docs/archive/` is frozen verbatim (`AGENTS.md`, and the
`.githooks/pre-commit` guard that enforces it), so after the move there was
nowhere to write a new record at all — the runbook drew the only conclusion
available to it and forbade new ADR files. Two orthogonal things had been
welded together: *not part of the product* and *no longer a living practice*.

The underlying cause was a missing category. This repository's scope taxonomy
had two classes — live prose (judged today) and frozen reference (never
judged) — and a decision register is neither. Its Context sections legitimately
cite claim ids that were live **then**; its status line and its amendment graph
bind **now**. Given two buckets, `docs/archive/` was the least-bad destination
and J-027 reasoned correctly within that constraint. This directory adds the
missing third position rather than reversing the move.

## Numbering continues; it is never restarted

New records continue the single number space at **054**. The space is not
restarted and archived records are never renumbered. Two reasons, both hard:

1. Code cites decisions by number. Measured 2026-08-18: 51 distinct `ADR-0NN`
   identifiers across `template/truthlib/`, `template/scripts/`, `scripts/`
   and `instruments/`.
2. Ledger citations are immutable. `docs/archive/adr/README.md` records the
   collision that established this: a consumer repo where the template's
   ADR-001 and the project's own ADR-001 met in one directory, and immutable
   ledger citations made renumbering impossible.

## Nothing here ships

This directory is meta-repo-only. It is deliberately outside `template/`, so
`copier update` never carries it to a consumer. A consumer's own decisions
belong in that consumer's own `docs/adr/`, in a number space of its own.

## Header convention

Carried forward unchanged from the archived corpus:

    Status:      Accepted | PROPOSED | Superseded by ADR-0NN  (+ date, who)
    Date:        YYYY-MM-DD
    Amends:      ADR-0NN  (this record narrows or corrects part of that one)
    Extends:     ADR-0NN  (builds on it without contradicting it)
    Cites:       ADR-0NN  (referenced in the argument, not modified)
    Supersedes:  ADR-0NN  (this record replaces that one wholesale)

A record that amends or supersedes an archived ADR **must** add its row to the
reverse index below, in the same commit.

## Reverse index — the forward pointer the freeze forbids

An ADR normally announces its own obsolescence: the superseded record gains a
`Superseded by:` line in its header, and a reader who arrives at the old record
is sent to the new one. `docs/archive/` is frozen verbatim, so an archived ADR
**cannot** carry that line. A reader arriving at `docs/archive/adr/025-*.md`
would otherwise have no way to learn that it has been amended.

This table is that pointer. It is the only place the archive-to-live edge is
recorded, which is why adding the row is not optional.

| Archived record | Amended / superseded by | Relation | Date |
|---|---|---|---|
| `ADR-025` commit-gate decidability | [`ADR-054`](054-doctor-resolves-delegated-gate.md) | Amends — the hook arm resolves one hop of delegation | 2026-08-18 |
| `ADR-039` blast forecast — advisory only | [`ADR-055`](055-churn-floor-refusal-and-structural-exemption.md) | Amends — ratifies the advisory→refusal promotion (PROPOSED: ADR-039's evidence clause is unresolved) and exempts selector targets | 2026-08-18 |
| `ADR-041` shell-free evidence execution (PROPOSED, "NOT implemented") | [`ADR-056`](056-shell-free-evidence-execution-implemented.md) | Amends — records what actually shipped, answers its four open questions, and states that decision 3 does NOT close R4a as its text claimed (PROPOSED: the independent adversarial pass ADR-041 required has not happened) | 2026-08-18 |
| `ADR-019` TTL expiry semantics | [`ADR-057`](057-read-time-ttl.md) | Amends — ADR-019's arithmetic is untouched (count from the claim's own `ts`, strict boundary), but its mechanism is replaced: the `ttl-scan` writer it ratified as "the sole clock reader" is removed and expiry is derived inside `fold(events, now_dt=…)` (PROPOSED: not independently reviewed) | 2026-08-23 |

## Rules

* **Write new records here.** Never add a file to `docs/archive/adr/`; a record
  appended to an archive stops it being an archive.
* **Never edit an archived record**, including its status line. The freeze is
  enforced at the git layer and exists because norms alone did not hold
  (J-027). Do not pass `--no-verify`.
* **An amendment is a new record plus an index row**, never an edit in place.
* Records here are live prose: `scripts/fact-health.sh` sweeps
  `docs/**/*.md` and this directory is not excluded, so a claim id cited here
  is judged against the ledger like any other living document. Cite live ids
  only, or name the id inside a fenced block if you mean it historically.
