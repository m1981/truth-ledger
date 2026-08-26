# Catch log

## Why this file exists, and why it is here and not in `.truth/`

The ledger answers one question: does a written sentence still correspond to
the repository it describes. Paper §0 places it BELOW the 12207 baseline on
purpose. It therefore cannot answer whether the apparatus is worth its cost —
that is a validation question, and asking it of the ledger will always return
silence, no matter how green the run.

This file is the operator's instrument, not the agent's. It records the only
figure that answers the question: **how often did a mechanism stop something
that would otherwise have reached a consumer, and how often did it fail to.**

It has no gate, no baseline and no instrument. It is read by a person.

## What this log cannot tell you

* Not whether the system is *correct* — that is what everything else measures.
* Not whether a catch was *important*. There is no severity scale here on
  purpose; each entry says in plain words what would have shipped, and the
  reader judges. A scale would invite fitting the number to the feeling.
* Not causation. A defect caught late might have been caught anyway.

## Rules

1. **Entries are never deleted.** A catch by a mechanism since removed still
   happened. This file is history, not state; the mirror rule that governs
   `.truth/` baselines does NOT apply here and must not be imported.
2. **Misses are mandatory.** A log that records only catches is confirmation
   bias with a filename: the rate is the point, and a rate needs a
   denominator. If adding a catch, look for the miss that preceded it.
3. **A catch by review is a miss by instrument.** When a human or a reviewing
   agent found what a gate should have found, it goes in BOTH tables. This is
   the commonest and most informative entry shape.
4. **Zero-catch mechanisms are listed.** A mechanism that has caught nothing
   is a cost with no measured return. That is not proof it is useless — it may
   guard a rare event — but after long enough it is the only deletion
   criterion this repository has.
5. **Provenance per entry.** `cmd` = reproducible now. `hist` = in git or the
   ledger. `test` = session testimony only, not independently reproducible.
   Testimony is admissible and marked, never laundered into evidence.

---

## CATCHES — a mechanism stopped it

| date | what would have reached a consumer | caught by | prov |
|---|---|---|---|
| 2026-08-24 | `arm-index` matcher read `Tier C` as arm `C`, captured `FAUL` from `SD-decay`, and missed backticked `` `FAULT B` `` — the arm census would have been wrong in three directions at once | `instruments/arm-index.py` on itself | test |
| 2026-08-24 | a waiver register omitting `--refresh-evidence`, a sentence-bearing override lifting a hard ADR-051 refusal, extracted by the very instrument being edited | adversarial reviewer NOT given the spec (ADR-062 r.1) | test |
| 2026-08-24 | eleven checks in the register-index suite were deletable with the suite still green — including the trailing-pipe check that was the block parser's entire justification | mutation of the suite's own gate (ADR-061) | test |
| 2026-08-24 | `--record-baseline` blessed a 42-entry backlog it had never read, when the measure was suspended — a fail-open in the baseline mechanism itself | adversarial reviewer | test |
| 2026-08-24 | a "defect" that did not exist: the claim that the AGENTS.md redraft dropped three ledger ids. The file had never carried one in thirty revisions. Fixing it would have invented content | `git log` over the file's history | hist |
| 2026-08-24 | a paragraph stating no guard exists on `mkrepo()`, when `441de48` added one on 2026-08-21 — the only PESSIMISTIC falsehood found in that file | agent re-measurement against git | hist |
| 2026-08-25 | `docs/waivers.md:79` claims `--accept-unsafe-ok` writes `accept.screened` AND `accept.executed`. The ledger shows 5 and 2, the second a proper subset of the first, split by entity kind. An L2 reader sizing that escape by `accept.executed` undercounts by 60% | `instruments/waiver-index.py` printed both populations adjacently; the contradiction was visible in its own output | cmd |
| 2026-08-25 | ADR-062 filed as a decision and named in the plan in no tense | `python3 instruments/register-index.py` → exit 1 | cmd |
| 2026-08-25 | a finding of mine that was false: I predicted a fail-open in the `options:` reader of `waiver-index.py`. The usage↔options cross-check refutes it. Reporting it would have cost an agent a day repairing a sound mechanism | reading the code for the falsifier before reporting | cmd |
| 2026-08-25 | three reasons in `.truth/waiver-not-an-override` truncated mid-clause at exactly 74 characters (`--basis`, `--watch-policy`, `--ttl-days`), in a file whose header declares a reason mandatory | operator-side review — see the matching MISS below | cmd |
| 2026-08-25 | **`TAG_CHECK_VERSION` overrides the version the pre-push tag check inspects**, and it was recorded in `.truth/waiver-not-an-override` as "a local shell variable … not an inherited one". It is assigned nowhere in `.githooks/pre-push`. The register has held `tr-b1472ca1` since **2026-07-14** — live, and stating the gate "FAILs when the tag's tree states a different version" — while the variable that chooses that version was introduced by `64a7605`, the SAME commit the claim pins. A month of a live claim about a gate, and its escape registered nowhere | adversarial reviewer NOT given the spec (ADR-062 r.1) | cmd |
| 2026-08-25 | the `admitted on` column was checked only for `flag` rows — the check sat below the return that skips every other carrier — so 21 of 32 rows could hold arbitrary prose while `docs/waivers.md` said the column "is checked against the parser". The summary line then counted those rows in neither bucket and still announced the full total: 13+5+13 printed as 32 | adversarial reviewer | cmd |
| 2026-08-25 | the environment harvest MISSED `NAME="${NAME:-default}"` — the commonest bash way to read an inherited variable, and the idiom this repository's own scripts use — while `docs/waivers.md` claimed the shell half "over-reports rather than under-reports". Two more misses in the same reader: the CLI entry point `scripts/truth` is Python with no suffix, and hook files were listed by name rather than read | adversarial reviewer | cmd |
| 2026-08-25 | six entries the author had just added to `.truth/waiver-not-an-override` declared environment names that no source actually reads — an over-classification that would have excused six things that do not exist | `instruments/waiver-index.py` mirror rule, on its own author, in the same session | cmd |
| 2026-08-25 | **an INVERTED ARM.** `assertEqual(local.returncode, 0, "a shell local was reported as inherited")` pinned the miss of `NAME="${NAME:-}"` — the commonest bash read idiom, the one this repository's own scripts use — as the DESIRED behaviour. Not a missing gate and not an empty one: a gate certifying a defect, which converts a hole into a requirement and makes the next reader argue with a passing test | operator, from the assertion's own wording: the message described an observation ("was reported as") where a requirement would read "an inherited variable must not be classified as local" | cmd |
| 2026-08-25 | `NOT COUNTABLE` asserted over 209 trivially countable standing excusals, and over `--ttl-days`, whose "no presence test separates it" was one line of predicate away from false — the real population is **2**. Over-suppression reads as humility and hides a number: the mirror of the correctly-made decision that a WRONG population is worse than none | adversarial reviewer | cmd |
| 2026-08-25 | a probe reported STILL GREEN and the FIXTURE was why, twice: a `--ttl-days` stamp cell with no backticked field could not express the defect, and a negation mutation swapped WHICH record was counted while the count stayed 1. An arm asserting a number cannot see an identity swap | writing the mutation and disbelieving the green | cmd |
| 2026-08-25 | the two-marker resolution: one marker made the index row fire on ITSELF, because `docs/registers.md` names the marker in a row about another file. A declaration must be about its own file to be one — use versus mention, object language versus metalanguage. Discovered empirically, by a gate shooting at itself | the gate, on its own index row, on first run | cmd |
| 2026-08-26 | **a measurement reported to the operator as 61 was 47.** The range that produced it swept in pre-existing tests around the arms it meant to audit. It had already been reported and acted on for a full round. Writing it to disk is what exposed it: the act of stating it where a later reader could check it forced the range to be named, and the range was wrong | persisting a measurement to disk (ADR-062 r.4), and the operator's `grep -rc permissive` returning 0 against the record that should have held it | cmd |
| 2026-08-26 | a new environment carrier `TRUTH_BATTERY_PLAN` added to `scripts/release-battery.sh` and classified nowhere. It exits the battery before the first check, so a push under it verifies nothing — the `--single-run` shape: lifts everything, on nothing, leaving no record. Caught minutes after it was written, before any reviewer started | `python3 instruments/waiver-index.py` → exit 1, naming the carrier and both places it could be declared | cmd |
| 2026-08-26 | two live claims asserting pre-ADR-057 semantics: `tr-56a8e36c` (the ADR-019 canary arm ADR-057 replaced) and `tr-d0191e65` (a clock-reader phrase `template/truthlib/policy.py` no longer contains, the arm having moved to `kernel.ttl_expiry`). Both had been false for two weeks with every instrument green | `python3 template/scripts/truth reproduce` → exit 7; the battery surfaced it at the push boundary | cmd |
| 2026-08-26 | seven defects in a 45-line change its author had declared green, gate-proven red in both directions and byte-identically restored. Four of them (D1–D4) were one cause: a completeness gate that models only part of the decision it claims to cover. The change was withdrawn, not patched | a reviewer given the diff, the tree and the house conventions, and NOT given the brief, the author's account, or any measurement — `docs/reviews/plan-mode-review-2026-08-26.md` | hist |
| 2026-08-26 | **`arm-index --record-links` froze a census computed from sources it could not read.** With one SOURCES entry hidden, the ordinary run raised two failures and the refresh printed `recorded 36 link and 221 prose hash(es)` at exit 0 — one link FEWER than the file it overwrote, the unreadable source's arms having silently vanished. The failure list was computed and never printed, because the early return preceded it: the `--record-baseline` shape, one instrument over | an independent audit of the transcript, which recovered the suspicion from the session's first answer; then a demonstration — hide the source, run the flag, watch it write | cmd |

## MISSES — it reached the operator, or lived, despite the apparatus

| date | what got through | which mechanism should have held it | prov |
|---|---|---|---|
| 2026-08-23 → 08-24 | ADR-059's central premise — "every override in this system is admitted on a sentence" — was false for four of ten flags, and stood for a day in a normative record | none existed: no register held the list of override flags. This is the miss that produced `docs/waivers.md` | hist |
| 2026-08-24 | `instruments/semantic-audit.py` and ADR-059 enumerated 5 of 8 override flags. The split was mechanical — the extractor walks payload fields and a bare boolean leaves no field to walk to — so the list could never have been completed by diligence | a list with no two-way sweep against the parser | cmd |
| 2026-08-24 | the first correction to that list said "FIVE of the eight" above a list of six — the count fitted to the list, one paragraph after describing that exact failure | nothing checks a count against the list beside it | hist |
| 2026-08-25 | reasons truncated at 74 chars pass `waiver-index`, which tests non-empty, not well-formed. The instrument does to its own input what ADR-059 says every gate here does: checks a sentence EXISTS, never that it MEANS anything | `instruments/waiver-index.py` `unreasoned` check | cmd |
| 2026-08-25 | `--ttl-days` sits on the not-an-override side while its own recorded reason says "a large value is ADR-032's visible opt-out". The row argues against its bucket | no mechanism can catch this: a partition tests placement, never correctness. Structural, not a defect to repair | cmd |
| 2026-08-25 | 42 of 43 entries in `.truth/register-index-baseline` carry an identical "reason" that restates the finding. The reason field carries zero information | the mirror rule governs whether an entry is stale; nothing governs whether a reason is a reason | cmd |
| 2026-08-24 | deleting a single trailing `\|` removed an entire register from administration with zero new failures — one layer above the malformed-row case that had just been hardened | the row-level parser. Fixing an instance did not fix the class | test |
| 2026-08-24 | an agent cited "the 2026-08-24 audit of this file" which existed only in a task notification and nowhere on disk — a phantom citation. Produced ADR-062 rule 4 | nothing verified that a cited measurement was persisted before the next role was dispatched | hist |
| earlier | a session claimed Appendix A's Gate column named no arms, generalising from the single row it had grepped. 16 of 21 rows name theirs | nothing requires a finding to state how many instances it examined | hist |
| 2026-08-25 | **an arm ASSERTED the fail-open as the desired behaviour.** `test_waiver_index_harvests_every_carrier_it_claims_to` contained `assertEqual(local.returncode, 0, "a shell local was reported as inherited")` — pinning the miss of `NAME="${NAME:-}"` as correct. A gate certifying a defect is worse than no gate: it converts a hole into a requirement, and the next reader must argue with a passing test | the arm itself. Nothing distinguishes an arm that proves a behaviour from one that freezes a bug, and writing both is the same act | cmd |
| 2026-08-25 | the `admitted on` vocabulary check EXISTED and was correct; it was placed below a `continue`. The defect was not a missing check but a check in the wrong position, which no coverage measure can see — the line is executed on every run, for a subset nobody declared | nothing tests that a check applies to the domain its own documentation claims. The file said "checked against the parser"; the code said "checked, for flags" | cmd |
| 2026-08-25 | `instruments/map.py` and `docs/map.txt` appeared in the working tree and **no session can be identified as their author**. Untracked, never committed, unknown to the ledger, naming no author and no session; git offers only an mtime. In a repository whose subject is knowing where a fact came from, an instrument of unknown provenance is a hole in the thing itself | nothing. `git log`, `git status` and the ledger were all asked and none can answer; provenance here is establishable only by testimony | hist |
| 2026-08-25 | the universal scope claim survived in `docs/registers.md` after being retracted in `docs/waivers.md` — the index kept "every gate that can be lifted" while the register it points at had already given it up. A limit repaired in one place and left standing one hop away, where `register-index` reported OK | nothing compared an index row's description against the register's own self-limitation. Now gated, both directions | cmd |
| 2026-08-25 → 08-26 | that same number lived a full round in a chat message and nowhere else, and it was **wrong while it was being cited**. ADR-062 rule 4 was written IN THIS SESSION, after a phantom citation in `AGENTS.md`, and was broken again by its own author one layer further out. The lesson is not "persist more": an unpersisted measurement is not merely unverifiable, it decays before anyone can check it, and this one was wrong in exactly the way a written record exposes — a silently over-wide range | nothing checks that a number quoted in a report exists in the record the report cites. Rule 4 says to persist; nothing reads back | hist |
| 2026-08-26 | a timing measurement whose stage function used `eval` without a subshell, so a `cd` inside one stage leaked into every later one. Three stages reported **0s** — failed starts read as results. The author had written the L0 rule ("did I measure the world, or my own apparatus?") into `docs/governance/architects-crib.md` hours earlier | nothing: no gate covers a measurement written in a scratch file. Marked `test` on the day it happened, which is what rule 5 is for — provenance tracks reproducibility, not recency | test |
| 2026-08-26 | ADR-057 changed what `stale` means, replaced a canary arm and moved the clock reader, and **nothing connected the decision to the claims that depended on it**. Suspect links hash prose citations; no mechanism runs decision → dependent claims. `reproduce` caught the consequence, two weeks and one push boundary late | the direction does not exist. Structural, not a defect to repair: an instance is repaired by judging two claims, the class needs a link type nobody has built | cmd |
| 2026-08-26 | the author added `GUARDS=$(grep -cE '^(if|elif) touches "\$' "$0")` as a completeness gate — **a roster inside a guard against rosters**, recognising one guard spelling out of four. The evading form is the style both guards used at HEAD one commit earlier. Over the SAME file whose `grep -oE` section counter reported 10 arms against 12 and produced operator RULING 8 | nothing in the tree enforces the spelling. Verified by injecting a literal-style guard: the plan still prints "every other stage is unconditional" at exit 0 | cmd |
| 2026-08-26 | `instruments/capsule-blindness.py` exists precisely for "a capsule that enumerates by pattern counts what it recognises, not what exists" — and could not have caught the above, because `capsule-blindness.py:75` reads `.truth/claims.jsonl` only. A pattern counter living in a shell script is outside its domain | the instrument's domain is the ledger; the class is wider than the instrument. Structural — an instance is repaired by rewriting one counter, the class needs the instrument to reach code | cmd |
| 2026-08-26 | `bash scripts/test-release-battery.sh 2` dies with `line 262: CANARY_STUB: unbound variable` — the stub is defined inside `if want 1`, so no arm after the first can be exercised alone. Pre-existing; it made both the reviewer's and the dispatcher's per-arm measurements incomplete | no gate covers the suite's own arm-selection wiring; the suite is only ever run whole | cmd |
| 2026-08-26 | that defect was **suspected in the session's first answer**, stated as "nobody but me knows this, so I am saying it plainly", and then evaporated for the whole session — one of seven escalations the audit found with no repository trace. It was real, and it sat unchecked for forty-odd answers while everything around it was being hardened | nothing carried it. `Otwarte` did not exist yet, and when it did its recall was ~45% against an independently compiled list. This is the instance that turns that statistic into a defect | hist |

---

## Mechanism census — cost side

Every instrument in this repository, and whether this log records it catching
anything. A blank column is not an accusation; it is an unanswered question,
and rule 4 says it is the only deletion criterion available here.

**Second column, added 2026-08-26: is this thing in the catching business at
all?** Without it a zero says nothing, and rule 4's deletion criterion is
blind — an extractor that has caught nothing has done exactly its job. Each
classification is taken from the instrument's own opening docstring, not
assigned by judgement:

* **detector** — it asks a question that can FAIL. A long-standing zero here
  is a real signal and rule 4 applies.
* **reporter** — it emits a measurement for a person to read. It cannot
  catch, so its zero carries no information and rule 4 must never be aimed
  at it.
* **gate** — it refuses. Its zero in THIS log means the log does not record
  its refusals, not that none happened; a refusal writes no record, which is
  the standing blindness this repository already knows about.

| instrument | catches recorded | in the catching business? |
|---|---|---|
| `arm-index.py` | 1 | detector · "which arm guards what?" |
| independent audit of the transcript | 1 | practice, not an instrument |
| `register-index.py` | 1 | detector · "is the index of registers itself administered?" |
| `waiver-index.py` | 3 | detector · "is the list of ways to bypass a gate itself administered?" |
| `map.py` | — (provenance unknown; see MISSES) | reporter · "one line per navigable artifact, so an agent greps instead of reads" |
| `blast-report.py` | — | reporter · the ADR-039 churn report |
| `capsule-blindness.py` | — | detector · commissioned for the fail-open capsule class (RULING 8) |
| `concern-tag.py` | — | reporter · its docstring says READER |
| `field-consumers.py` | — | detector · "does every payload field have a READER?" |
| `label-coupling.py` | — | detector · "which modules share decisions without sharing code?" |
| `override-velocity.py` | — | reporter · the ADR-033 override report |
| `retraction-causes.py` | — | reporter · ADR-049's adoption metric |
| `semantic-audit.py` | — (appears in MISSES) | reporter · its docstring says EXTRACTOR |
| `separation-report.py` | — | reporter · the ADR-010 separation evidence |
| `watch-derivation.py` | — | detector · "does a claim watch what its recipe reads?" |
| `doc-health.sh` | — | gate · refuses; refusals are not logged here |
| `truth-canary.sh` | — | gate · catches seeded faults every run; not logged here |
| `truth reproduce` (the push-boundary sweep) | 1 | gate · refused a push this very session |
| review by an agent NOT given the spec | 8 | practice, not an instrument |
| mutation of a gate (ADR-061) | 2 | practice, not an instrument |
| git history as an oracle | 2 | practice, not an instrument |
| operator-side reading | 3 | practice, not an instrument |
| persisting a measurement to disk (ADR-062 r.4) | 1 | practice, not an instrument |

---

## What the figures currently say

**Twenty-three catches, twenty misses, and the sample is still far too small to
conclude anything.** That sentence is the honest reading and it should stay
until the log has run for months, not days.

Three patterns are visible and each is a hypothesis to be tested by further
entries, not a result:

1. **The highest-yielding mechanism in this table is not an instrument.**
   Review by an agent deliberately not given the specification accounts for
   three catches; no single instrument accounts for more than one. If that
   holds at thirty entries, the cheapest available improvement is more
   role separation, not more code.

2. **Every recorded miss is a judgement about CONTENT; every recorded catch
   is about STRUCTURE.** Instruments here reliably establish that a thing
   exists, is enumerated, is reachable, is hashed. Not one has ever
   established that a sentence means what it says. The apparatus has a
   ceiling and the misses sit exactly on it.

3. **Two misses are marked structural** — `--ttl-days` and the empty reason
   fields. Neither can be repaired by adding a case, because both are
   failures of a partition to judge the contents of its own cells. That is
   a shape problem, and the shape is currently correct for what it can do.

4. **The census reads very differently now that it says what each thing is
   FOR.** Of the fourteen instruments, **seven are detectors and seven are
   reporters** — and a reporter that has caught nothing has done its job
   exactly. So the figure is not "three of fifteen have caught something";
   it is **three of the seven that were ever in the catching business**, with
   `capsule-blindness`, `field-consumers`, `label-coupling` and
   `watch-derivation` the four detectors still silent. That is the set rule 4
   may be aimed at, and it is half the size the bare column suggested. The
   earlier framing was not wrong about the numbers; it was wrong about the
   population, which is the failure this repository produces at every level.

## How to use this file

Add an entry the day it happens; a catch reconstructed a week later is
testimony, not evidence, and rule 5 will mark it so. Read the two tables
together, never separately. When the census shows a mechanism at zero after
a long enough run, that is the moment to ask what it is for — and the answer
"it guards something rare" is admissible exactly once, in writing, with the
rare event named.
