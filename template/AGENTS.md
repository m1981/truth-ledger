# Agents

This project keeps a truth ledger. Before relying on a repository fact,
check it: `scripts/truth list --live`. When you verify a fact, file it:
`scripts/truth claim "<fact>" --class VERIFIED --evidence-cmd "<cmd>" --paths "<glob,glob>" --tier P1`
Facts about the world outside the repo: add `--ttl-days N` instead of --paths.
Never edit .truth/claims.jsonl directly; status changes are new records.

See `.truth/README.md` for full documentation.
End every session with `bash scripts/session-close.sh` — it refuses (exit 1) while knowledge is still in flight (dirty tree, claimed work items, failing gates); project-specific gates plug in as executable `scripts/session-gates.d/*.sh`.
Using Beads as the work tracker? See `docs/beads-integration-guide.md` for the claim->verify->work->close loop and adapter wiring.
