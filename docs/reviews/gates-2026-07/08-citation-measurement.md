# Citation measurement — retracted ids cited outside archive (2026-07-31)

> Data artifact backing ledger claim `tr-f0c94c6c` (INFERRED, TTL 30d).
> Method: for each of the meta-repo's 49 retracted claim ids at anchor
> 1d10a21, `git grep -l -F <id>` over tracked `*.md` excluding
> `docs/archive/` and `.truth/`. Recomputed mechanically by the
> verifier session `verifier-adr-review-2026-07-31`.

12 of 49 retracted ids are cited in tracked markdown outside archive:

| Retracted id | Citing files |
|---|---|
| tr-11beb903 | docs/truth-ledger-operations-guide.md |
| tr-3a31bfcf | docs/field-notes-batch-m-verification-session.md, docs/roadmap-v3.md, trial-prompts/RUNBOOK.md |
| tr-58077018 | docs/truth-ledger-operations-guide.md |
| tr-7b5a5e72 | docs/truth-ledger-operations-guide.md |
| tr-bbdff732 | docs/field-notes-batch-m-verification-session.md |
| tr-d570e6c2 | docs/truth-ledger-operations-guide.md |
| tr-d61e96fd | docs/roadmap-v3.md |
| tr-da868d5c | docs/field-notes-batch-m-verification-session.md |
| tr-ebac6513 | docs/growth-gate/symbol-tracing-design.md, docs/truth-ledger-loophole-map.md, docs/truth-ledger-operations-guide.md |
| tr-f0ac802b | docs/roadmap-v3.md |
| tr-f8d1d042 | template/CHANGELOG.md |
| tr-fe1169f4 | template/docs/adr/truth/023-inv-m-static-dead-tripwire-scope.md, template/docs/adr/truth/024-inv-m-statically-dead-globs.md |

Reading notes, not defects per se: most rows are historical record
(field notes, CHANGELOG, ADR amendment blocks, roadmap logs) — the
class the rev-3 tombstone gate's consumer-declared scope exists to
exempt. The actionable row is `tr-11beb903`: the operations guide's
living-contract table cites it as the *current* watcher of
`docs/truth-ledger-explained.md`, but the watcher chain has rolled to
`tr-56682235` (live, agreed) — a stale citation in a living contract,
exactly the ADR-036/rev-3 defect class, to be fixed at the next
operations-guide edit.
