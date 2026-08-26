# Handoff: an independent review of `AGENTS.md`

For a session that has not worked on this file. Written under ADR-062 rule 1,
and deliberately written so that it does not brief you.

## Why this document is shaped oddly

ADR-062 separates roles by what each is **not** told. The reviewer is denied
the specification of the change under review, because a reviewer given the
brief checks *"was what was asked built"* — conformance — instead of *"is what
is now written true of this repository"* — correctness. Every defect that has
mattered here was of the second kind.

That ADR also names what actually threatens the arrangement, and it is not
publication: it is **recovery**. A reviewer who can reconstruct the
specification from the dispatcher's message has been briefed by other means,
and a handoff written to be maximally helpful is the easiest way to do it. So
this one omits things you would normally be given. That is the mechanism, not
an oversight, and this file is the first artefact written under that rule.

**You are not being asked to trust it.** If you conclude the omissions make
the review impossible, say so — that finding is more valuable than a review
performed on a reconstruction.

## What you are reviewing

`AGENTS.md`, at the repository root of `~/PycharmProjects/truth-ledger`. It is
**modified and uncommitted**. It is the file every agent in this repository
reads first, so a false sentence in it propagates by being believed and
copied.

```
cd ~/PycharmProjects/truth-ledger
git diff AGENTS.md          # the change
cat AGENTS.md               # the current state
```

Other files in the tree are modified by unrelated work. `AGENTS.md` is the
whole of your subject.

## Nine defects documented against this file

These were recorded in `docs/reviews/agents-md-audit-and-review-2026-08-24.md`
on 2026-08-24. They are listed here **flat and in the order that document
lists them**. Nothing here tells you which, if any, were subsequently
addressed, and the ordering carries no ranking — determining the current state
of each against the tree is the work.

1. `--exit-ok` does not exist; the flag is `--evidence-exit-ok`.
2. "the `.truth/` policy files are *each* pinned by a claim" — 5 of 16 are,
   and the file instructs editing one that carries no claim.
3. "policy files by `sha256sum` and the scripts by a content recipe" — false
   for `.githooks/pre-commit`, `scripts/truth-whisper.deny` and
   `scripts/test-release-battery.sh`.
4. "there is no scan, no `invalidation` record, no bot" — about two thousand
   `invalidation` records exist; ADR-057 makes the kind inert for status, not
   absent.
5. It cites "the 2026-08-24 audit of this file", which did not exist when the
   sentence was written.
6. "the scope file and the ADR-036 retraction gate cannot drift apart" names
   the wrong pair — the gate reads the scope file by definition.
7. It cites `fact-health.sh:119` by line number, the shape ADR-037 and ADR-012
   lint as a recipe that diverges mechanically.
8. It quotes ARM 17, ARM 14 and ARM 6 immediately after instructing the reader
   not to quote numbers.
9. "One home per fact", and then it restates `v0.10.0`, making the file a
   version surface that no test pins; and the file carries no ledger ids, so
   `fact-health.sh` has nothing to check in the very file it is cited to
   defend.

**Treat this list as documented history, not as a work order.** At least one
entry in it has been measured false since it was written. Which one, and
whether there are others, is yours to establish.

## House conventions that apply to your finding, not to the file

1. **A claim without a falsifier is not a claim.** For each assertion the file
   makes, state the observation that would prove it wrong, then look for it.
2. **A gate that has not been MADE TO FAIL is not evidence.** Where the file
   says something is ENFORCED, find the thing that goes red and, where cheap
   and safe, make it go red. Restore byte-identically and prove it with
   `sha256sum`.
3. **Hunt fail-open first.** This repository has been bitten by an instrument
   that named nine sources and read four, by a `--record-baseline` that
   blessed a corpus it never read, and by a table row that un-administered its
   register in silence. A missing input must be LOUD.
4. **Measuring nothing is not passing.**
5. **A refusal writes no record**, so gates are invisible in the ledger. You
   cannot infer a gate fired from the absence of a violation.
6. **Read the whole thing before generalising from one row.** A previous
   session claimed a table named no arms, having grepped one row; 16 of 21
   named theirs.
7. **Look for the strongest counter-evidence to your own finding before
   reporting it.** Say which of your findings you could not reproduce with a
   command.
8. **Every number you report must come with the command that produces it,
   and the command must be one a later reader can run.** A measurement that
   lives only in your report cannot be checked against anything, and this
   repository has now watched one such number be wrong for a full round
   before the act of writing it down exposed the error. If you cannot give
   the command, say the figure is testimony and mark it so.

## Rules for your session

- **Do not modify the tracked working tree.** Probe in a copy under your own
  scratch directory.
- **Never run `git checkout <path>`, `git restore`, `git stash` or
  `git reset`.** Work here is uncommitted; those destroy it.
- **Never write to `.truth/claims.jsonl`**, and never stage it.
- If you must mutate a tracked file in place: `sha256sum` first, restore from
  your own copy, and prove the sha matches.
- Do not run `template/scripts/truth-canary.sh` or any release battery — they
  write git state.
- Finish with `git status --short` and confirm you changed nothing.

## What to produce

For each defect: one line stating what is FALSE, BROKEN or WORSE; the exact
command that reproduces it and its real output; severity; and whether it would
mislead an agent into doing the wrong thing. Rank by how well the defect hides
a regression.

Then a **Verified sound** section: what you checked and found correct, with
the commands, so a later reader knows the coverage and not only the failures.

Then state plainly whether this should be committed as it stands.

Be blunt. Every previous review in this repository found defects the previous
pass had cleared, in changes whose authors had demonstrated their own gates
going red and reported honestly. Self-demonstration is necessary and not
sufficient — that sentence is in ADR-062 because it was measured here twice.
