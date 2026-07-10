# Agents

This repository (the truth-ledger template itself) runs its own ledger.
Before relying on a repository fact, check it: `scripts/truth list --live`.
When you verify a fact, file it:
`scripts/truth claim "<fact>" --class VERIFIED --evidence-cmd "<cmd>" --paths "<glob,glob>" --tier P1`
Facts about the world outside the repo: add `--ttl-days N` instead of --paths.
Never edit .truth/claims.jsonl directly; status changes are new records.

Meta-repo conventions, on top of the standard layer:
- One home per fact: load-bearing facts in README/docs are cited as
  ledger ids, never restated as counts or contracts. Sweep with
  `bash scripts/fact-health.sh` after editing docs.
- The normative mechanism spec is docs/truth-ledger-paper-v2.md §1; the
  CLI contract summary is template/.truth/README.md. Do not restate
  either elsewhere — link or cite.
- Accepted ADRs are immutable in body; corrections land as
  `Amended by:` lines in the status block (see ADR-002, ADR-004).
- `docs/archive/` is frozen verbatim; never update it.
- A pre-edit whisper hook is wired (`.claude/settings.json` → PreToolUse
  → `scripts/truth-whisper.py`, ADR-005 trial): editing a path the
  ledger watches injects the mechanical prediction of what your commit
  will stale; `docs/archive/` and `.truth/claims.jsonl` are deny-listed
  (edit tools blocked — the ledger changes only through the CLI). The
  whisper count per session lives in `.git/truth-whisper.seen`; that is
  the ADR-005 adoption-gate metric.

See `template/.truth/README.md` for the layer's full documentation.
