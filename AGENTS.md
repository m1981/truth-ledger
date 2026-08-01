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
- The machinery's own control surfaces carry sentinel claims (2026-08-01):
  `.truth/evidence-allow`, `evidence-deny`, `accept-allow`, `citation-scope`,
  `generated-paths`, plus `scripts/truth-whisper.deny`, `scripts/fact-health.sh`,
  `.claude/settings.json` and `.githooks/pre-commit` are each pinned by a
  `sha256sum` claim. Editing one stales its claim, and because the DIGEST
  changed, `reaffirm` cannot auto-clear it — a human verdict is forced. That
  is the point: these files decide what the screen admits and what the hooks
  refuse, and until this pin the ledger watched every doc in the repo and
  none of them.
- A fact about a DEPLOYMENT (the pilot, the SDK repo) takes `--ttl-days`, not
  `--paths` — no git event here can observe another repository. Treat that TTL
  as a timer, not a detector: a claim pinning the pilot's template version sat
  wrong for weeks (twenty releases of drift) inside its 60-day window, because
  nothing could notice and nobody re-read it. Re-verify deployment facts at
  release time; do not let the clock stand in for a check.
- Machine-local operational notes live in `.local/` (gitignored, never
  commit its contents): the deployment-site disk mapping (machine
  paths stay out of git; the paper's own text anonymizes the pilot,
  though other committed docs name the sites) and this machine's
  workarounds. Agent-agnostic by design — read them there, update them
  there, and do NOT mirror them into any harness-private memory; a
  fresh clone won't have `.local/`, which is intended.
- Doc edits get an independent reader BEFORE the commit lands: any
  change touching `docs/` or `template/.truth/README.md` is peer-reviewed
  by a fresh session/agent that did not author it (check mechanical
  sentences against the code, version mentions on UNPINNED surfaces,
  cross-surface consistency, which live claims the text breaks). The
  lockstep tests refuse only the pinned stamps; everything else is
  caught by reading or not at all — the v0.9.15 release proved both
  halves (a missed unpinned Scope header, found only by an independent
  reviewer). This is the review the design assumes; do it unprompted.
- `bash …truth-canary.sh` is deliberately NOT on the evidence allowlist
  (ADR-009's test-runner rule), so `verdict --recheck` will refuse to
  execute any claim carrying it: run the suite yourself and judge the
  ALL-CAUGHT sentinel by hand. Accepted ceremony, decided 2026-07-13 —
  do not "fix" it by allowlisting `bash`, which would gut the screen.
  (This paragraph used to describe "the P0 canary claim" in the present
  tense; that claim was retracted 2026-07-20 and re-homed as an ADR-014
  acceptance oracle. It cited no id, so fact-health — the tripwire built
  for exactly this — could not see it go stale. A restated fact, in the
  file that mandates cite-don't-restate.)
- `scripts/truth` is a SYMLINK to `template/scripts/truth`: watch the
  real path in evidence_paths (a watch on the symlink can never fire —
  git only sees the link itself, which never changes).
- Export a stable `TRUTH_SESSION` before filing anything. The default is
  ppid-derived and differs per one-shot shell call (Claude Code Bash,
  `pi -p`), so records from one working session scatter across ids and
  ADR-010's author≠verifier refusal cannot be trusted from the default —
  separation by PID accident is not separation. A verifier exports its
  own `TRUTH_SESSION=verifier-<slug>`; never scribe verdicts through the
  author's session.
- Downgrading an independent finding's severity is itself a claim — the
  one that stops further work, so the highest-leverage one to be wrong
  about. Before building on a downgrade, dispatch a fresh adversary to
  REFUTE the disposition; after building, a second one to attack the
  artifact. Three shipped releases (ADR-021, ADR-024, ADR-028) exist
  because exactly this drill flipped a "just document it" back into a
  code fix.
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
  — deny voice, main-tree and worktree whisper, injection-verified. The
  pre-push RELEASE BATTERY (`scripts/release-battery.sh`) has the same
  shape and the same reason: `bash scripts/test-release-battery.sh`, six
  arms, each one verified red against a mutated copy of the battery
  before being committed. Do not add an arm you have not seen fail.

See `template/.truth/README.md` for the layer's full documentation.
