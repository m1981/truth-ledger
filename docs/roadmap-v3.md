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

## Backlog

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

- **R9 (A5) Re-home the meta-repo canary claim** as an ADR-014
  acceptance oracle (ledger operation in the meta-repo). — OPERATOR
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
