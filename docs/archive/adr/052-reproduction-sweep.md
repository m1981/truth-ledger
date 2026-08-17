# ADR-052: ask every live claim whether its evidence still reproduces

Status: **PROPOSED** (2026-08-13, drafted by the implementing session) — NOT
accepted. The code exists in an uncommitted working tree; the decision below
is the operator's to make or refuse. Drafted here because the argument, not
the diff, is what leaks across session boundaries — and because ADR-051's
*Non-goals* already names this verb by name and owes it a record.
Date: 2026-08-13
Extends: ADR-051 (the mechanical form of its residual — "running
`truth reproduce` in CI, where a different machine makes the question answer
itself"), ADR-050 (the 7:1 false-staling ratio this instrument exists to
measure against), ADR-030 (reaffirm's triage shape, reused for a different
population), ADR-009/029 (the screen gates execution — one screen, one
executor), ADR-012 (a mismatching hash is a judgment call, so this verb files
nothing), ADR-042 rule 2 (zero coverage is a failure, given an exit code here).
Cites: ADR-016 (the refresh reader walks fold order), ADR-005 (a second
differ is forbidden — `changed_files_since` became a range parameter rather
than gaining a sibling), ADR-038 (`dirty_watch`, reused for the fourth shape),
ADR-046 (Tier B: this is a template verb, not a meta-repo instrument, because
its output gates CI), ADR-047 (adoption metric below).
Supersedes: —

## Context

The ledger has exactly one automatic tripwire: *a watched path moved, so this
claim is suspect*. ADR-050 measured what it costs on the kuchnie ledger —
**556 false stalings against 79 true ones, 7.0:1**, and **293 of the 556 were
paid for by a human re-reading the evidence**, not absorbed by reaffirm.

That is the error the system can see. The opposite error it has never been
able to see at all: **a claim that is `live` and whose evidence capsule
quietly stopped being producible.**

Three verbs execute capsules, and all three are blind to it by construction:

| verb | population |
|---|---|
| `verdict --recheck` | one claim, on demand, driven by a human |
| `reaffirm` | claims already knocked out of `live` by the scan |
| intake (G6 double-run) | the claim being filed, once, at birth |

A live claim is by definition not in the second population, and nobody
re-checks by hand what already reads as current. So the question *"can this
still be produced?"* was asked of every claim exactly once — at filing — and
never again unless a path happened to move.

ADR-051 found the consequence: 13 of 126 live claims carrying a hash nobody
could produce, and it closed the *creation* of new ones. It did not give
anyone a way to ask how many exist, where, or why — and its own adoption gate
names `truth reproduce` as the missing measurement.

## Decision

**One read verb that re-runs every live claim's capsule and classifies what
came back.** `truth reproduce [--since TS] [--arm ARM] [--json]`.

Not in `WRITE_VERBS`: it takes no ledger lock, prints no commit-gate banner,
and **files nothing**. A mismatching hash is ADR-012's mechanical-vs-genuine
call and a batch verb has no judge — the same rule that keeps reaffirm's
mismatch arm from auto-filing a `diverge`.

### 1. Four arms

Decided by `reproduce_triage`, pure, in this order — most fundamental
disability first, so a claim that would qualify for two reports the one that
disables the others:

| arm | meaning |
|---|---|
| `no-capsule` | no evidence command. Its standing rests on judgment alone and no mechanical check can ever contradict it. |
| `unexecutable` | `screened=false` (the author's own admission, final), or the CURRENT allowlist refuses it, or exit 127. |
| `reproduces` | hash and returncode match the ADR-051 effective capsule. |
| `capsule-stale` | the recorded capsule can no longer be produced here. |

`unexecutable` is separated from `capsule-stale` deliberately and it is the
distinction the exit code rests on: **a missing `rg` is not evidence drift.**
Collapsing them would fire the CI gate on eleven claims whose facts are
untouched.

Execution goes through the same screened path `--recheck` and `reaffirm` use —
`screen_evidence_command` against the **current** allowlist (committed policy
now, not at filing time), then `run_evidence`, then `recheck_verdict` against
`effective_evidence`. A second screen, a second executor or a second matcher is
forbidden; the one addition is `cwd=repo_root()`, so a sweep run from a
subdirectory does not report the caller's working directory as drift.

### 2. Four shapes — because one count is three different repairs

`capsule-stale` alone is unreadable. `capsule_stale_shape` decides, pure, from
two commit-to-commit diffs of the claim's **own** `evidence_paths` plus the
working tree:

| shape | what happened | repair |
|---|---|---|
| `uncommitted` | a watched path is edited and not committed | commit, re-run |
| `watched-moved` | a watched path changed in `effective-anchor..HEAD` | let the scan stale it, then judge |
| `orphaned-capsule` | a watched path changed in `own-anchor..effective-anchor` — an `agree` carried the claim over it and the capsule stayed behind | `agree --refresh-evidence`, one human judgment at a time |
| `unexplained` | neither window moved, and the output still differs | the command reads something outside its own watch |

**Two of these four exist because the first cut was wrong, and both errors were
found by measurement rather than review.**

`orphaned-capsule` was first decided by `anchor_advanced` alone — the anchor
moved, therefore the capsule is orphaned. That is too weak: it labels a
dark-dependency claim an orphan whenever any unrelated `agree` happened to move
the anchor. The **buried window** (`own-anchor..effective-anchor`) is what makes
the label mean what it says, and it required `changed_files_between(a, b)`;
`changed_files_since` is now its `..HEAD` case, because a second `git diff` call
site is how the F1/F5 screen drift started.

`uncommitted` exists because both windows are commit-to-commit. Running the
sweep on the tree that was implementing it produced a claim hashing
`.truth/generated-paths` reported as `unexplained` — while the file sat edited
and uncommitted three directories away. Without this shape, `unexplained` — the
one arm that is supposed to mean something — silently accumulates "you have not
committed yet". It reuses ADR-038's `dirty_watch`; no new matcher.

### 3. Two exit codes

- **7** — at least one `capsule-stale`. A report, distinct from a crash (1), so
  a CI lane can tell drift from breakage.
- **8** — the sweep examined **zero** claims. ADR-042 rule 2: an instrument
  that measured nothing has not passed, it has failed to run. An empty sweep
  exiting 0 is indistinguishable from a healthy repo at the CI summary line,
  which is the whole failure mode that rule exists to forbid.

## Measured

Every number below is from the real CLI on a real ledger, and the sweep was
cross-checked against a **reimplementation written from this ADR's text rather
than from `truthlib`** — 126 claims, **zero per-claim disagreements**. Checking
a fold with the fold is not a check.

**kuchnie @ `ae16a60`, macOS, operator's working tree**

| arm | n |
|---|---|
| reproduces | 86 |
| capsule-stale | **7** — all `orphaned-capsule` |
| unexecutable | 11 — `rg` ×7, `sqlite3`, `bash`, `cd`, `.venv/bin/python` |
| no-capsule | 22 |
| examined | 126 |

**The same commit measured three ways, which is the finding:**

| tree | reproduces | capsule-stale |
|---|---|---|
| Linux container, clean clone @ `6deb001` | 78 | **13** |
| macOS, clean worktree @ `6deb001` | 82 | **9** |
| macOS, operator's tree @ `ae16a60` | 86 | **7** |

The container/macOS gap at one commit is **four claims that depend on the
machine**. The clean/dirty gap is **two claims hostage to gitignored
`__pycache__`** — `ls kitchen-cam/src/kitchen_cam | sort` and
`grep -rln recipe kuchnie-core/src/kuchnie_core` both read build artifacts no
tripwire watches, and both reproduce only on a tree that has them.

**This verb measures the working tree, not the commit.** That is stated rather
than warned about: an "ignored files present" banner would fire in every repo
and train `2>/dev/null` (the ADR-046 noise lesson). The report carries `head`
and `dirty` instead, and CI — a clean checkout on another machine — is the
mechanism that surfaces it.

## Consequences

The orphan population becomes a number with a name attached, and the two
error classes stop being one word. `unexplained` in particular names claims
whose watched set is **wrong** — a defect no other surface reports.

**CI is not a separate mechanism.** A clean checkout on another machine makes
`unexplained` there minus `unexplained` here the machine-dependent population,
named. That measurement **disappears once the orphans drain**, so the CI lane is
worth landing before the repair, not after.

**No bulk repair.** Refreshing the orphan population by script is the
judgment-laundering ADR-030 declines, and would convert a visible count into an
unexamined one. Each claim passes through a human `agree --refresh-evidence` —
or, if the sentence genuinely no longer holds, a retraction. Both drain it
honestly.

**Cost:** one screened execution per live capsule per sweep. On kuchnie, 93
executions in ~1.6s wall clock. This is now the **fifth** documented execution
site for an evidence command (intake ×2, manual `agree` on a path-claim,
`--recheck`, `reaffirm`), and the machinery doc owes a single table.

## Non-goals — residuals owned

**Not a gate on anything but its own exit code.** It files nothing, changes no
status, and touches no fold.

**Not a judge.** `capsule-stale` is a report; deciding mechanical-vs-genuine
stays ADR-012's, and stays human.

**Not proof of environment independence.** It measures one machine at a time.
The independence signal is the *difference* between two runs, which requires
someone to run it twice.

**`unexplained` is a residual bucket, not a diagnosis.** It says the command
reads something the claim does not watch; it does not say what.

**Top-level judgement only on the population.** A claim whose command is
non-deterministic in a way that happens to hash stably is invisible here, as it
is everywhere else (G6 is an intake check, not a standing one).

## Adoption gate (ADR-047)

**Metric:** the `capsule-stale` count and its shape split, local and in CI.
**Data source:** `truth reproduce --json`.
**Next review:** 2026-11-13, in the R11 monthly slot.
**Retirement test:** if `capsule-stale` is zero locally **and** in CI across
two consecutive reviews, the class ADR-051 closed is not recurring and this
verb drops from the CI gate to an on-demand instrument. If instead
`unexplained` dominates, the finding is about watch quality (ADR-037's
territory), not about this verb.

**Falsifier:** a live claim whose capsule does not reproduce and which this
sweep reports as `reproduces` — or an `orphaned-capsule` label on a claim whose
watched paths never changed before its last agree.
