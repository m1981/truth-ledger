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
  **That sweep has a measured blind spot, so a retracted NUMBER can
  outlive its retraction indefinitely.** `fact-health.sh` reads only
  `.md` files (its `FILES=` list) and matches only ledger IDs — a figure
  restated inside a `.py` string is invisible twice over. Measured
  2026-08-18: J-040 recounted the whisper metric (`2329`/`6.8` →
  `1670`/`22.6`) and the correction reached the journal, the runbook and
  the dossier, while four LIVE surfaces kept quoting the retracted pair
  for a day — `registry.py:69`, `test-truth-core.py:5373`,
  `.truth/watch-policies:30`, and worst, `gates.py:140`, which is the
  REFUSAL text printed to an author: the gate argued from a number the
  project had already withdrawn. When a journal entry retracts a figure,
  grep the retracted literal across code and policy files too, not just
  docs: `grep -rn '<old-figure>' template/ .truth/ scripts/`.
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
- Delegating an EDIT to a subagent is a destructive operation; delegating
  a SEARCH is not, and the split is worth holding. Measured 2026-08-17: an
  agent briefed to "add tests to `template/scripts/test-truth-core.py`"
  emitted a whole-file rewrite and took 784 lines with it, stripped the A3
  `tracked_files` seam out of `shellio.py` (production code its brief
  forbade it to touch), and deleted `docs/diagnosis-2026-08/`. None of
  that reddened a suite — deleted tests do not fail. The same session's
  SEARCH delegation (an inventory of every `evidence_paths` consumer,
  every call site with its file:line) was accurate and saved real time.
  So: `git diff HEAD > <scratch>/snapshot.patch` before handing an agent
  write access, and after ANY delegated edit read `git diff --stat` for
  files outside its scope and for net-negative line counts inside it — a
  net -784 on an "add tests" task is the tell. A killed agent can still
  land writes while shutting down, so re-verify AFTER `TaskStop`, not
  before. `scripts/mutate.sh` mutates `template/truthlib/*.py` in place
  and warrants the same snapshot-then-compare.
- A pre-edit whisper hook is wired (`.claude/settings.json` → PreToolUse
  → `scripts/truth-whisper.py`, ADR-005 trial): editing a path the
  ledger watches injects the mechanical prediction of what your commit
  will stale; `docs/archive/` and `.truth/claims.jsonl` are deny-listed
  (edit tools blocked — the ledger changes only through the CLI). The
  whisper count per session lives in `.git/truth-whisper.seen`; that is
  the ADR-005 adoption-gate metric. `docs/archive/` is additionally
  guarded harness-independently at pre-commit (`.githooks/pre-commit`) —
  but only while `core.hooksPath=.githooks` is set, and that is LOCAL
  config no mechanism keeps true. `truth doctor` is the only thing that
  says it lapsed; it had lapsed, and the freeze rested on the edit-tool
  hook alone until 2026-08-21 (canary escape — see the worktree rule
  above). The consumer hooks are untemplated, so they have no home in the
  template canary; their regression gate is
  `python3 template/scripts/test-integrations.py` — deny voice, main-tree
  AND linked-worktree whisper, injection-verified, plus the session
  digest, the CLI exit contracts and the Tier C instruments. The pre-push
  RELEASE BATTERY (`scripts/release-battery.sh`) has had NO gate of its
  own since `32022c6` (2026-08-15) retired `scripts/test-release-battery.sh`
  with the rest of the bash scaffolding and nothing replaced its **twelve**
  arms (`git show 32022c6^:scripts/test-release-battery.sh | grep -c '^echo "ARM'`).
  This paragraph said SIX until 2026-08-21, and six was the count on the day
  the sentence was first written; `3c449a4` took it 6→12 on 2026-08-02 and the
  prose never followed. Anyone rebuilding to the stale figure would rebuild
  half the harness and think it done — which is the AGENTS.md rule about
  restated numbers, firing on AGENTS.md itself. Its doctrine stands and is
  exactly why that gap matters: do not add an arm you have not seen fail.
- Retracting a claim is HUMAN-ONLY (G12) and no agent flag opens it.
  `TRUTH_HUMAN` exists for the ADR-011 ack ceremony; reaching for it to
  get past a tombstone refusal is exactly the judgment laundering the
  gate is there to refuse. So migrating a claim onto a named watch
  policy is a TWO-PERSON ceremony: an agent files the successor and the
  independent verdict, a human runs the retraction. The order is forced
  opposite to how it reads — `--cause restated` REQUIRES an existing
  `--successor`, so the successor is born while its predecessor is still
  live and trips the G8 near-duplicate gate every single time.
  `--duplicate-ok` is therefore the ceremony, not a workaround: its
  `overridden_duplicates` stamp records the exact predecessor id, which
  is the provenance the migration wanted written down anyway. Until the
  human half runs, the ledger legitimately holds live duplicate pairs —
  visible cost of the gate, not a defect (FAZA 3 step 3.3 pilot).
- No module under `template/truthlib/` may import a stdlib module newer
  than the CLI's Python floor AT MODULE SCOPE. `structural.py` imported
  `tomllib` (3.11+) while it was a leaf nothing reached, which cost
  nothing; the moment `kernel` imported it, the floor of the WHOLE CLI
  rose from 3.9 to 3.11 for every consumer repo — to serve one of four
  supported formats. Unit tests are structurally blind to this: they run
  on whichever interpreter you invoke them with. The canary is not, and
  caught it — its tracker arms run `truth ready` under
  `PATH="/usr/bin:/bin"`, where macOS ships 3.9, and nine arms went
  CAUGHT -> MISSED on a raw ModuleNotFoundError traceback. Guard such an
  import with `try/except ModuleNotFoundError` and degrade to a refusal
  that names the interpreter, so the failure is a sentence at intake
  rather than a traceback inside a sweep.
- An analysis is a claim and carries an evidence class like any other.
  Before a finding changes what anyone does, name what backs it: a command
  that re-runs, or a stated basis. A conceptual frame — layers, hierarchies,
  "this is the epistemic tier" — is NEITHER, and earns no conclusion on its
  own; at best it is a hypothesis generator that says where to point a
  measurement. The 2026-08-18 diagnosis ran that drill four times and the
  frame lost three: it predicted `kernel.py` would be the weakly covered
  module (measured that day: `validate_events` 96.6%, 173/179 mutants — the
  strongest part of it), read 165 ADR→arm citation edges as a dependency
  inversion (40 sites read by hand: incident citations, meaning nothing),
  and called a 79%→47% label/import correlation drop a degradation (it was
  two clean new modules diluting the pairs — evidence the refactor worked).
  It won once, and that win is the shape to copy: asking which layer was
  weakest sent a grep at `docs/governance/gate-metrics.md`, which found six
  review dates already past and nothing in the repo enforcing them. The
  frame chose the grep; the grep is the finding.
- Say which half you are on. A sentence that restates a frame in the
  system's own vocabulary — "the ledger is the ontological layer, the gates
  are axiological, the fold is the epistemic bridge" — is true,
  unfalsifiable, and load-bearing for nothing. Writing it feels like
  understanding, which is why it survives review. If you cannot follow such
  a sentence with a path, a number, or a command, delete it instead of
  shipping it as insight.
- A doc review may VETO, and its off-scope findings outlive the session. The
  reviewer's verdict is a gate, not an opinion: on FAIL the change comes out,
  and it comes out before anything is built on it — `template/docs/**` is
  overwritten by `copier update` and appears in no `_skip_if_exists`, so a
  wrong sentence there is re-imposed on every consumer forever. On 2026-08-18
  the reviewer failed a header sentence whose own first clause was a countable
  falsehood ("the four sections" — there are five, `## Where the arguments
  went` being the fifth), read past twice by the author who had run the
  heading list himself; reverted in `e770fc0`. File the review's OFF-SCOPE
  findings as issues in the same sitting — that review surfaced three defects
  older than the change under review (wk-8437672f, wk-4f60611d, wk-1e579b90),
  and an unfiled finding dies with the session that found it.
- **A worktree, not a branch, is what isolates parallel agents here.** A
  branch protects the commit graph; the commit graph was never what broke.
  Measured on the 2026-08-17/18 session: a feature branch was cut to keep out
  of a concurrent worker's way, **0 commits then landed on `main`** and every
  subsequent commit went to the branch instead — each other agent simply
  followed onto it (re-check with
  `git rev-list --count $(git merge-base main HEAD)..main`), so the branch
  was `main` under another name plus a pending merge. In the same session the
  SHARED WORKING DIRECTORY was destroyed twice (a subagent's whole-file rewrite;
  a `git stash` from another session), and a branch prevents neither. This repo
  has no PR flow to make a branch mean review-before-merge: it commits to `main`
  behind a pre-commit gate and a pre-push battery. So branch only for work that
  might be abandoned WHOLESALE; otherwise commit to `main` and give each
  concurrent agent its own `git worktree`.
  Two consequences of worktrees worth knowing before you are surprised by them:
  ADR-045's ledger flock is placed under `--git-dir`, which in a linked
  worktree is `.git/worktrees/<name>` and NOT the shared `.git`, so the lock
  does not span worktrees — it does not need to, because each worktree has its
  own `.truth/claims.jsonl` and the two histories reconcile by the union merge
  the ledger is built for (INV-A, ADR-031). But until you merge, `truth list`
  and `truth reproduce` in a worktree answer about a DIFFERENT ledger than
  `main`'s, which is a real way to reach a confident wrong conclusion.
  A third consequence is practical: `.venv/` is gitignored, so a fresh
  worktree has none and `make` silently falls back to the system `python3`
  — symlink the main tree's `.venv` in, or the schema arm goes dark.
- **NEVER run the canary, the battery, or `git push` from a LINKED worktree.**
  Edit there; VERIFY from the main worktree. The canary escapes its sandbox
  when its cwd is a linked worktree, and it scribbles on shared state:
  measured 2026-08-20 21:48, a battery run triggered by `git push`'s pre-push
  hook wrote fixture commits (`init`, `add comment`, `third line`) onto the
  SHARED repository's `main`, created six fixture branches (`um-side`,
  `umh-tamper`, `bl-rewrite`, …), repointed the worktree's own branch ref at
  `canary: init`, set `core.bare=true` — which breaks the MAIN working tree
  outright (`git status` → "this operation must be run in a work tree") — and
  overwrote `user.name`/`user.email` with the sandbox identity, so the NEXT
  FOUR commits by two different sessions were authored by
  `test-actor <test@example.com>` before anyone noticed
  (`git log --format='%h %an' | grep test-actor`). That last one is the
  damage you cannot repair: config and refs are restorable, a wrong author
  in published history is not.
  `mkrepo()` in `truth-canary.sh` does a bare `cd "$1"` with no `|| exit`,
  under `set -u` and NO `set -e`, so a failed cd lets `git init -b main .`
  run wherever the shell happens to be standing.
  The differentiator is verified, not assumed: the same canary run from the
  MAIN tree produced 0 new branches and left `core.bare` untouched.
  Repair, in this order, and nothing is lost — commits and files survive, it
  is refs and config that get scribbled on:
  `git config core.bare false`; `git update-ref refs/heads/main <real-sha>`;
  `git update-ref refs/heads/<your-branch> <your-sha>` (find it with
  `git log --oneline <sha>`, which still resolves); delete fixture branches.
- **`git add <file>` takes the other agent's hunks too.** Filtering
  `git status` by FILE is not enough when two agents edit the SAME file, and
  the failure is silent in a shared tree. Measured 2026-08-20: a commit of
  mine added seven tests to `test-truth-core.py` — three mine, four another
  agent's ADR-054 arms whose implementation was still uncommitted. HEAD then
  carried tests for code that was not there and the battery went BLOCKED,
  invisible locally because the missing implementation sat in the shared
  working tree beside it. Before committing a file another agent is also
  editing, read `git diff --cached <file>` and confirm every hunk is yours;
  `git add -p` if it is not. To unpick one later, extract the hunk from the
  bad commit and `git apply -R` it — never hand-edit, and never finish
  someone's work for them by committing their half too.

See `template/.truth/README.md` for the layer's full documentation.
