# Agent onboarding — picking up work in this repository

> Reader: any fresh agent session about to change this repo | Enables: reaching a correct picture of the ledger, the open scope and the working regime before touching anything | Update-trigger: the regime changes (AGENTS.md), or the progress source of truth moves

**META-REPO ONLY, and the placement is deliberate.** `prompts/` is a SYMLINK
to `template/prompts/`, so anything written there SHIPS to consumer repos via
`copier update`. This file cites `docs/refactor/`, `docs/decisions/` and
`instruments/`, none of which a consumer has — it would hand them an
onboarding guide to files that do not exist. It therefore lives in `docs/`,
beside the other untemplated surfaces (`scripts/fact-health.sh`,
`scripts/release-battery.sh`). A consumer-facing equivalent would be a
different, shorter document and does not exist yet.

Paste this whole file into a fresh session as its first instruction. It
carries almost no facts on purpose: facts rot, and a prompt that restates
them becomes the defect this project exists to catch (`AGENTS.md`, "one home
per fact"). What it carries is a READING ORDER and a VERIFICATION PROCEDURE.

---

You are joining a repository that runs its own truth ledger and holds itself
to it. Before you change anything, you establish state by RUNNING things, not
by believing a summary — including this one.

## 1. Establish state (do this first, in this order)

```
make help                     # the operational interface; nothing else is the entry point
make health                   # reproduce + fact-health + doc-health + retracted-figures + field-consumers
scripts/truth list --live     # what this repo currently claims to be true
git log --oneline -15         # what just happened, and by whom
git status --short            # work in flight -- possibly ANOTHER agent's
```

Two things that will mislead you if you skip them:

* **Use `make`, or `.venv/bin/python`.** A bare `python3` here lacks
  `jsonschema`, and the core suite then fails one test for a purely
  environmental reason that looks like a real defect.
* **`git status` may show files that are not yours.** Several agents work
  this repo concurrently and commit to the same branch. Read `git log` for
  authorship before assuming a modified file is your predecessor's mistake.
  Do not revert, commit or "clean up" another agent's in-flight work.

## 2. Read, in this order — and cite it rather than restating it

1. `AGENTS.md` — the regime. Every rule there was written after an incident;
   the incident is in the rule. This is the one file to read completely.
2. `docs/refactor/00-RUNBOOK.md` — **the only source of truth about progress.**
   Status lives there, not in any session's memory. Its status table tells you
   what is done, what is blocked and on whom. Start from its header block.
3. `docs/refactor/01-JOURNAL.md` — append-only empirical record. Read the last
   two or three entries; they explain why the code looks the way it does.
   Format is binding for anything you add: command, RAW OUTPUT, conclusion.
   A conclusion without a command is not an entry.
4. `template/.truth/README.md` — the CLI contract. `docs/truth-ledger-paper-v3.md` §1
   is the normative mechanism spec. Cite these; never restate them elsewhere.
5. `docs/decisions/README.md` — the live decision register (records 054+;
   001-053 are frozen at `docs/archive/adr/` and are never edited).

## 3. The regime — non-negotiables

Each of these is enforced somewhere, and the enforcement is the reason it is
short here. Read the cited home before working around any of them.

* **Never edit `.truth/claims.jsonl`.** Status changes are new records through
  the CLI. The edit tools are deny-listed for it.
* **Export a stable `TRUTH_SESSION` before filing anything.** The default is
  ppid-derived, so without it your records scatter and ADR-010's
  author≠verifier separation cannot see you as one session.
* **You cannot retract.** Retraction is a human tombstone decision (G12). If a
  claim should die, `diverge` with a basis saying so, and stop.
  `TRUTH_HUMAN` exists for a different ceremony; reaching for it here is
  judgment laundering (ADR-030).
* **Migrating a claim is birth-before-death.** `--cause restated` requires an
  existing `--successor`, so the successor meets the G8 near-duplicate gate
  while its predecessor is still live. `--duplicate-ok` is the ceremony, not a
  workaround — its `overridden_duplicates` stamp records the predecessor id.
* **A gate that refuses you is usually right.** Before reaching for
  `--paths-ok`, `--scope-ok`, `--duplicate-ok` or `--generated-ok`, state to
  yourself why the gate is wrong. Every override is recorded, decays, and is
  counted in the override report.
* **Doc edits get an independent reader before the commit lands** (AGENTS.md).
* **`make mutate`, never `scripts/mutate.sh` directly.** The raw script scores
  against stale coverage and its survivor list lies; the header explains.

## 4. How to work here

* **One task at a time**, and the loop is fixed: verification → status in the
  RUNBOOK → entry in the JOURNAL → commit.
* **Measure before building.** Recompute the number that justifies a step
  before implementing it, and be willing to have it kill the step. A negative
  result is a valid outcome and belongs in the journal (see J-045, where a
  proposal died on its own measurement).
* **An analysis is a claim and carries an evidence class.** A conceptual frame
  — layers, hierarchies, "this is the epistemic tier" — earns no conclusion on
  its own. If you cannot follow a sentence with a path, a number or a command,
  delete it instead of shipping it as insight (AGENTS.md).
* **Delegating a SEARCH to a subagent is safe; delegating an EDIT is
  destructive.** Snapshot with `git diff HEAD > <scratch>/snapshot.patch`
  first, and check `git diff --stat` afterwards (AGENTS.md carries the
  measurement that made this a rule).
* **Before you finish:** `make battery` must be all-green, and say plainly
  which arms you ran. If something is blocked, say what and on whom rather
  than routing around it.

## 5. Forbidden

Editing `docs/archive/` (frozen, enforced at pre-commit — do not pass
`--no-verify`); editing the ledger by hand; filing a verdict on your own claim
(ADR-010); retracting anything; adding a release-battery arm you have not seen
fail; committing another agent's in-flight work; and reporting a suite as green
that you did not run.

---

**Where the scope of open work lives:** `docs/refactor/00-RUNBOOK.md`, status
table. Anything blocked on a human is marked there with what it is blocked on.
This prompt deliberately names no specific open item, so that it cannot go
stale — read the table.
