# Six open decisions, and one defect nobody decided to have

> Reader: an independent reviewer judging what the operator should decide, or the operator deciding it | Enables: ruling on six items that four agent sessions could not rule on themselves, each with the command that settles its facts | Update-trigger: any of the six is decided, or the ledger counts below move

## What this brief is, and how to read it

`main` was fast-forwarded to `328760c` on 2026-08-22 with all gates green.
Four sessions wrote handoff testimonies in `.local/session_*.md` and
cross-checked each other's claims before that fast-forward. **Six sessions
actually committed inside its range, and eleven appear across the last two
hundred commits.**

    git log --format='%(trailers:key=Claude-Session,valueonly)' 5578572..328760c \
      | sed 's|.*session_||' | grep -v '^$' | sort | uniq -c | sort -rn
    #  15 01KzvGV9bYeWvrtRx5cFLXAi      7 01HzSxqVKRdYhu8aSCK6B2bX
    #   6 01JdHzXYoKAdJjwJNuyMmhWn      5 013jva2WUTrMH9MrjV1N1wxB
    #   1 01XY21ifMt27PnLTf6pQKUBm      1 01JjeEbwTtWMT4dk4ZAS62pi
    ls .local/session_*.md | wc -l      # 4
    git log -200 --format='%(trailers:key=Claude-Session,valueonly)' \
      | sed 's|.*session_||' | grep -v '^$' | sort -u | wc -l    # 11

**State that limitation plainly: the reconciliation covered four of the six
writers in range.** Two committed and left no testimony, and one of them turns
out to matter — see §8. A seventh session, `01J7mceSv9FvXxv6wYsajX5d`,
introduced the naming form at the centre of that finding.

Note also that the trailer is not an authorship key: session
`013jva2WUTrMH9MrjV1N1wxB` disclaims `cc3aef0`, which carries its identifier.
What remains are six things no agent may decide — five because the ledger's
G12 rule or ADR-047 governance reserves them for a human, one because it is a
question about how work itself is organised — plus one measured defect that
needs a ruling rather than a decision.

**Verify, do not believe.** Every factual claim below carries the command that
settles it. This session was wrong at least five times in six days, each time
about something it had stated confidently:

| what I asserted | what was true |
|---|---|
| the battery's own gate had "six arms" (repeating `AGENTS.md`) | twelve; corrected in `bed0ab4` by another session |
| my session→commit map over-claimed a row | it did not; the window excluded the commit |
| the J-045 collision was a race between two sessions | one commit added both headers |
| `grep -cE '^# --- [0-9]+[.] [a-z]+'` counts the battery's arms | it undercounts by two; see §8 |
| a harness under `make test` would be cleaner than under the battery | it would cost minutes on every push |
| four sessions worked this repository | four wrote handoffs; six committed in range, eleven in 200 commits |
| the sessions that added `5b` and `8b` were among those four | `5b` came from a seventh session with no handoff |

Three of those five were caught by other sessions, not by me. Treat any
sentence here without a command in the next line as a hypothesis.

---

## 2. Does the ADR-047 gate registry cover battery arms?

**Decide:** whether `docs/governance/gate-metrics.md` is a registry of intake
gates and counted overrides, or of every blocking gate including the release
battery's arms. Tracked as `wk-5cbbc965`, which replaced a mis-framed
predecessor (see §3).

    grep -c '^| ' docs/governance/gate-metrics.md          # 15 = header + 14 gate rows
    grep -cE '^# --- [0-9]' scripts/release-battery.sh     # 13 battery arms
    grep -n label-coupling docs/governance/gate-metrics.md # the one battery arm with a row

Thirteen of the fourteen rows describe intake gates and overrides (G0, G8,
ADR-007, ADR-009/021/022, ADR-035/036/037/038/039, ADR-033, INV-M, G6). The
fourteenth is `label-coupling`, a battery arm, added retroactively in
`4760366` by the session that had shipped it without a row two days earlier.

That one row created an expectation the other twelve arms do not meet. The
issue it spawned originally blamed `field-consumers` for lacking a row; that
framing is wrong, because **no battery arm had a row until `4760366` invented
the precedent.**

**(a) The registry covers battery arms.** Twelve rows are missing. That is a
work programme, not an afterthought, and each row must state a metric and a
review date that someone will actually read.

**(b) The registry stays with intake gates and overrides.** Then
`label-coupling`'s row is the anomaly, and nothing is owed. The reviewer
should ask whether removing it would be honest or would look like retreat.

**Contested, and worth the reviewer's attention:** under either answer, a
registry that counts arms needs a *source for the count* that survives the
next naming convention. §8 shows the obvious grep does not. `wc -l
.truth/label-coupling-opt-out`, the metric that row already uses, does.

## 3. Kill `wk-1bbb48c2` by hand

**Decide:** nothing, really — this is an execution the machine refuses to do.

The mis-framed issue from §2 is still open. The session that filed it tried to
cancel it and was refused:

> issue cancellation is a human tombstone decision (G12) — file diverge saying
> it should die, and stop; the human queue decides

They did not route around it with `done --basis`, and said why: *"turning
should-die into is-done is laundering the judgement."* The reviewer may want
to note that as the behaviour the refusal message was designed to produce —
it is the counter-example to `wk-36066db9`, "stop refusal messages teaching
their own bypass."

## 4. The G12 retraction backlog

**Decide:** each of these, individually. Retraction is human-only and no agent
flag opens it.

    python3 template/scripts/truth list --json | python3 -c "import json,sys,collections; \
      print(collections.Counter(r['status'] for r in json.load(sys.stdin)).most_common())"
    # 2026-08-22: retracted 135, live 68, diverged 32, unverified 28

**Three pilot pairs, both halves live.** `tr-f9318142`→`tr-99d9b476`,
`tr-7c4966ad`→`tr-bc8bb5c8`, `tr-66b04399`→`tr-a3a63432`. Successors are
independently verified; predecessors were never retracted, so the ledger holds
three live duplicate pairs. Blocked on G12 since 2026-08-18.

**Ten orphaned `diverged` claims** naming `docs/adr/truth/`, a path that no
longer exists — they cannot be re-judged because their subject moved to
`docs/archive/adr/`. That is 10 of 32 diverged. Recipe already drafted at
`docs/refactor/00-RUNBOOK.md:182` (`--cause expired`). Tracked `wk-5cda9f1a`.

    python3 template/scripts/truth list --json | python3 -c "import json,sys; \
      print(sum(1 for r in json.load(sys.stdin) if r['status']=='diverged' and 'docs/adr/truth/' in r.get('text','')))"

**`tr-c5ff452c`** (diverged) and **`tr-599e7561`** (unverified). The second is
a sentinel over `.pi/extensions/truth-whisper.ts`, a file whose harness the
owner has said is unused. The claim and the file must die together or stay
together; killing one alone leaves either a sentinel over nothing or an
unwatched file.

**`tr-38d32bc7`** was diverged by this session on 2026-08-21 — see §8 for why
that judgement is more interesting than it looks. A successor should name the
battery's arm set *without a count literal* (genus `wk-97e27acf`).

## 5. ADR-055 and ADR-056 are PROPOSED and agent-authored

**Decide:** accept, reject, or leave pending. Both are in `docs/decisions/`,
the register this session re-founded on 2026-08-18 after the 54-ADR corpus was
moved to `docs/archive/adr/` and, as a side effect nobody decided, the practice
of writing decision records stopped.

    sed -n '1,20p' docs/decisions/055-*.md
    sed -n '1,20p' docs/decisions/056-*.md

**ADR-055** (churn floor refuses; structural selector targets exempt). Its own
author declines to accept it: ADR-039 made the advisory→refusal promotion
conditional on ≥30 days of forecast-versus-observed data, that data was never
produced, and refactor step 2.5 made "observed stalings" unmeasurable. The
gate is running without an accepted record.

**ADR-056** (shell-free evidence execution, implemented). Its author asks
explicitly that it stay PROPOSED: ADR-041 set two acceptance conditions, a
simulation (done, whole-corpus hash stability) and an **independent
adversarial pass** (not done). ADR-041 records that the previous patch in this
area passed 235 canary arms and was then broken three ways. A green suite is
not the evidence that record demands.

    python3 template/scripts/adr041-hash-stability.py .truth/claims.jsonl   # exit 0

**For the reviewer:** if you take one thing from this brief, consider taking
the adversarial pass on ADR-056. Its author names the target: the lexer
(`_lex_word`, `_evidence_lex` in `template/truthlib/evidence.py`), because
that is where the runner departs from `/bin/sh`. ADR-056 itself discloses that
R4a is *not* closed — glob expansion happens at run time, so `uniq *` still
delivers a write in positional position.

## 6. One worktree per agent, for editing

**Decide:** whether concurrent sessions edit in their own git worktrees, with
the main tree reserved for verification.

This is the only defence in `docs/refactor/01-JOURNAL.md` J-047 that converts
a norm into an impossibility rather than another reminder. `git add` takes
paths, and the unit of correctness is not a path; hunks carry no session
signature and never will. Three times in eleven minutes on 2026-08-18 one
session committed another's uncommitted work — tests without their
implementation, an ADR without its code, a journal entry that collided a
number. A rule was written two days later and has never been tested against a
live case.

    git log --format='%h %ad %s' --date=format:'%m-%d %H:%M' f53ee93 39e1052 7172d51

**Cost the reviewer should weigh:** `.venv/` is gitignored, so a fresh
worktree silently falls back to the system interpreter and the schema arm goes
quiet — the cure manufactures its own class of false signal. And verification
must stay in the main tree regardless: a canary run from a linked worktree
escaped its sandbox on 2026-08-20 and wrote to the shared `.git/config`,
unsetting `core.hooksPath` and stamping four commits with a test identity.

## 7. An arm selector for the battery harness

**Decide:** whether to fund it. Tracked `wk-38131acb`.

`AGENTS.md:126-132` requires "do not add an arm you have not seen fail". One
red-check currently costs a full harness run — roughly ten minutes of CPU and
twenty-two battery invocations — because arms cannot be run individually.

The consequence is already on the record. When the harness was restored in
`5968a5d`, arms 4, 5 and 15 were seen red in-session and arms 10, 11 and 12
had their red-capability verified by breaking the battery's guarantee; **arms
1-3, 6-9, 13 and 14 entered on the previous author's testimony, not this
session's verification.** That is disclosed in the file's header rather than
smuggled past the rule, but it is a nine-arm gap.

    sed -n '/RED-VERIFICATION STATUS/,/^set -u/p' scripts/test-release-battery.sh

A rule whose execution costs ten minutes is a rule nobody re-runs — J-047
class E, a norm without a mechanism.

---

## 8. The finding that is not a decision: a capsule went blind and stayed green

This one needs a ruling on what it implies, not a choice between options.

`tr-38d32bc7` asserted the release battery carries **TEN** numbered arms. Its
capsule:

    grep -oE '^# --- [0-9]+[.] [a-z]+' scripts/release-battery.sh

At the claim's anchor commit that recipe was **exact**. Eight hours later a
naming form its regex cannot see — `5b`, then `8b` — entered the file:

    for c in c0ff7f32 be0b4da d5d0259 4760366 328760c; do
      printf '%s capsule=%s actual=%s\n' "$c" \
        "$(git show ${c}:scripts/release-battery.sh | grep -cE '^# --- [0-9]+[.] [a-z]+')" \
        "$(git show ${c}:scripts/release-battery.sh | grep -cE '^# --- [0-9]')"
    done
    # c0ff7f32 capsule=10 actual=10     <- anchor, exact
    # be0b4da  capsule=10 actual=11     <- 5b lands; claim still green
    # d5d0259  capsule=10 actual=12     <- 8b lands; claim still green
    # 4760366  capsule=10 actual=12
    # 328760c  capsule=11 actual=13

**The claim reproduced green for four days while being false.** It broke only
because this session's new section is numbered `11.` with a dot — a form the
regex happens to match. Had it been named `10b.`, the claim would be green
today and still wrong.

This is a blind spot of reproduce-on-read itself, and `reproduce` cannot see
it by construction. A green capsule means *"my pattern still matches the same
subset"*, not *"the fact still holds"*. ADR-051's whole value rests on those
being the same sentence; here they were not, and nothing in the repository
noticed. Neither session that added `5b` or `8b` did anything wrong, and neither could
have known: `5b` arrived from `01J7mceSv9FvXxv6wYsajX5d` in `2822d8e`, a
session that left no handoff and had no reason to have read a capsule filed
eight hours earlier. The capsule was fail-**open** to forms invented after it.

    git log -1 --format='%h %ad %(trailers:key=Claude-Session,valueonly)' \
      --date=format:'%m-%d %H:%M' 2822d8e

The session whose `5b` first widened the blind spot put the consequence better
than this brief had: detection here depended on a naming choice made by
someone who did not know the capsule existed. **That is not a gate; it is a
lottery.**

**Questions for the reviewer, in descending order of how much they matter:**

1. How many other live claims carry a pattern-matching capsule whose coverage
   can silently shrink? A `grep -c`, `grep -oE`, `sed -n '/x/p'` or `ls | wc -l`
   recipe all share this shape. The population is measurable today.
2. Should a capsule that COUNTS be refused at intake, the way `wk-97e27acf`
   proposes refusing count literals in claim *sentences*? The sentence and the
   recipe failed together here, which suggests one rule, not two.
3. Is there a cheap fail-**closed** form? A recipe that greps a pattern could
   also assert the pattern's complement is empty — here,
   `grep -E '^# --- [0-9]' | grep -vE '^# --- [0-9]+[.] [a-z]+'` returning
   nothing. That converts an unseen form from silence into a failure.
4. `retracted-figures` was built to catch stale numbers in prose. Does the
   analogous instrument for stale numbers *in capsules* already have a home, or
   is it a new Tier C instrument?

---

## Summary

| # | item | who must decide | blocked work |
|---|---|---|---|
| 2 | scope of the ADR-047 registry | operator | `wk-34a7bbde`, the tier-boundary pin |
| 3 | kill `wk-1bbb48c2` | operator (G12) | tidiness only |
| 4 | retraction backlog | operator (G12) | three live duplicate pairs, 10 unjudgeable claims |
| 5 | ADR-055, ADR-056 | operator, ideally after an adversarial pass | two gates running without accepted records |
| 6 | worktree per agent | operator | nothing blocked; three incidents already paid for |
| 7 | arm selector | operator | nine arms credited on second-hand evidence |
| 8 | capsule blindness | reviewer's ruling | unknown population of claims |

Item 8 is the one this session would put first. Items 2-7 are debts that are
named and bounded. Item 8 is a defect in the mechanism that decides whether
anything else here is true, and its population has not been measured.
