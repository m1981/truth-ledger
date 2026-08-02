# ADR-046: Tier C instruments leave the template; the envelope earns an admission rule

Status: Accepted (2026-08-02, operator) — decision D4 of the migration
plan, the P5 "tiering" phase. Implemented in CLI v0.9.30 with the
phase's single schema bump ($id v0.15 → v0.16). This is the one
migration phase that deliberately changes consumer-facing behavior:
report surface is REMOVED; fold, statuses, refusal messages, exit
codes, and every gate are unchanged.
Date: 2026-08-02
Supersedes: — (demotes the ADR-039 storage half and the v0.9.15
concerns surface; ADR-010/033/039's *reports* stand, re-homed)

## Context

The target shape's tier model (§6): **Tier A** is the kernel every
consumer runs; **Tier B** is governance each gate must justify with a
metric; **Tier C** is instruments — the research half that *judges
whether B pays*. Three report families and one metadata surface were
living in Tier A without ever being product:

* the `stats` **separation / overrides / blast** sections (and
  doctor's "verifier separation" check) — instruments read by the
  monthly hand-audit, shipped to every consumer;
* **`concerns`** tags — triage metadata never read by the fold, any
  gate, `ready`, or the queue: pure envelope weight (X3/X5 leak class);
* **`blast_forecast`** — a number stamped into permanent records that
  nothing ever read back except the report beside it, computable at
  read time from the same single `git log` intake paid to stamp it.

The pattern needed a rule, not just a cleanup, or the envelope regrows.

## Decision

**1. The envelope admission rule.** *A payload field is admitted only
if the fold or a blocking gate reads it.* Report-only data lives in
Tier C instruments, never in records. Written into the schema header
and docs/truth-ledger-machinery.md. Grandfathered as PASSING: the
override bases (`scope_basis`, `generated_ok_basis`,
`evidence_exit_basis`, `orphan_basis`, `overridden_duplicates`) and
`ttl_default` — gates stamp them and reviews/decay read them.
`concerns` and `blast_forecast` FAIL the rule.

**2. `concerns` → Tier C (D4).** `claim --concern`, `list --concern`,
and the stats concerns section are removed; `concerns_intake_error` is
gone. `CONCERN_RE` and `claim_concerns` stay — validate's legacy
branch and the reader instrument need them. The field is
**legacy-admitted**: this repo's ledger holds pre-ADR-046 records that
carry it, append-only history is never rewritten, so `validate` and
the schema keep accepting (and shape-checking) stored tags — and it is
**closed to new records**: no verb stamps it, and hand-editing tags
into the ledger is forbidden (that would rewrite history AND smuggle a
field past the rule). Reader: `instruments/concern-tag.py` (stdlib,
over `truth list --json` + the raw ledger). If triage returns, it
returns as a Tier C sidecar store, never as payload.

**3. `blast_forecast` computed on read.** Intake stops stamping it;
`_gate_blast` is advisory-only (computes the forecast live, passes it
and the parsed history through `facts` to the CC-1 advisory).
`effective_blast_floor(claims, history)` calibrates P90 from live
forecasts over live path-claims — one `blast_history()` log, N pure
matches, same git cost as the stored-int read it replaces; the ≥1
clamp and fallback stand, and None history (shallow/unavailable) never
calibrates. Stored ints on legacy records stay validate-admitted;
`blast_report(events, folded, history)` reports them only when history
is unreadable.

**4. Reports out of `stats`/`doctor`.** `stats` keeps exactly the
Tier B core: claims_by_status/by_tier, verdicts, half_life (feeds the
FS-1 intake advisory), queue_size/age — plain and `--json`. The pure
reports (`separation_report`, `override_report`, `blast_report`) STAY
in truthlib/advisory.py; the meta-repo drivers are
`instruments/separation-report.py`, `instruments/override-velocity.py`,
`instruments/blast-report.py` (thin, `--json`-capable, NOT templated).
Doctor's "verifier separation" check is retired with them.

## The canary-arm ledger (retired BY NAME → replacement)

| Retired | Replacement |
|---|---|
| canary SEP1, SEP2, SEP3 (FAULT SEP) | scripts/test-instruments.sh separation lane (incl. SEP3's negative control) |
| canary FAULT OV stats arms (verbatim-repeat advisory + narrowed negative control) | test-instruments.sh override-velocity lane (identical expiry/repeat fixture) |
| canary BF5 (stats blast section render) | test-instruments.sh blast lane (floor + live observed-vs-forecast rows) |
| canary BF4 (asserted blast_forecast stored) | FLIPPED in place: asserts NOT stored + BF1 advisory still voices + legacy line validates (item 3's red-proof) |
| core TestConcernsCLI (6 tests) | test-instruments.sh concern-tag lane + core test_legacy_tagged_and_forecast_records_still_admitted |
| core TestOverrideReportCLI (2 tests) | test-instruments.sh override-velocity lane; pure TestOverrideReport never moved |
| core test_stats_report_concern_tally | concern-tag instrument arm (sandbox tally) |
| core test_slug_hygiene (drove concerns_intake_error) | test_slug_shape_guards_the_legacy_validate_branch (drives CONCERN_RE) |

Arm accounting: canary 251 → 245 (−SEP1/2/3, −OV×2, −BF5; 0 added —
replacements live meta-repo-side); core 298 → 293; NEW
test-instruments.sh: 16 arms (real-ledger lane + one red-proof lane
per instrument, each seeded fault named or the gate reddens).

## Consequences

* Consumers adopt a smaller surface: `stats` is counts/verdicts/
  half-life/queue; no `--concern`; records shrink by one stamped int.
  The meta-repo keeps every instrument, now explicitly Tier C — the
  layer whose job is to answer "does Tier B pay?" (P6 wires the
  gate-metric reviews onto them).
* Legacy tolerance is permanent, not transitional: pre-ADR-046 records
  validate forever (append-only history); both schema properties carry
  deprecation notes; the FS-2 mirror/corpus lockstep rode the single
  $id bump (v0.16).
* Blast floors now describe *today's* window, not filing-day snapshots
  — on this repo's ledger the calibrated floor moved 15 (fallback) →
  63 (calibrated) at cutover, which is the instrument getting more
  honest, not churn.
* Red-proven at adoption: the payload stamp restored reddens BF4 and
  the instruments-gate not-stored arm; each instrument's report logic
  patched out reddens its seeded-fault lane; a regrown stats section
  reddens TestStatsCLIShape.
