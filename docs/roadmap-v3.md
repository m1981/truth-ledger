# Roadmap v3 — post-review remediation

Status: living document. Created 2026-07-20 from three review rounds
(novelty review, red-team of orthodox redesigns, peer review) plus the
TLR counter-proposal reconciliation. Execution model: agent-implemented
batches; every batch must leave all suites green (test-truth-core.py,
test-truth-v04.py, truth-canary.sh — currently 159 / 13 / 166) and adds
its own regression tests. Nothing is committed by agents; the operator
reviews diffs and commits under the repo's own gate.

Statuses: TODO / IN-PROGRESS / DONE / OPERATOR (human-owned) / BLOCKED.

## Governing constraints (settled — do not re-litigate)

- Constraint budget: POSIX + git + Python3 stdlib, single-file CLI,
  solo operator, zero owned processes, compliant-agent threat model.
- Do-not-do list (red-team falsified): Lamport/causal ordering; linear
  prev_hash chain; sandbox replacing the evidence screen; 8-status
  collapse; work-kernel extraction; schema→mirror generation; unified
  override flag; scan-time auto-execution; hard exit-0 gate; fold cache
  before FS-3's trigger fires; signing before the growth gate trips.
- TLR reconciliation: the fork-permanent hash-tree design
  (TLR-002/013/014 + its oracle) is the NAMED growth-gate successor for
  §10, not a current work item.

## Batch 1 — hardening, smallest first (effort S) — DONE

- **R1 (A3) Exit-code warning at VERIFIED filing** — DONE
  (v0.9.11: pure predicate `evidence_exit_warning`, printed by `claim`
  and `done --claim` after the successful append; core tests
  TestEvidenceExitWarning.)
  Non-blocking: when the evidence command's intake runs exit non-zero,
  print a warning ("evidence exited N; a VERIFIED claim usually
  demonstrates its fact with a passing command") and file normally.
  Closes the hollow-VERIFIED silent channel (2 real instances).
  Accept: warning on exit≠0, silence on exit 0, no behavior change
  otherwise; unit tests for both; all suites green.
- **R2 (A4) Doctor banner on write verbs** — DONE
  (v0.9.11: doctor's hook detection factored into
  `git_hooks_dir`/`find_gate_hook`, shared by `commit_gate_wired`; pure
  `commit_gate_banner` over `WRITE_VERBS`, probed once in main(); core
  tests TestCommitGateBanner.)
  When doctor's commit-gate check (ADR-025 logic) would FAIL, every
  write verb (claim, verdict, issue, start, done, cancel, premise,
  invalidate-scan) prints a loud stderr banner. Never refuses. Read
  verbs and `validate --stdin` exempt. Cache the check per invocation
  (no per-verb git cost beyond one doctor probe).
  Accept: banner when unwired, silence when wired, exit codes
  unchanged; unit tests; suites green.

## Batch 2 — the churn fix (effort M) — DONE

- **R3 (A2) `truth reaffirm` batch verb** — DONE
  (v0.9.12, ADR-030: pure `reaffirm_triage` + the same screened recheck
  path as `verdict --recheck`; match auto-agrees with anchor=HEAD (F2),
  mismatch files NOTHING and is listed for dispatch; TTL / unscreened /
  never-agreed / same-session skip with reasons; --dry-run/--json; core
  tests TestReaffirmTriage+TestReaffirmCLI, canary FAULT RA.)
  In a verifier session: walk stale claims; for each path-staled claim
  run the existing deterministic recheck; on hash-match auto-file
  `agree` with basis "reaffirm: hash-match, no judgment re-run"
  (advancing the effective anchor, F2 semantics); on mismatch, list for
  real dispatch; skip + report TTL-staled (re-file path, ADR-019) and
  `screened:false` (never execute). Respects ADR-010 (runs as its own
  session; refuses claims authored by the same session).
  Accept: unit tests for all four triage arms; a canary fault proving a
  hash-mismatch is never auto-agreed; suites green; ADR documenting the
  verb (mechanical-reaffirmation vs first-verification distinction,
  extending ADR-012's vocabulary).

## Batch 3 — self-consistency (effort S) — DONE

- **R4 (A6a) Version tests over satellite docs** — DONE
  (v0.9.13: TestCrossSurfaceVersions +3 pins — the two docs/ `current:
  CLI vX.Y.Z` headers (skip when absent in a consumer copy) and
  check-truth.sh's "current CLI:" comment, which now states the gate
  CONTRACT as v0.4 separately since the script's semantics haven't
  changed; both docs' headers carry an honest "content last synced at
  v0.6.4 / v0.9.0" scope note — see Backlog.)
  Extend the ADR-026 version test to `docs/truth-ledger-loophole-map.md`
  and `docs/truth-ledger-operations-guide.md` `current:` headers and
  `check-truth.sh`'s version comment; update the three files once.
  Accept: test fails on any future drift; suites green.
- **R5 (A6b) Extract CLI changelog** — DONE
  (v0.9.13: ~505 history lines moved to template/CHANGELOG.md (shipped
  by copier; added to `_skip_if_exists` so a consumer's own CHANGELOG
  is never clobbered — N4 reasoning); the CLI keeps a ~20-line header
  whose line 2 still states the version for the ADR-026 test; nothing
  in the repo greps the removed docstring lines.)
  Move the version-history docstring (lines ~2–445) to `CHANGELOG.md`;
  keep a ~15-line header stating current version + pointer. The
  "file states its own version" property must survive (version test).
- **R6 (TLR adoption) Collapse duplicate-id forensics to one rule** — DONE
  (v0.9.13, ADR-031: order_check refuses ANY content-distinct duplicate
  id with one message; supersedes the detection halves of ADR-008/016
  only — fold order, clock-push, regression warning untouched; canary
  B1/B3–B5 expect the unified message, new FAULT K2 pins the later-ts
  flip to refused; core TestOrderCheck +3.)
  order_check: refuse ANY duplicate id whose content differs
  (content-equality test), regardless of ts relation — subsumes the
  backdated (ADR-008) and equal-ts (ADR-016) cases; byte-identical
  union-merge duplicates still pass. Needs a short ADR + paper §1
  "Fold semantics" touch + canary faults updated to expect the unified
  message. Corrections already require fresh ids, so no legitimate
  content-distinct duplicate exists.

## Batch 4 — paper v3 (effort M) — DONE

- **R7 (A1) Consolidation pass** — DONE
  (docs/truth-ledger-paper-v3.md, 9,999 words (wc -w; v2 was 14,710);
  v2 left in place for the operator to retire to docs/archive/ — note
  in v3's status line. (a) ~24 dated in-place corrections collapsed
  into current-state text + new Appendix C revision history, one dated
  line each; (b) §2 rewritten dual-window — pilot table kept, dated,
  marked unreproducible; meta-repo longitudinal window regenerated from
  the committed snapshot docs/paper-data/stats-snapshot-2026-07-20.json
  (1,363 records, 63 claims, 614 verdicts, ~1.5% verification hit rate,
  ~0.02-day half-life medians), churn analysis promoted from §8 item 2,
  which now references §2.2; (c) §4 +2 rows (ADR-028 intake↔fold seam,
  hollow VERIFIED) + §3 scope sentence (full audit covers v0.4 only);
  (d) §10 hash-linking bullet replaced with the growth-gate hash-tree
  pointer, Haber–Stornetta → annotation updated, loophole-map ~l.171
  one-line correction note added; (e) refs verified — 5 never-cited
  [proposed] entries dropped (Doyle, de Kleer, Barr, RFC 6962, Mokhov),
  remainder renumbered 1–20, six kin refs verified against publisher
  records and cited from new §6.5 (novelty framing: each element known,
  the composition unprecedented); (f) §1 fold-semantics + INV-G/N now
  state the unified ADR-031 rule; reaffirm added to §1 Verification,
  new Appendix A row (as INV-S — INV-R was already taken by contradicts,
  a deliberate deviation from the R7 sketch), §6.2/§8 cost text updated,
  ADR-030's reaffirm_cleared residual named. Suites untouched-but-run:
  test-truth-core.py 201, test-truth-v04.py 13.)
  (a) collapse the 24 dated in-place corrections into current-state
  text + a Revision History appendix; (b) §2 dual-window: pilot
  snapshot AND longitudinal churn, regenerated from a committed
  `truth stats --json` snapshot; (c) add missing §4 rows (ADR-028
  seam, hollow-VERIFIED) + one §8 sentence scoping the v0.4 audit;
  (d) strike §10 hash-linking, replace with the TLR growth-gate
  pointer (see R8); (e) verify refs 20–25, drop unused [proposed].
  (f) R6 follow-up: §1 fold-semantics + INV-G/N rows must describe the
  ADR-031 unified duplicate rule (they still state the two-case
  ADR-008/016 detection).
  Target ≤10,000 words.
- **R8 Archive the TLR design as the growth-gate successor** — DONE
  (docs/growth-gate/ populated: tlr-target-architecture-and-adrs.md,
  test-tlr-fold.py (18/18 from the new location, 2026-07-20), README.md
  stating status (growth-gated future work; adopted piece ADR-031 from
  TLR-013) and trigger (first in-the-wild forged timestamp). The
  gate-vs-queue decision rule appended to
  docs/truth-ledger-operations-guide.md as a dated new section.)
  Copy `truth-ledger-target-architecture-and-adrs.md` and
  `test-tlr-fold.py` into `docs/growth-gate/`; §10 points at them:
  "when the first forged timestamp is found in the wild, build the
  fork-permanent hash tree (TLR-002/013/014); its executable spec is
  test-tlr-fold.py (18/18 with negative controls, 2026-07-20)."
  Also: adopt the gate-vs-queue decision rule text into the ops guide.

## Batch 5 — override decay + its instrument (effort S) — DONE
(From the 2026-07-20 candidate-adoption analysis of the clean-room six:
C4+C6 adopted; C1/C2/C3/C5 deferred as obligation-ledger §9 amendments;
rejected placements in docs/growth-gate/clean-room-convergence.md and
the analysis's register of rejections.)

- **R12 (C4, ADR-032) `--scope-ok` default expiry** — DONE
  (v0.9.14, ADR-032: pure `DEFAULT_OVERRIDE_TTL_DAYS=30` + `override_decay`;
  a scope_basis claim without --ttl-days is stamped ttl_days=30 +
  ttl_default:true in build_claim_payload, notice printed by cmd_claim /
  done --claim, never refused; expiry rides the UNCHANGED ADR-019 scan,
  ADR-030 arm 1 → re-file → re-fires ADR-007. Schema gains typed optional
  boolean ttl_default AND stdlib mirror gains it independently; $id bumped
  v0.9→v0.10, FS-2 corpus +3 fixtures + generated-mutant lockstep. Core
  TestOverrideDecay (4) + TestScopeDecayCLI (3); canary FAULT SD-decay
  (4 arms incl. negative control).)
  A scope_basis claim filed without --ttl is stamped ttl_days=30 +
  ttl_default:true (notice printed, never refused); expiry rides the
  unchanged ADR-019 scan path; ADR-030 arm 1 routes it to re-file,
  which re-fires ADR-007. Schema AND mirror gain optional ttl_default
  (FS-2 fixtures both ways).
  Accept: pure-function unit tests (3 arms + _ttl_expired parity),
  sandbox integration, canary FAULT SD (4 arms incl. negative control);
  suites 201/13/170 + additions; INV-T row, §1/§10/loophole-map/
  ops-guide touches. ADR carries its own adoption gate: widen or drop
  to opt-in if decay invalidations exceed genuine diverges across two
  rot-free reviews.
- **R13 (C6, ADR-033) override-velocity report** — DONE
  (v0.9.14, ADR-033: pure `override_report(events, now)` beside
  stats_report — overall counts (house convention, no per-window split):
  scope_basis filings, decay expiries (reason_code=ttl on ttl_default
  claims), overridden_duplicates, screened:false filings, max scope ttl,
  and verbatim-repeat detection reusing tokens() (token-set equal to an
  EARLIER now-dead {stale,diverged,retracted} claim — 'superseded' isn't a
  claim status here; a still-live prior is ADR-018 territory, not flagged).
  `truth stats` prints an overrides section + a NON-blocking advisory line;
  --json carries the structured section. NO threshold/gate. Core
  TestOverrideReport (5) + TestOverrideReportCLI (1); canary FAULT OV
  (2 arms incl. negative control).)

## Backlog

- **R13 threshold tripwire** — only after two R11 hand-audit windows
  establish the advisory's FP baseline.
- **Decay for screened:false claims** — only if a stale-in-fact
  unscreened claim is found unquestioned in the field (deliberately
  excluded from R12).
- **Content re-sync of the two satellite docs** (from R4, v0.9.13) —
  DONE (2026-07-20: both bodies re-synced to v0.9.13 against the CLI,
  CHANGELOG, ADRs 007–031, and paper v3; headers now state "content
  re-synced at v0.9.13" with the test-pinned `current: CLI v0.9.13`
  stamp intact. Loophole map: ADR-014/017/021/031 closures marked
  in-place, hollow-VERIFIED + ADR-030 reaffirm residuals added, verdict
  table and bottom line updated, 2026-07-20 growth-gate correction note
  kept. Ops guide: reaffirm trigger row + rung-3 operation (four arms,
  --dry-run, reaffirm_cleared, evidence-width rule), ADR-031 gate
  message, v0.9.11 banner + exit-code warning signatures, ADR-017 gate
  in §4, CHANGELOG.md location + lockstep pins noted, v0.6.2-diagram
  honesty note, gate-vs-queue section kept. test-truth-core.py 201 OK.)

## Operator-owned (no agent can do these)

- **R9 (A5) Re-home the meta-repo canary claim** — DONE
  (2026-07-21: old claim tr-3a31bfcf human-retracted, plus 6 superseded
  diverged claims, all via the ADR-011 ceremony. Re-homed as an ADR-014
  acceptance oracle: `wk-d13b8014` "weekly canary",
  `--accept-cmd "bash scripts/truth-canary.sh"`, screened true against
  `.truth/accept-allow`. Filed without --premise: nothing live to stand
  it on since the old claim was retracted, not superseded.)
- **R10 (A7) External referee run** of docs/independent-review.md by a
  genuinely external party; publish verbatim; cite in §8.1. — OPERATOR
- **R11 Efficacy trial**: land Batches 1–2 first (honest churn
  denominator), then start the control-arm clock; first monthly
  hand-audit due ~2026-08-08 (§8 item 2). — OPERATOR

## Sequencing

Batch 1 → Batch 2 → R11 clock starts → Batches 3–4 during accrual →
submission with trial numbers. R9/R10 anytime; R10 before submission.

## Log

- 2026-07-20: roadmap created; §6.4 standards-motivation section added
  to the paper (prior session work). Batch 1 dispatched to an
  implementation agent.
- 2026-07-20: Batch 1 (R1+R2) implemented as v0.9.11; all suites green:
  test-truth-core.py 170 (was 160, +10), test-truth-v04.py 13,
  truth-canary.sh 166 caught / 0 missed. Left uncommitted for operator
  review.
- 2026-07-20: Batch 2 (R3) implemented as v0.9.12 + ADR-030; all suites
  green: test-truth-core.py 190 (was 170, +20), test-truth-v04.py 13,
  truth-canary.sh 169 caught / 0 missed (FAULT RA +3). Paper's §4
  invariant table untouched (Batch 4 owns it): an INV row for "a
  reaffirm mismatch is never auto-filed" is pending R7. Left
  uncommitted for operator review.
- 2026-07-20: R3 red-team fixes applied (F1/F2/F3-test mandatory +
  F3-hardening/F4), still v0.9.12 uncommitted; all suites green:
  test-truth-core.py 195 (was 190, +5), test-truth-v04.py 13,
  truth-canary.sh 169 caught / 0 missed.
- 2026-07-20: Batch 3 (R4+R5+R6) implemented as v0.9.13 + ADR-031; all
  suites green: test-truth-core.py 201 (was 195: +3 version pins, +3
  order-check), test-truth-v04.py 13, truth-canary.sh 170 caught / 0
  missed (FAULT K2 +1; B1/B3–B5 now assert the unified ADR-031
  message). Follow-ups recorded: satellite-doc content re-sync
  (Backlog) and the R7(f) paper touch for the unified duplicate rule.
  Left uncommitted for operator review.
- 2026-07-20: Batch 4 (R7+R8) implemented — editing batch, no code
  changes. Paper v3 written at 9,999 words (v2: 14,710; wc -w), stats
  snapshot committed beside it; growth-gate archive populated, TLR
  oracle 18/18 from docs/growth-gate/; ops-guide gate-vs-queue section
  and loophole-map correction note added. Suites re-run unchanged:
  test-truth-core.py 201, test-truth-v04.py 13. Reaffirm invariant row
  landed as INV-S (INV-R already names contradicts). Left uncommitted
  for operator review.
- 2026-07-20: Backlog satellite-doc content re-sync done — loophole-map
  body v0.6.4→v0.9.13 (ADR-014/017/021/031 closures marked; hollow
  VERIFIED, ADR-030 reaffirm residuals, ADR-024/028 additions; paper
  links → v3), ops-guide body v0.9.0→v0.9.13 (reaffirm row + rung-3
  operation, ADR-031 refusal, v0.9.11 banner/warning, ADR-017,
  CHANGELOG location, version-pin note); headers re-stamped "content
  re-synced at v0.9.13", pin format unchanged. Editing-only change;
  test-truth-core.py 201 OK (version-pin tests green). Left uncommitted
  for operator review.
- 2026-07-20: candidate-adoption analysis of the clean-room six (prompt
  archived in session scratchpad): C4+C6 adopted as Batch 5 (R12/R13,
  ADR-032/033 pending); C1/C2/C3/C5 deferred — written as
  obligation-ledger-design.md §9 amendments; register of rejections
  with reopeners in the analysis output. Zero outright rejects is
  pre-screening, not miscalibration: the convergence doc had already
  quarantined the re-losing mechanisms.
- 2026-07-20: Batch 5 (R12+R13) implemented as v0.9.14 + ADR-032/033; all
  suites green: test-truth-core.py 214 (was 201: +4 override_decay,
  +5 override_report, +3 scope-decay CLI, +1 report CLI; FS-2 corpus +3
  fixtures ride the generated-mutant lockstep), test-truth-v04.py 13,
  truth-canary.sh 176 caught / 0 missed (FAULT SD-decay +4, FAULT OV +2).
  Schema $id bumped v0.9→v0.10 for the ttl_default field (EXPECTED_SCHEMA_ID
  + PINNED_SHAPE_SHA256 updated). Docs owned by this batch done:
  template/.truth/README.md (default-expiry daily-op + intake notes, title
  v0.9.14), template/CHANGELOG.md v0.9.14; the lockstep `current: CLI`
  stamps bumped to v0.9.14 in check-truth.sh + both satellite docs (stamp
  only; content re-sync pending). PENDING docs touches (NOT edited, for a
  later editing batch): paper v3 §1/§10/§8 + Appendix A INV-T (R12) / INV-U
  (R13) rows; loophole-map §B row; ops-guide intake + stats paragraphs
  (the satellite-doc bodies note "ADR-032/033 override-decay content sync
  pending" in their headers). Left uncommitted for operator review.
- 2026-07-20: Batch 5 red-team fixes applied (F1 FS-1 exclusion, F2
  plain-text lock, F3 ADR-033 residual naming), still v0.9.14
  uncommitted; all suites green: test-truth-core.py 218 (was 214: +3
  F1 half-life TTL exclusion, +1 F2 plain-text lock), test-truth-v04.py
  13, truth-canary.sh 176 caught / 0 missed. Left uncommitted for
  operator review.
- 2026-07-21: human retraction round committed (R9 first half + 6
  superseded claims); ledger fully groomed (0 stale, 0 diverged, empty
  queue). v0.9.14 tagged and pushed; kuchnie pilot copier-updated
  v0.9.9 -> v0.9.14 zero-conflict, all suites green there (core 218
  w/ 2 consumer skips, v04 13, canary 176/0, validate 1139 OK, doctor
  clean), committed on branch chore/copier-update-v0.9.14 and pushed —
  PR + merge is the operator's. _skip_if_exists protected the pilot's
  own CHANGELOG.md (first real-world test of R5's guard). Still open:
  R9 second half (oracle re-file), R10, R11 (first audit ~2026-08-08),
  paper v2 retirement to docs/archive/, Batch 5 paper doc touches
  (INV-T/INV-U rows etc., see 2026-07-20 entries).
- 2026-07-21 (cont'd): AGENTS.md and README.md still named v2 the
  normative/living spec after Batch 4 shipped v3 as its consolidation
  successor — fixed, both now cite truth-ledger-paper-v3.md; post-commit
  scan staled tr-6308173b and tr-f0ac802b as the pre-edit whisper
  predicted. R9 second half done: filed `wk-d13b8014` "weekly canary" as
  an ADR-014 acceptance oracle, `--accept-cmd "bash scripts/truth-canary.sh"`,
  screened true (R9 entry above updated HALF-DONE -> DONE). Paper-v2 ->
  docs/archive/ move itself still sits uncommitted in the working tree —
  operator-approved but blocked pending the deliberate freeze lift
  (.githooks/pre-commit). Still open: R10, R11 (first audit
  ~2026-08-08), Batch 5 paper doc touches, and the un-fixed stale-v2
  citations noted in review (docs/field-notes-sdk-session.md,
  docs/independent-review.md's R10 review target) — left for operator
  judgment since one's a historical field note and the other decides
  what R10 actually reviews.
- 2026-07-21 (cont'd): Batch 5 PENDING docs touches landed. Paper v3:
  §1 gains an "Override decay" paragraph (ADR-032); §8 gains item 8
  (ADR-033's verbatim-repeat advisory is evadable by one text edit —
  raw counters are the real backstop); §10's scoping-fault bullet notes
  what shipped vs. what's still unmeasured; Appendix A gains INV-T
  (ADR-032) and INV-U (ADR-033), title bumped to v0.9.14. Loophole-map
  §B gains a "closed since v0.9.14 — scope-ok rot" paragraph and a
  ranked-table cell; header's content-sync-pending note cleared. Ops
  guide: new "scope-ok default-expiry notice" paragraph (§2, exact
  stderr string) + stats trigger-map row extended for the `overrides`
  section; header note cleared. `bash scripts/fact-health.sh` run clean
  on all three (zero new tr- citations added — cited by ADR number, the
  ADRs' own home). Pre-existing, out of scope: fact-health flags
  tr-3a31bfcf (README, field-notes-batch-m, this file) as retracted-but-
  cited, from last session's R9 retraction not yet scrubbed from prose;
  and tr-6308173b/tr-f0ac802b in this file's own Log narration of
  today's staling, same past-tense-citation shape the Log already uses
  for tr-3a31bfcf's retraction. Neither touched. Also found and
  restored: the paper-v2→docs/archive/ move (left uncommitted for the
  operator, see above) was sitting half-done in the working tree — file
  physically gone from its old path with nothing staged — which crashed
  fact-health.sh's first run (`open()` reads disk, not git's index).
  Moved it back to match HEAD exactly; `git mv` is a clean one-step
  redo whenever the freeze is deliberately lifted.
- 2026-07-21 (cont'd): tr-3a31bfcf scrub, partial by design. README.md's
  two citations fixed — the canary table row now points at
  `wk-d13b8014` (the ADR-014 oracle it was re-homed as, §"Operator-owned"
  R9 above) instead of the dead claim; the claim-id-pattern example
  repointed to tr-dca73f8a (live, cited below it in the same doc).
  Deliberately NOT touched: docs/field-notes-batch-m-verification-session.md
  and this file's own Log narrate the id at points when it *was* live/P0
  — rewriting those would falsify history, not fix a bug, same shape as
  this Log's own tr-6308173b/tr-f0ac802b narration two entries up.
  fact-health: 5 failures remain, all historical-narration citations, 0
  live-prose-on-dead-fact.
- 2026-07-22: symbol-level tracing designed, falsified/amended (this
  repo), validated at scale (kuchnie: 2,397 symbols, 2% lit; catalog
  BOM path found wholly unwatched). Archived as
  docs/growth-gate/symbol-tracing-design.md with tested recipes.
  Backlog: kuchnie first wave steps 2-3 (core manifest + ERP pricing)
  on operator demand; D2 --symbols verb demand-gated.
- 2026-07-23: spec-archetype satellite promoted from kuchnie into the
  template as part of unreleased v0.9.15 — six archetype blanks + field
  guide land at template/docs/templates/, the bootstrap interview
  extracted to template/prompts/spec-bootstrap.md (the guide now points
  at it, no second copy). Kuchnie-local references genericized
  (docs/spec-convention.md → .truth/README.md § Feature specs; the
  kitchen-erp screens.md worked-example pointer generalized; Beads A/B
  lore → beads-integration-guide pointer) with a precedence line: a
  repo's own spec-convention doc outranks the summary. Ownership rule
  stated in the guide: template-owned, updates via `copier update`,
  per-project extensions in a separate docs/templates/local-archetypes.md
  — the evidence-deny pattern. Gate authority pinned: the guide's
  pseudo-code stays pseudo-code, scripts/spec-health.sh is authoritative.
  AGENTS.md snippet gains the classify-then-blank step; template
  CHANGELOG v0.9.15 entry extended. Docs-only — zero scripts/, .truth/
  contract, or copier.yml changes (the existing chmod task already
  covers spec-health.sh). Kuchnie takes it back via copier update.
- 2026-07-23 (later): satellite committed after red-team (authority
  wording fixed: five-name section contract attributed to the template
  set, spec-health "four checks" claim corrected to one, status line
  points extensions at local-archetypes.md). En route found and fixed a
  real CLI bug: invalidate-scan was rename-blind (git diff --name-only
  under rename detection emits only the destination path, so the
  paper-v2 retirement in e01dd50 left five claims falsely live) --
  changed_files_since now passes --no-renames, regression test with
  config-pinned negative control (c0bb4b6). v0.9.15 TAGGED and pushed
  (concern tags + satellite + scan fix). Ledger groomed: rename victims
  judged genuine, successors filed and cross-verified (paper-v3 coverage
  tripwire tr-8d246eb3 replaces the dead v2 pair; one successor caught
  unfaithful by its verifier and corrected -- tr-a6ce8d2c). Kuchnie
  synced v0.9.14->v0.9.15 (PR #12 merged): its new-doc gate demanded
  Reader/Enables/Update-trigger headers within 15 lines -- fixed
  upstream (8137ce8, rides v0.9.16) and forward-ported verbatim; both
  repos' satellites covered by live claims (tr-4d9fff1b meta,
  tr-b949e4e0 pilot). NOTE: kuchnie tr-54214e5f carries an ADR-032
  30-day scope-ok decay (~2026-08-22) -- re-word to existential before
  then or let it re-file. Queue: paper-v2 family diverged tombstones
  await operator retraction. (Retracted by operator 2026-07-23,
  52bbb36 -- queue empty.)
- 2026-07-26: spec-coverage manifests -- requirements-based traceability
  (spec assertion <-> test citation) designed and adversarially
  falsified (two rounds: designer self-falsified the empty-manifest
  hole; falsifier killed the unscoped extraction regex, hit ADR-018
  jaccard on serial adoption, measured corpus-level gaming). Verdict
  BUILD-WITH-AMENDMENTS: slug-scoped recipes SC-<slug>-NNN, per-spec
  pre-sorted manifest <spec>.sc.txt, slug registry, 2 sentinel claims
  per spec, grades r0-r3 (r1 = citation is a report, r0/ADR-014 alone
  proves execution; r3 unminted prose undetectable -- honest limit).
  PILOT SHIPPED on kuchnie catalog/docs/specs/configurator-api.md
  (505e02c content, 2738e0b ledger): 6 markers, manifest, 8 docstring
  citations, sentinels tr-fcca2d96 (spec-manifest, sort without -u
  closes duplicate-id blindness) + tr-40a5beb5 (tests-manifest,
  catalog/tests/** glob live at scan time), verified agree by
  verifier-r-0726, 21 tests green, governance clean. OPEN: design doc
  not yet archived in growth-gate (option 1 pending operator say-so);
  docs integration map drafted (explained.md sec 10 subsection +
  glossary, ops-guide trigger row + coverage-policy LIVING CONTRACT
  entry, loophole-map event F citation-without-verification, tutorial
  3.6 paragraph, asbuilt+concept-map nodes) -- not yet applied.
- 2026-07-27: option C built -- the V&V section lands in all six
  archetype blanks per the red-teamed design
  (docs/growth-gate/vv-archetype-pairings.md): verification pre-paired
  per the Part 1 table with the oracle CITED by id, never restated
  (F8); validation as an UNVERIFIED + --ttl-days attestation with the
  ADR-019 expiry loop spelled out in the blank (F9); residuals by
  TITLE only (F6); E confined to the ADR-014 accept-cmd lane (F4), F
  stated as session-close/session-gates.d enforcement, not a ledger
  oracle (F12). Field guide gains "Appendix -- oracle recipes that
  survive the screen" (canonical layer-rule sentinel with the
  mandatory tr -d ' ' (F1/F2), ADR-007/032 discipline (F3),
  path-tripwired schema sentinels vs hash-pin divergence generators
  (F5), attestation pattern with disclosed costs, consumer-safe
  pointer at the spec-coverage traceability sibling).
  prompts/truth-verifier.md gains the attestation paragraph (recheck
  files cannot_verify -- judge manually). Shipped as v0.9.16,
  docs-only (also carries the 8137ce8 three-question-header fix);
  ADR-026 lockstep bumped across truth docstring, .truth/README
  title, check-truth.sh, ops-guide + loophole-map headers,
  explained.md scope + glossary, asbuilt NOTE;
  TestCrossSurfaceVersions green. Kuchnie takes it via copier update
  AND must extend its own spec-convention section contract with the
  V&V section (F7) -- until that doc changes, the section is a dead
  letter there by its own precedence rule.
- 2026-07-27 (later): phase 2 executed in kuchnie -- the V&V section
  stops being decorative: first real ADR-014 acceptance oracle wired.
  wk-e7a2992d ("Wire the configurator pytest suite as the ADR-014
  verification oracle for the configurator-api spec", --accept-cmd
  .venv/bin/python -m pytest catalog/tests/test_configurator.py -q,
  kind verification) filed, started, and closed with the oracle
  executed green at close (21 passed, executed=true rc=0 on the close
  event -- the r0 execution proof). configurator-api.md gained its
  Verification & Validation section citing the wk- id as oracle
  carrier (commit f611ade); completion claim tr-f2c1c720 (citation
  sentinel, evidence scoped to what the grep shows -- red-team moved
  the execution narrative to the close event's basis) verified agree
  by an independent session. Spec-edit restales of both spec-coverage
  sentinels reaffirmed by hash-match, exactly as predicted. The
  validation half is deliberately open: the spec's Validation line is
  an attestation-pending placeholder citing NO id -- filing the TTL'd
  attestation (UNVERIFIED, --ttl-days 90) requires the operator to
  actually walk the BOM output against a real production sheet; the
  command is handed to the operator, an agent cannot attest a human
  event that has not happened. Next: phase 3 (symbol-tracing second
  wave) per the approved order.
- 2026-07-27 (phase 3): symbol-tracing second wave live in kuchnie per
  the adoption sketch. Two D3 contract-symbol manifests committed
  (kuchnie-core/docs/contract-symbols-core.txt, 16
  geometry/decomposition symbols; kitchen-erp/docs/
  contract-symbols-pricing.txt, 10 pricing symbols) with sentinel
  claims tr-12b7419f/tr-e602c0b0, plus 9 D1 definition pins
  (decompose_drawer_box, lw, runner_clearance_per_side_mm multi-region
  x4 per A3, front_reveal, door_width, drawer_front_width,
  import_price_file, _last_known_price, generate_cost_trace_lines) --
  11 claims, 11 independent verifier sessions, 11 agree. Two earned
  amendments: **A4** (method-pin recipe needs the 4-space-closing
  `    \).*` alternative -- the verbatim recipe silently lost a method
  body whose multi-line signature closes at 4-space indent; folded
  into this design doc) and a red-team ADR-018 catch (pin texts
  sharing the boilerplate tail collided at jaccard 0.617 between the
  door_width/drawer_front_width pair -- diversified, refiled clean;
  rule: pin families need per-claim tail variation, not just distinct
  symbol names). Tier deliberately P2 (vs first-wave P1): at the
  measured burst rate P1 pins would flood the human queue; genuine
  mismatches dispatch regardless of tier. Next: phase 4 (spec-coverage
  second spec).
- 2026-07-27 (phase 4): spec-coverage second spec (wtuu) live in
  kuchnie -- and it demanded real carpentry, not just wiring. Both
  named candidates lacked tests; the operator chose implementing
  worktop-uu-seeding with a furniture-technology expert agent. Domain
  resolution: the spec's "40 decors / 80 variants" described the
  manufacturer's offer, not the DB -- seeded 18 decors x 2 widths = 36
  U-U variants (38mm, 4100x900/4100x1200), 0190 excluded (legacy, no
  documented 2U offer); the DB's PF-U-600 variants carried NO edges,
  so 18 HPL edge rolls (code = decor code, per the manufacturer table)
  were materialised first. Red-team (also expert) found two substantive
  domain gaps filed as wk-4fc28a19 (ten decors inherit wrong structure
  code RS from upstream YAML) and wk-bca0a74b (U-U absent from
  worktop_specs: worktops endpoint hides what the configurator
  offers). Bonus finds: catalog-service.md's "extras in any order" was
  FALSE (curated kitchens must precede decor style tags or style
  associations silently seed 0) and production carries 6 hand-era
  decor_style_tags rows the tagger cannot regenerate -- rebuild path
  re-verified on scratch (five extras, 2/148/222/145/123/87) and
  re-pinned as tr-0dda200b, predecessor referenced by title only to
  survive its future retraction. Wiring: SC-wtuu-001..007 + manifest +
  docstring citations + sentinels tr-22772c10/tr-a2acd399 + ADR-014
  oracle wk-25d33212 (suite executed green at close). 3/3 verifier
  agree; the rebuild verifier independently reproduced the whole
  scratch rebuild. Next: phase 5 (incident-to-gap ritual), operator
  attestation still open.
