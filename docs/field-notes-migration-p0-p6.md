# Field notes — the P0–P6 target-shape migration (session of 2026-08-01/02)

Dated session record (sweep-excluded by the fact-health scope rule: ids
cited here were live during this session and will age — that is what
field notes are for). The durable artifacts are in-repo: ADR-043..047,
CHANGELOG v0.9.27–v0.9.31, `docs/governance/gate-metrics.md`,
`docs/governance/operator-actions-2026-08.md`.

## What happened, in order

A four-lens adversarial review (architecture, design, robustness,
testing — four independent sessions, findings coordinator-verified)
found the repo's meta-claims one notch stronger than its code at the
seams: satellites drifting on a hand-copied status matrix (`disputed`
passed both sweeps as ok), "atomic" `done --claim` as two write calls,
sensors reading their own death as zero, canary arms that could not go
red, and the sync story never driven through a real `git merge`. The
operator ruled on five open decisions (package split; adopt flock;
install pre-merge-commit; concerns to Tier C; govern gates rather than
retire), and a seven-phase migration executed them: oracle repair →
live fixes → contract layer → `truthlib/` package split → write-path
lock + merge gate → tiering with the envelope admission rule → gate
governance. Each phase: one implementer subagent, coordinator diff
review + independent suite runs, commit only on green, and the ledger's
own blast → reaffirm → dispatch cycle completed before the next phase.

## Closing numbers

v0.9.26 → v0.9.31 · canary 231 → 245 arms (every changed arm
red-proven; −6 retired by name into `scripts/test-instruments.sh`) ·
core suite 254 → 293 · four new satellite gates (fact-health 10, digest
3, whisper +2, instruments 16) · schema `$id` v0.16 · 3,594 ledger
records, 67 live, fact-health 0 failures · battery green at full scope
on close · session-close: 0 failures, 2 WARNs (both pre-existing debt,
below).

## Traps this session actually hit (for the next one)

- **`git checkout -- <file>` during a red-proof restore wipes your own
  uncommitted edits.** Three implementer agents hit it independently;
  all recovered. Use cp-backups for mutation restores, never checkout.
- **A re-filed claim's sentinel string must be re-read, not just its
  endpoint test.** The coordinator filed `SERIES-DENSE-001-042` under a
  043 sentence; self-diverged per ADR-010 and re-filed. Test every
  recipe by running it AND reading its echo before filing.
- **Version-pin claims (ADR-count, explainer-sync, check-truth sha) die
  at every version bump by design.** The ceremony is: file successor
  (test recipe first) → swap citations in live prose → fresh-session
  verify. Budget it into any release.
- **The instruments read filings, not folded status** — the "3650-day
  TTL outlier" belonged to an already-retracted claim. Check folded
  status before escalating an instrument reading.
- **A worktree-sibling lock file dirties `git status`** and trips the
  session-close gate; machine-local state belongs under the git dir
  (ADR-045 records the reversal).

## Open state handed to the operator

- `docs/governance/operator-actions-2026-08.md`: 31 preflighted
  superseded-predecessor retractions; one statement-obsolete retraction;
  the 3650-day-TTL policy ruling; 27 pre-migration diverged claims to
  dispatch-or-retire.
- The two session-close WARNs are pre-existing: 15 unverified claims
  (GitHub-issue spec claims and research measurements, none filed by
  this migration) and the 57-item queue (dominated by the
  superseded-predecessor pool awaiting the human retirement above).
- Not yet pushed or tagged: the pre-push battery is green; the
  tag-check will prompt for a v0.9.31 tag.
- R11 monthly audit (~2026-08-08) opens on the gate-metrics registry;
  ADR-033 probation review dated 2026-10-08.
