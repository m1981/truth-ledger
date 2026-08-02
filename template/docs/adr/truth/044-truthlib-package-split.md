# ADR-044: The single-file CLI becomes the truthlib package behind a thin entry

Status: Accepted (2026-08-02, operator) — decision D1 of the migration
plan, the P3 "package split". Implemented in CLI v0.9.28: pure file
moves and imports, zero logic edits — every refusal message, exit code,
advisory line and derived status byte-identical, proven by the entire
existing test corpus (243-arm canary, 286-test core suite, v04 suite)
running unchanged against the new entry.
Date: 2026-08-02
Supersedes: — (reopens one entry of the as-built "deliberately NOT
changed" list; no fold, gate, or schema semantics change)

## Context

"Single-file CLI" sits on the settled list, adversarially confirmed
twice — at ~1–2k lines, where one file was the cheapest honest shape.
The repo's own rule is that settled decisions reopen only on new
evidence, and the evidence arrived measured: at 4.4k lines the
FUNCTIONAL CORE / IMPERATIVE SHELL boundary was a banner comment, and
the four-lens review caught real drift across it — the R1 incident
(`disputed` joined STATUSES; the gated copies stayed correct, both
satellites' hand copies did not) and R7 (`done --claim` silently lost
`--json` and never gained `--concern`, a hand-copied flag surface).
Every drift crossed a boundary no machine enforced. P2 (ADR-043)
extracted the contracts inside the one file precisely so this split
could be pure mechanics.

## Decision

**Carve `template/truthlib/` along the concern map; keep
`scripts/truth` as the one loading surface.**

Module → concern (the P2-shaped seams, moved, not rewritten):

| module | concern |
|---|---|
| `registry.py` | vocabulary + lexicons: statuses, verdict maps, kinds, tiers, ADR-007/035 token sets, id/ts/concern shapes, policy-file paths, numeric knobs |
| `kernel.py` | canon/fold_key (ADR-016), fold/fold_issues/fold_supersedes, order_check (ADR-031), validate mirror, path matcher, pure git-output parsers |
| `evidence.py` | the ADR-009/014 screen (one implementation), recipe lints, determinism, recheck, reaffirm triage (R3/ADR-030) |
| `policy.py` | intake predicates: ADR-001 matrix, supersede/contradicts ladders, G8/ADR-007/INV-M/ADR-032, invalidation strategies |
| `gates.py` | the ADR-034 INTAKE_GATES table + gate fns + run_intake_stage |
| `advisory.py` | CC-1 assembly, intake advisories, banner, and the pure report family (queue/impact/inverse/baseline/stats/overrides/separation/blast/vocab/dispatch) |
| `shellio.py` | ALL I/O — the only subprocess importer: git probes, files, clock, env, append_records, loaders, human-ack |
| `cli.py` | argparse + cmd_* orchestration; refusal exits |

Import DAG, enforced not conventional: registry ← kernel ←
evidence/policy ← advisory; shellio → kernel/registry only; gates →
policy/evidence/kernel/registry **+ shellio** (documented exception —
some gate fns gather their own facts exactly as they did inline);
cli → everything. Two placements follow the DAG over the drafted
concern map: `parse_name_log` and `blast_forecast` live in kernel (pure
parsers shellio.blast_history consumes), and `citation_sweep` lives in
cli (it orchestrates loaders, notices, and exits).

**The thin entry keeps every property that made single-file right.**
`scripts/truth` resolves its own real path (so the meta-repo's root
symlink and every copied tree resolve identically), puts truthlib/'s
parent on `sys.path`, re-exports every module's namespace (underscore
names explicitly), and mirrors attribute assignments into the owning
modules so the suites' monkeypatch seam (`tm.ledger_path = ...`) keeps
working. Retained: no install step, no dependencies, copier-copyable
(`_subdirectory: template` ships truthlib/ automatically),
`SourceFileLoader("truth", "scripts/truth")` compatibility for every
existing consumer. If true single-file distribution is ever needed,
`python3 -m zipapp` over the same modules is the escape hatch — the
decision reopened here is packaging, not surface.

**Purity is a theorem.** TestModulePurity parses each pure module with
`ast` and refuses subprocess imports, `os.environ` reads, `open()`
calls (allowlist deliberately empty), `datetime.now`/`time.time`, and
any truthlib import outside the DAG row. Red-proven at adoption:
`import subprocess` seeded into policy.py reddened the arm.

## Consequences

* The next boundary drift is a red test, not a review finding: the
  PURE-CORE banner, the one-subprocess-importer rule, and the DAG are
  machine-checked every run.
* Layout consumers copy a directory now: canary mkrepo + the BF
  shallow/unborn sandboxes, test-fact-health, test-session-digest, and
  the release battery's canary trigger were updated in the same change.
* The acceptance oracle for the split is deliberately the OLD corpus
  unchanged — a 243/243 canary with the same arm count is the whole
  equivalence proof; any arm-count delta would have meant the phase
  exceeded its license.
