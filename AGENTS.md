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
`scripts/truth` is a SYMLINK to `template/scripts/truth`: watch the REAL
path in `evidence_paths`, because a watch on the symlink can never fire --
git sees only the link, which never changes. Nothing refuses such a watch;
it is a documented undecidable residual, and this warning was deleted in the
same change that added the pointer below, which is why it is back.
The CLI states its own version on `scripts/truth` line 2, and five other
surfaces are held to it by `TestCrossSurfaceVersions` (ADR-026). Read it
there. This file deliberately does not restate it: a seventh surface that
no test pins is a stale stamp waiting to happen.

## How to read this file

Rules below carry one of three markers, and some carry none.

- **ENFORCED** — something can go red, and the rule names it. If you are
  unsure whether you broke it, run the named thing.
- **NORM** — nothing fails. It is held by reading, or not at all. These are
  not weaker rules; several of them describe damage that has already
  happened here. They are just undefended, and you should know which side of
  the line you are standing on.
- **MECHANISM, UNGATED** — code enforces it today, and nothing stops a later
  edit removing that code. Stronger than NORM, weaker than ENFORCED, and
  the distinction is load-bearing: obey the rule, and do not assume the
  mechanism will still be there.

**An UNMARKED paragraph is a rule nobody classified, not an implied NORM.**
There are several — the pin paragraph and the read-time-TTL paragraph among
them — and the honest reading is that this file has not finished marking
itself. Nothing checks the markers; a marker is prose like everything else
here. Treat an unmarked imperative as undefended until you have found what
would fail.

This file is DOCTRINE, and the rule holds for arm counts and hook state:
they live in the mechanisms that report them and this file points at those
mechanisms. It does NOT hold everywhere, and pretending otherwise was itself
a falsehood — review dates are quoted below, and the `.truth/` counts are
quoted with an apology in the same paragraph. Where a reading is quoted, it
is dated and the command that regenerates it stands beside it. Treat a quoted
reading as stale until you have re-run that command. Every falsehood
`docs/reviews/agents-md-audit-and-review-2026-08-24.md` found in the previous
version of this file was a sentence that had been TRUE once — and every one
was stale in the optimistic direction, describing a gap that had since been
closed. The audit missed a fifth, of the opposite kind, recorded in
`docs/reviews/agents-md-verification-2026-08-24.md`.

## Facts, and where they live

**One home per fact.** Load-bearing facts in README/docs are cited as ledger
ids, never restated as counts or contracts.
*ENFORCED:* `bash scripts/fact-health.sh` — run it after editing docs; it
also rides the release battery. Its corpus is not a hardcoded list: since
2026-08-23 the globs come from `.truth/citation-scope`, read through the
CLI's own loader (find it with `grep -n load_citation_scope
scripts/fact-health.sh`; no line number here, because a citation by position
diverges on the next insertion above it — ADR-012, ADR-037).

What that join fixed is **sweep-to-gate**, not scope-file-to-gate: the ADR-036
retraction gate reads the scope file by definition (`citation_sweep()` in
`template/truthlib/cli.py`), so those two could never drift. It was the SWEEP
that hardcoded its own corpus and saw 31 files where the gate saw 21. Since
`af6f7f5` both read one loader, and their INCLUSION cannot diverge.
Their EXCLUSION still can: the sweep subtracts a hardcoded list of frozen-
reference prefixes (`grep -v` lines just below the loader block) that is
derived from nothing. Today it excludes zero files, because no glob in
`.truth/citation-scope` matches any of them — inert, not absent. Add
`docs/reviews/*.md` to the scope file and the divergence reopens silently.

Two further limits worth knowing: it matches ledger IDs only, and the scope
file currently names `*.md` only — a figure restated inside a `.py` string is
invisible to it twice over.

**A retracted NUMBER is swept separately.** That blind spot is why
`.truth/retracted-figures` exists: one line per withdrawn figure, its
replacement, and where it was retracted. The rule it enforces is that a
retracted literal may still appear, but only NEXT TO its replacement —
which is what a correction looks like; a lone occurrence is a stale
restatement.
*ENFORCED:* `bash scripts/retracted-figures.sh`, wired into
`scripts/release-battery.sh` (section 3b). Its regression arm in
`scripts/test-release-battery.sh` covers both halves, unevenly: it mutates the
invocation and proves a failing sweep BLOCKS, but the empty-policy half is a
`grep -q` for the sentence in `scripts/release-battery.sh` rather than a run
of that path — it proves the branch is still written, not that it behaves.
Find the arm by what it asserts,
not by its number: `grep -n 'retracted-figures sweep must block'
scripts/test-release-battery.sh`. Arm numbers here are ordinals; they
renumber on any insertion, and this repository has measured that name
references rot while pattern references do not.

When a journal entry retracts a figure, add the line to the policy file — do
not go grepping literals by hand. **Know what that edit does and does not
do:** `.truth/retracted-figures` is watched by NO claim, so editing it stales
nothing and forces no verdict. The sweep is the only thing that reads it, and
only at battery time.

**The normative mechanism spec** is `docs/truth-ledger-paper-v3.md` §1; the
CLI contract summary is `template/.truth/README.md`. Do not restate either
elsewhere — link or cite. *NORM.*

**Normative prose cites a position** (ADR-060). A paragraph that tells
someone what to do names the record it derives from, and that citation is
freshness-checked: when the cited position is amended or superseded, the
citing paragraph goes SUSPECT until a human confirms it. The hashed target
is the position PLUS the set of records that amend it — ADR-019 was never
edited, ADR-057 superseded it from outside. *ENFORCED for the corpus the
arm-index covers -- which is exactly two files, `PROSE_DOCS` at
`instruments/arm-index.py:116`: the paper and `truth-ledger-explained.md`.
**AGENTS.md is not one of them** (`grep -c 'AGENTS.md' .truth/arm-index-prose-hashes`
returns 0), so for this paragraph, and for this file, the marker is NORM and
nothing reddens on it.*

**Accepted ADRs are immutable in body**; corrections land as `Amended by:`
lines in the status block. *NORM.* Do NOT reach for ADR-002 or ADR-004 as the
example: both live under `docs/archive/adr/`, which the next paragraph's gate
refuses to stage, so the procedure cannot be performed where they are. And
`grep -l 'Amended by' docs/decisions/*.md` returns **nothing** -- the norm has
no live instance at all, and has never been exercised in a place that permits
it. Corrected 2026-08-26; the contradiction stood in this file until a review
that was not given the specification found it.

**`docs/archive/` is frozen verbatim**; never update it.
*ENFORCED, twice:* `.githooks/pre-commit` refuses any staged path under it
(the harness-independent backstop), and `scripts/truth-whisper.deny` blocks
the edit tools. The hook half depends on `core.hooksPath=.githooks`, which
is LOCAL config no mechanism keeps true — `truth doctor` is the only thing
that reports it either way, and it has lapsed before. Run `truth doctor`
rather than assuming.

**Some control surfaces carry pins. Not all of them, and what a pin actually
does is narrower than it sounds.** Read this whole paragraph before relying
on it; the shorter version of it that stood here was wrong in the optimistic
direction.

**Editing a pinned file changes NO status.** Since ADR-057 `stale` is a
projection over the claim's own `ts` and `ttl_days` and is reachable from no
record at all; `diverged` is reachable only from a filed verdict. So nothing
happens at edit time, and nothing happens at commit time either. What
observes the edit is **`scripts/truth reproduce`**, which re-runs each live
claim's recorded capsule and exits **7** when one no longer reproduces — and
it rides `scripts/release-battery.sh`, so the finding lands at **push**.
`scripts/truth list --live` and `--diverged` are read verbs that exit 0
whatever the ledger says; they cannot go red, and reaching for them after
editing a pin is how an edit reads as health.
*ENFORCED:* `scripts/truth reproduce` (exit 7), via the pre-push battery,
which invokes it as `python3 template/scripts/truth reproduce`. Run it
yourself after touching a pinned file rather than waiting for the push.

The remedy is a **judgement, not a human ceremony**: `truth verdict <id>
diverge`, or an agree carrying `--refresh-evidence "<sentence>"` (ADR-051).
Only RETRACTION is human-only (G12). An agent can clear a diverged pin, and
does. For the split, ask the ledger rather than this sentence --
`grep '"evidence_refresh"' .truth/claims.jsonl | grep -c '"actor"'` --
because the figure that stood here rotted **inside this working tree**: it
said six, three and three, which was true at HEAD and false by the time the
file was read, the operator having filed a seventh the same day.

Pinned by a `sha256sum` claim, enumerated rather than generalised because the
last generalisation here was false: `.truth/accept-allow` (tr-96351a43),
`.truth/citation-scope` (tr-48fc1f89), `.truth/evidence-allow` (tr-11701d6f),
`.truth/evidence-deny` (tr-6a3c9fef), `.truth/generated-paths` (tr-165faff1),
plus `scripts/truth-whisper.deny` (tr-45312cff), `.claude/settings.json`
(tr-df856f43) and `.githooks/pre-commit` (tr-bcd40e31). Pinned by a content
recipe instead: `scripts/fact-health.sh` (tr-a00459ec) and `.githooks/pre-push`
(tr-b1472ca1). **Both battery scripts are pinned too and are deliberately not
given ids here:** `scripts/test-release-battery.sh` carries a digest pin that
is **DIVERGED right now** — an open judgement, and its id is left out
precisely because a diverged id in live prose reddens `fact-health`, which
would make this file fail for correctly describing the ledger.
`scripts/release-battery.sh` carries several pins at once, which is more than
a sentence can hold -- and asking for them takes TWO questions, not one:
`truth impact <path>` reports only ACTIVE claims, so a diverged pin on the
same path is invisible to it and needs `truth list --diverged`. A count
written here was wrong on both the number and the split for exactly that
reason. Ask both verbs.

So the split is not "policy files by digest, scripts by recipe" -- the
surfaces above mix both, and at least one carries more than one kind at once.
The counts that stood here are deliberately gone: they were re-derived from a
single verb that cannot see diverged pins. The generalisation has no shape
worth keeping — this is a list, and
lists are asked for, not remembered.

**Twelve of the seventeen files in `.truth/` are pinned by no claim in any
status** (measured 2026-08-26; the figure that stood here said eleven of
sixteen and its own next paragraph already disagreed with it): the four
`*-opt-out` files, `arm-index-paper-baseline`, `register-index-baseline`,
`arm-index-link-hashes`, `arm-index-prose-hashes`, `watch-policies`,
`waiver-not-an-override` -- introduced by the same work that wrote the
sentence and left out of it -- `claims.jsonl` itself, and `retracted-figures`, which this
file tells you to edit two sections above. Editing any of those produces no
divergence and no verdict. *NOTHING enforces them.*

Do not maintain the membership here — ask the ledger. Recount it with
`ls .truth | wc -l` against each claim's watch set; this paragraph is
DOCTRINE carrying two counts it should not, and they rot the next time an
instrument adds a baseline file, which this repository does routinely.
The ids, unlike the counts, ARE held: if one of them leaves `live` for
`stale`, `diverged`, `retracted` or `disputed`, `scripts/fact-health.sh`
reddens on THIS file. `cannot_verify` and `unverified` produce a WARN and
exit 0 — the net has a documented hole, and it is this one.

**Machine-local operational notes live in `.local/`** (gitignored, never
commit its contents): the deployment-site disk mapping and this machine's
workarounds. Agent-agnostic by design — read them there, update them there,
and do NOT mirror them into any harness-private memory; a fresh clone won't
have `.local/`, which is intended. *NORM.*

## Time, TTL, and what DONE means

**A fact about a DEPLOYMENT** (the pilot, the SDK repo) takes `--ttl-days`,
not `--paths` — no git event here can observe another repository. Treat that
TTL as a timer, not a detector: a claim pinning the pilot's template version
sat wrong for weeks inside its 60-day window because nothing could notice
and nobody re-read it. Re-verify deployment facts at release time; do not
let the clock stand in for a check. *NORM.*

**Expiry is computed at read time** (ADR-057, PROPOSED, unreviewed).
`fold(events, now_dt)` derives `stale` from `claim ts + ttl_days`; there is
no scan, no bot, and **no NEW `invalidation` record**. The kind is inert for
status, not absent: about two thousand TTL invalidations written by the
retired scan are still in the ledger and still readable, and `kernel.py`
skips them in a branch written out rather than deleted so the decision stays
on the page. Count them yourself rather than
carrying the number in prose: `grep -c '"kind": "invalidation"'
.truth/claims.jsonl`. Two consequences for your advice
about `--ttl-days`: the shelf life counts from the claim's own `ts` with a
strict boundary, and a claim's status no longer depends on whether anyone
swept. `ttl-scan`, `reaffirm` and `invalidate-scan` are gone; do not reach
for them and do not tell a consumer to. The record is PROPOSED, so the code
here may be ahead of the record rather than behind it — say which when it
matters.

**An item is DONE when a gate exists that can go red for that item's named
reason, and someone has demonstrated it going red** (ADR-061). Three parts,
none optional: a named failure condition (the sentence that, if observed,
means it regressed), a gate that observes it without being remembered, and a
demonstration — the gate was made to fail on purpose and did. A green suite
is not the third part.
Where no gate is possible the item is **DECLARED**, not DONE, and the reason
a demonstration is impossible is the interesting part of the record.
This is the doctrine behind the older rule, which stands: **do not add an arm
you have not seen fail.** *NORM in the plan; ENFORCED per item by whatever
gate that item names.*

## Agent roles (ADR-062)

Four roles, separated by **what each is NOT told**. PROPOSED 2026-08-24, from
one session's measured experience.

| role | receives | must NOT receive | must produce |
|---|---|---|---|
| measure | a measurement spec | any hypothesis about the result | numbers, and a note if it changed the spec |
| implement | a spec + house conventions | — | the change AND a demonstration of its gate going red, restored byte-identically |
| review | the diff + house conventions | **the specification** | confirmed defects, each with the command that reproduces it |
| operator | everything | — | the commit |

Four rules follow, each earned:

1. **The reviewer's ignorance of the spec is load-bearing.** Given the spec
   it checks compliance — "was what was asked built" — instead of
   correctness. The defects that mattered were of the second kind.
2. **An agent never commits.** A dispatcher with an exhausted context cannot
   honestly review, and writing "verified" without verifying is the failure
   INV-O exists to prevent.
3. **The review travels with the change.** Commit them together, so the
   evidence against a change cannot be separated from it. Dispatch the
   review ON THE DIFF, never in parallel with the work producing it.
4. **A measurement is persisted before the next role is dispatched.**
   Write it to `docs/reviews/` FIRST, then dispatch. A finding that lives
   only in a task notification cannot be cited, because there is nothing
   for a later reader to check it against — and the agent dispatched next
   will cite it anyway. This rule exists because that happened here: an
   audit of THIS file was real, was never written to disk, and the
   redrafting agent cited "the 2026-08-24 audit of this file", a document
   that existed nowhere. The phantom citation is what licensed the whole
   restructuring you are reading.

**Self-demonstration is necessary and not sufficient.** The implementing
agent demonstrated its own gate going red on all three checks, restored
byte-identically, and reported honestly — and a defect still passed under
it. Two review passes each found defects the previous pass had cleared.

**Delegate implementation when your own context is thin, not only when the
task is large.** Thin context produces blind patches: that session's worst
act was patching a shipped Tier A gate while out of context, guessing a
variable name the script does not have.

*NORM.* Nothing enforces the separation. The mechanisable residue ADR-062
names — a commit adding or editing a file under `instruments/` with no
accompanying review document is a candidate finding — is not wired to
anything yet.

## Delegation and shared state

**Delegating an EDIT is destructive; delegating a SEARCH is not.** Measured
2026-08-17: an agent briefed to "add tests to
`template/scripts/test-truth-core.py`" emitted a whole-file rewrite and took
784 lines with it, stripped the A3 `tracked_files` seam out of `shellio.py`
(production code its brief forbade it to touch), and deleted
`docs/diagnosis-2026-08/`. None of that reddened a suite — deleted tests do
not fail. The same session's SEARCH delegation (an inventory of every
`evidence_paths` consumer with file:line) was accurate and saved real time.
*NORM:* `git diff HEAD > <scratch>/snapshot.patch` before handing an agent
write access; after ANY delegated edit read `git diff --stat` for files
outside its scope and for net-negative line counts inside it — a net -784 on
an "add tests" task is the tell. A killed agent can still land writes while
shutting down, so re-verify AFTER `TaskStop`, not before. `scripts/mutate.sh`
mutates `template/truthlib/*.py` in place and warrants the same drill.

**`git add <file>` takes the other agent's hunks too.** Filtering
`git status` by FILE is not enough when two agents edit the SAME file, and
the failure is silent in a shared tree. Measured 2026-08-20: a commit added
seven tests to `test-truth-core.py` — three the author's, four another
agent's ADR-054 arms whose implementation was still uncommitted. HEAD then
carried tests for code that was not there and the battery went BLOCKED,
invisible locally because the missing implementation sat in the shared
working tree beside it.
*NORM:* before committing a file another agent is also editing, read
`git diff --cached <file>` and confirm every hunk is yours; `git add -p` if
it is not. To unpick one later, extract the hunk from the bad commit and
`git apply -R` it — never hand-edit, and never finish someone's work for
them by committing their half too.

**Export a stable `TRUTH_SESSION` before filing anything.** The default is
ppid-derived and differs per one-shot shell call (Claude Code Bash, `pi -p`),
so records from one working session scatter across ids and ADR-010's
author≠verifier refusal cannot be trusted from the default — separation by
PID accident is not separation. A verifier exports its own
`TRUTH_SESSION=verifier-<slug>`; never scribe verdicts through the author's
session. *NORM. Nothing checks that you did.*

**Doc edits get an independent reader BEFORE the commit lands.** Any change
touching `docs/` or `template/.truth/README.md` is read by a fresh
session/agent that did not author it: mechanical sentences against the code,
version mentions on UNPINNED surfaces, cross-surface consistency, which live
claims the text breaks. The lockstep tests refuse only the pinned stamps;
everything else is caught by reading or not at all — the v0.9.15 release
proved both halves (a missed unpinned Scope header, found only by an
independent reviewer). *NORM. Do it unprompted; nothing will ask.*

**A doc review may VETO, and its off-scope findings outlive the session.**
On FAIL the change comes out, and it comes out before anything is built on
it: `template/docs/**` is overwritten by `copier update` and appears in no
`_skip_if_exists`, so a wrong sentence there is re-imposed on every consumer
forever. On 2026-08-18 the reviewer failed a header sentence whose own first
clause was a countable falsehood ("the four sections" — there were five),
read past twice by the author who had run the heading list himself; reverted
in `e770fc0`. File the review's OFF-SCOPE findings as issues in the same
sitting — that review surfaced three defects older than the change under
review, and an unfiled finding dies with the session that found it. *NORM.*

**Downgrading an independent finding's severity is itself a claim** — the
one that stops further work, so the highest-leverage one to be wrong about.
Before building on a downgrade, dispatch a fresh adversary to REFUTE the
disposition; after building, a second one to attack the artifact. Three
shipped releases (ADR-021, ADR-024, ADR-028) exist because exactly this
drill flipped a "just document it" back into a code fix. *NORM.*

## Worktrees and the push boundary

**A worktree, not a branch, is what isolates parallel agents here.** A branch
protects the commit graph; the commit graph was never what broke. Measured
2026-08-17/18: a feature branch was cut to keep out of a concurrent worker's
way, 0 commits then landed on `main`, and every other agent simply followed
onto the branch — so it was `main` under another name plus a pending merge
(re-check with `git rev-list --count $(git merge-base main HEAD)..main`). In
the same session the SHARED WORKING DIRECTORY was destroyed twice, and a
branch prevents neither. This repo has no PR flow to make a branch mean
review-before-merge: it commits to `main` behind a pre-commit gate and a
pre-push battery. So branch only for work that might be abandoned WHOLESALE;
otherwise commit to `main` and give each concurrent agent its own
`git worktree`. *NORM.*

Three consequences of worktrees, before they surprise you:

- ADR-045's ledger flock is placed under `--git-dir`, which in a linked
  worktree is `.git/worktrees/<name>` and NOT the shared `.git`, so the lock
  does not span worktrees. It does not need to: each worktree has its own
  `.truth/claims.jsonl` and the two histories reconcile by union merge
  (INV-A, ADR-031). But until you merge, `truth list` and `truth reproduce`
  in a worktree answer about a DIFFERENT ledger than `main`'s.
- `.venv/` is gitignored, so a fresh worktree has none and `make` silently
  falls back to the system `python3` — symlink the main tree's `.venv` in,
  or the schema arm goes dark. *NORM.*
- **NEVER run the canary, the battery, or `git push` from a LINKED
  worktree.** Edit there; VERIFY from the main worktree.

That last one **was NORM, and it cost more than any other norm here. It is
now a mechanism, and the prose that said otherwise was three days stale in
both directions of this file.**
Measured 2026-08-20 21:48: a battery run triggered by `git push`'s pre-push
hook wrote fixture commits onto the SHARED repository's `main`, created six
fixture branches, repointed the worktree's branch ref at `canary: init`, set
`core.bare=true` — which breaks the MAIN working tree outright — and
overwrote `user.name`/`user.email` with the sandbox identity, so the next
FOUR commits by two different sessions were authored by
`test-actor <test@example.com>` before anyone noticed
(`git log --format='%h %an' | grep test-actor`). Config and refs are
restorable; a wrong author in published history is not. The mechanism was
`mkrepo()` in `template/scripts/truth-canary.sh`: a bare `cd "$1"` with no
`|| exit`, under `set -u` and NO `set -e`, so a failed cd let
`git init -b main .` run wherever the shell happened to be standing. The
differentiator is verified, not assumed: the same canary run from the MAIN
tree produced 0 new branches and left `core.bare` untouched.
Repair, in this order, and nothing is lost — commits and files survive, it is
refs and config that get scribbled on: `git config core.bare false`;
`git update-ref refs/heads/main <real-sha>`;
`git update-ref refs/heads/<your-branch> <your-sha>` (find it with
`git log --oneline <sha>`, which still resolves); delete fixture branches.

**What prevents it today, and what still does not.** `441de48` (2026-08-21)
made the norm a mechanism. `mkrepo()` now refuses twice before it can write:
`cd "$1" || { ... exit 1; }`, and then an outright refusal if the sandbox
resolves inside ANY git repository, naming the owner. Demonstrated both ways
in `docs/reviews/agents-md-verification-2026-08-24.md`: a sandbox under
`mktemp -d` passes, a sandbox inside a worktree exits 1, an unenterable path
exits 1.

The guard is real; it is **not DONE under ADR-061**. No arm in the battery
gate, `test-integrations.py` or `test-truth-core.py` exercises it, so a later
edit that removes it goes unnoticed — the mechanism that replaced the norm has
no gate of its own. Keep obeying the rule for that reason, not because the
code is missing. *MECHANISM, UNGATED.*

**`bash template/scripts/truth-canary.sh` is deliberately NOT on the evidence
allowlist** (ADR-009's test-runner rule), so `verdict --recheck` will refuse
to execute any claim carrying it: run the suite yourself and judge the
ALL-CAUGHT sentinel by hand. Accepted ceremony, decided 2026-07-13 — do not
"fix" it by allowlisting `bash`, which would gut the screen.
*ENFORCED:* the evidence screen refuses. `.truth/evidence-allow` is pinned
(tr-11701d6f), so widening it makes that claim's capsule stop reproducing and
`truth reproduce` exits 7 at the next push — a judgement is forced, not a
human one; see the pin paragraph above for which verb actually sees it.

**The pre-push boundary.** `.githooks/pre-push` runs a tag-check arm and then
`scripts/release-battery.sh`. The tag-check WARNs when the CLI's stated
version has no tag and FAILs when a tag's tree states a different version;
its WARN branch deliberately does not `exit`, because it once did and
silently skipped the whole battery in exactly the window where most change
lands. **An advisory must not be able to cancel a gate.**
*ENFORCED:* `.githooks/pre-push`, and an arm of
`scripts/test-release-battery.sh` holds the tag-check ahead of the battery
(`grep -n 'tag-check arm ahead of the battery' scripts/test-release-battery.sh`).

**The battery has its own regression gate**: `scripts/test-release-battery.sh`,
rebuilt 2026-08-21 after `32022c6` retired the bash scaffolding. It reports
its own arm count (`TOTAL_ARMS` in its header) and takes `--arm N` to run
one; read it there rather than quoting a number here — the number in this
paragraph went stale twice before the sentence was deleted.
*ENFORCED:* an arm of that same gate makes the battery run it when the
battery moves, and only then
(`grep -n 'run THIS gate when the battery moves'
scripts/test-release-battery.sh`).

**Consumer hooks are untemplated**, so they have no home in the template
canary. Their regression gate is `python3 template/scripts/test-integrations.py`:
`TestCLIContractsAndRefusals`, `TestClaudeWhisperHook`,
`TestClaudeSessionDigest`, `TestTierCInstruments`,
`TestMarkdownAndSpecHealth` — deny voice, main-tree AND linked-worktree
whisper, injection-verified, plus the session digest, the CLI exit contracts
and the Tier C instruments. *ENFORCED, and it rides the battery.*

**A pre-edit whisper hook is wired** (`.claude/settings.json` → PreToolUse →
`scripts/truth-whisper.py`, ADR-005 trial): editing a path the ledger watches
injects the mechanical prediction of which live claims watch the path you are
about to edit (`truth impact` is the same question asked by hand). It does NOT
predict a status change: nothing stales on commit, and the whisper does not
say it does.
`docs/archive/` and `.truth/claims.jsonl` are deny-listed (edit tools
blocked — the ledger changes only through the CLI). The whisper count per
session accumulates in `.git/truth-whisper.seen`. ADR-005 calls that the
fatigue half of its adoption gate but names **no threshold and no reader**,
so the counter accumulates and nobody reads it. Treat it as unfinished
instrumentation, not as a gate. *NORM.*

## Gates you will meet at intake

**Retracting a claim is HUMAN-ONLY (G12)** and no agent flag opens it.
`TRUTH_HUMAN` exists for the ADR-011 ack ceremony; reaching for it to get
past a tombstone refusal is exactly the judgment laundering the gate refuses.
So migrating a claim onto a named watch policy is a TWO-PERSON ceremony: an
agent files the successor and the independent verdict, a human runs the
retraction. The order is forced opposite to how it reads — `--cause restated`
REQUIRES an existing `--successor`, so the successor is born while its
predecessor is still live and trips the G8 near-duplicate gate every single
time. `--duplicate-ok` is therefore the ceremony, not a workaround: its
`overridden_duplicates` stamp records the exact predecessor id, which is the
provenance the migration wanted written down anyway. Until the human half
runs, the ledger legitimately holds live duplicate pairs — visible cost of
the gate, not a defect. *ENFORCED: the CLI refuses at intake.*

**The freehand watch budget refuses** (ADR-055, ACCEPTED over an unmet
condition — the threshold itself is still unvalidated by data, and the record
says so). Either name a reviewed set with `--watch-policy`, or say why THIS
set is right with `--paths-ok` (stored, decays at 30 days, counted).
Structural selector targets (`path.json#/a/b`) are exempt from both budgets.
*ENFORCED at intake; the override is counted.*

**Six of the eleven CLI-flag overrides are admitted on a sentence, four on
nothing, one on a number — and flags are only one of six carriers** (ADR-059, PROPOSED — its opening premise said "every", and was wrong
until 2026-08-24; the first correction then said "five of eight" in a sentence
that listed six. Do not carry these counts: read them off
`python3 instruments/waiver-index.py`).

Sentence-bearing: `--scope-ok` / `--paths-ok` / `--generated-ok` /
`--evidence-exit-ok` / `--orphan-ok` / `--refresh-evidence`. The gates check
only that the basis is non-empty; `"ok"` and a real argument are the same
value to them.
`instruments/semantic-audit.py` extracts them, and the reader that judges them
is deliberately outside this repository. Write the sentence for that reader.
*ENFORCED as non-empty; NORM as to meaning.*

Bare booleans, carrying no rationale at all: **`--duplicate-ok`**,
**`--evidence-unsafe-ok`**, **`--accept-unsafe-ok`**, **`--single-run`**.
These are not the minor four. They lift EXECUTION screens — admit a
near-duplicate over G8, file a claim whose evidence command the screen refused
(ADR-009), close a work item without running its acceptance oracle (ADR-014),
skip the G6 determinism double-run — where the other six only lift a judgement
about how good a justification is. Reaching for one records that you did, and
nothing about why.

**`--single-run` is the sharpest of them: it writes NO field into the record
at all.** The other three at least leave `screened: false` or
`overridden_duplicates`. Skipping the determinism double-run is invisible in
the ledger, so nobody can count it, ask about it, or find it later. If you
use it, say so in the claim text — that is the only surface left.
*NOT ENFORCED as to meaning, and for `--single-run` there is nothing to
enforce it on.*

Do not read a small `semantic-audit` count as "few gates were bypassed": it
can only see the six that carry a sentence, five of them on ACTIVE claims
only -- `orphan_basis` is read from RETRACTED ones on purpose, being valid
nowhere else, so an active-only scope would report it as 0 forever. Ask `python3 instruments/waiver-index.py` instead -- it
partitions the carriers it CAN enumerate from a source and reports how many
records carry each stamp, the silent ones included. It does not carry the
whole escape surface and says so in its own last lines: five carriers are
recorded by hand from no list at all, syntax and config among them. A
sentence claiming totality here would be the exact shape `docs/waivers.md`
was retitled on 2026-08-25 to kill. The register is `docs/waivers.md`. It is swept against the CLI parser in both
directions, and the reverse direction is **total**: every flag the parser
accepts must be either a waiver row or an entry in
`.truth/waiver-not-an-override` with a reason, so a new flag of any shape
fails until somebody judges which it is. Scoping that check by name is what
hid `--refresh-evidence` and `--single-run` from its own first draft.
*ENFORCED:* `instruments/waiver-index.py`, gated by
`template/scripts/test-integrations.py`.

**Evidence commands run without a shell** (ADR-056, ACCEPTED without the
adversarial pass its predecessor required — the status line keeps that fact).
Two residuals are open and disclosed: glob expansion happens at run time, and
the lexer is where the runner departs from `/bin/sh`. *ENFORCED by the screen
and the executor.*

**The battery may not judge with an apparatus the run authored** (ADR-058,
PROPOSED and deliberately NOT WIRED). The operator ruled 2026-08-23 that the
local battery tests the working tree and isolation moves to the CI boundary
only. Do not wire it back without reversing that ruling in a record. *NORM,
by ruling.*

**No module under `template/truthlib/` may import a stdlib module newer than
the CLI's Python floor AT MODULE SCOPE.** `structural.py` imported `tomllib`
(3.11+) while it was a leaf nothing reached, which cost nothing; the moment
`kernel` imported it, the floor of the WHOLE CLI rose from 3.9 to 3.11 for
every consumer repo — to serve one of four supported formats. Unit tests are
structurally blind to this: they run on whichever interpreter you invoke them
with. Guard such an import with `try/except ModuleNotFoundError` and degrade
to a refusal that NAMES the interpreter, so the failure is a sentence at
intake rather than a traceback inside a sweep.
*ENFORCED:* the canary's tracker arms run `truth ready` under
`PATH="/usr/bin:/bin"`, where macOS ships 3.9. Nine arms went CAUGHT → MISSED
on a raw `ModuleNotFoundError` when this broke.

## Analysis discipline

**An analysis is a claim and carries an evidence class like any other.**
Before a finding changes what anyone does, name what backs it: a command that
re-runs, or a stated basis. A conceptual frame — layers, hierarchies, "this
is the epistemic tier" — is NEITHER, and earns no conclusion on its own; at
best it is a hypothesis generator that says where to point a measurement.
The 2026-08-18 diagnosis ran that drill four times and the frame lost three:
it predicted `kernel.py` would be the weakly covered module (measured that
day: `validate_events` 96.6%, 173/179 mutants — the strongest part of it),
read 165 ADR→arm citation edges as a dependency inversion (40 sites read by
hand: incident citations, meaning nothing), and called a 79%→47%
label/import correlation drop a degradation (it was two clean new modules
diluting the pairs — evidence the refactor worked). It won once, and that win
is the shape to copy: asking which layer was weakest sent a grep at
`docs/governance/gate-metrics.md`, and the grep found **six rows whose next
review date had already passed, with nothing in the repository enforcing
them**. **The frame chose the grep; the grep is the finding.**

That finding is still open, which is why it is restated here rather than
replaced by a pointer. Re-run it:
`grep -n '2026-08-08' docs/governance/gate-metrics.md` returns those six
rows plus the prose line naming the R11 hand-audit they were due at, and
`grep -rn 'Next review' scripts/ instruments/ template/ .githooks/` returns
nothing at all. The registry has carried review dates since `6f3e9b1`
(2026-08-02) and has never had a reader. Read the standing in the registry —
but do not read the presence of dates as the presence of a gate. *NORM,
and the residue is exactly the L4(c) proof-test interval named in
`docs/reviews/mechanism-layers-brief-2026-08-24.md`.*

**Say which half you are on.** A sentence that restates a frame in the
system's own vocabulary — "the ledger is the ontological layer, the gates are
axiological, the fold is the epistemic bridge" — is true, unfalsifiable, and
load-bearing for nothing. Writing it feels like understanding, which is why
it survives review. If you cannot follow such a sentence with a path, a
number, or a command, delete it instead of shipping it as insight. *NORM.*

## Language

Until now this was an unwritten norm; it is written down here so nobody has
to infer it again.

- **Artifacts are English** — docs, ADRs, code comments, claim text, this
  file.
- **Commit messages are Polish in practice.** Read the log before you write
  one and match what is there; nothing enforces either language.
- **The operator may converse in Polish.** Answer in the language you were
  addressed in; the artifact you produce is still English.

*NORM.* No gate reads any of this.

See `template/.truth/README.md` for the layer's full documentation.
