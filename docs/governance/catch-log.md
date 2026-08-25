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

---

## Mechanism census — cost side

Every instrument in this repository, and whether this log records it catching
anything. A blank column is not an accusation; it is an unanswered question,
and rule 4 says it is the only deletion criterion available here.

| instrument | catches recorded |
|---|---|
| `arm-index.py` | 1 |
| `register-index.py` | 1 |
| `waiver-index.py` | 1 |
| `blast-report.py` | — |
| `capsule-blindness.py` | — |
| `concern-tag.py` | — |
| `field-consumers.py` | — |
| `label-coupling.py` | — |
| `override-velocity.py` | — |
| `retraction-causes.py` | — |
| `semantic-audit.py` | — (appears in MISSES) |
| `separation-report.py` | — |
| `watch-derivation.py` | — |
| `doc-health.sh` | — |
| `truth-canary.sh` | — |
| review by an agent NOT given the spec | 3 |
| mutation of a gate (ADR-061) | 1 |
| git history as an oracle | 2 |
| operator-side reading | 1 |

---

## What the figures currently say

**Ten catches, nine misses, and the sample is far too small to conclude
anything.** That sentence is the honest reading and it should stay until the
log has run for months, not days.

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

## How to use this file

Add an entry the day it happens; a catch reconstructed a week later is
testimony, not evidence, and rule 5 will mark it so. Read the two tables
together, never separately. When the census shows a mechanism at zero after
a long enough run, that is the moment to ask what it is for — and the answer
"it guards something rare" is admissible exactly once, in writing, with the
rare event named.
