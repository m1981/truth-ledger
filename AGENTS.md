# Agents

This repository (the truth-ledger template itself) runs its own ledger.
Before relying on a repository fact, check it: `scripts/truth list --live`.
When you verify a fact, file it:
`scripts/truth claim "<fact>" --class VERIFIED --evidence-cmd "<cmd>" --paths "<glob,glob>" --tier P1`
Facts about the world outside the repo: add `--ttl-days N` instead of --paths.
Work items live in the same ledger (ADR-002): pick work with
`scripts/truth ready` (only premise-valid items show), close with
`scripts/truth done <wk-id> --claim "<fact>"` (claim-at-death). Verbs and
the tracker seam are documented in template/.truth/README.md — cite, don't restate.
Never edit .truth/claims.jsonl directly; status changes are new records.

Meta-repo conventions, on top of the standard layer:
- One home per fact: load-bearing facts in README/docs are cited as
  ledger ids, never restated as counts or contracts. Sweep with
  `bash scripts/fact-health.sh` after editing docs.
- The normative mechanism spec is docs/truth-ledger-paper-v3.md §1; the
  CLI contract summary is template/.truth/README.md. Do not restate
  either elsewhere — link or cite.
- Accepted ADRs are immutable in body; corrections land as
  `Amended by:` lines in the status block (see ADR-002, ADR-004).
- `docs/archive/` is frozen verbatim; never update it.
- The P0 canary claim's evidence command (`bash …truth-canary.sh`) is
  deliberately NOT allowlisted (ADR-009's test-runner rule), so
  `verdict --recheck` refuses to execute it: verifiers run the suite
  manually and judge the ALL-CAUGHT sentinel by hand. Accepted
  ceremony, decided 2026-07-13 — do not "fix" it by allowlisting
  `bash`, which would gut the evidence screen.
- `scripts/truth` is a SYMLINK to `template/scripts/truth`: watch the
  real path in evidence_paths (a watch on the symlink can never fire —
  git only sees the link itself, which never changes).
- A pre-edit whisper hook is wired (`.claude/settings.json` → PreToolUse
  → `scripts/truth-whisper.py`, ADR-005 trial): editing a path the
  ledger watches injects the mechanical prediction of what your commit
  will stale; `docs/archive/` and `.truth/claims.jsonl` are deny-listed
  (edit tools blocked — the ledger changes only through the CLI). The
  whisper count per session lives in `.git/truth-whisper.seen`; that is
  the ADR-005 adoption-gate metric. The same two stages are enforced
  for the pi harness via `.pi/extensions/truth-whisper.ts` (same deny
  list, same metric file), and `docs/archive/` is additionally guarded
  harness-independently at pre-commit (`.githooks/pre-commit`). The
  consumer hook has its own regression gate (it is untemplated, so it
  has no home in the template canary): `bash scripts/test-whisper-hook.sh`
  — deny voice, main-tree and worktree whisper, injection-verified.

See `template/.truth/README.md` for the layer's full documentation.
