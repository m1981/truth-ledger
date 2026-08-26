# ADR-063: An answer's findings terminate, or the answer is not finished

Status: **PROPOSED** (2026-08-26, agent-authored, from one session's measured
experience). The operational form belongs in `AGENTS.md`; this record carries
the decision and its falsifier. **Not gateable inside this repository** — see
*Rejected*.

Cites: ADR-042 (rule 2 — measuring nothing has not passed), ADR-061 (DONE
requires a gate that can go red), ADR-062 (roles are separated by what each is
not told — this is its sibling: what each must say when it reports).

## Context

An operator complaint — answers carry many observations and close on one —
was measured rather than accepted. An independent auditor, not given the
figures, hand-classified all 51 substantive answers of the 2026-08-26 session
against a definition it stated before counting and calibrated by re-scoring a
random sample (drift +0.9 pp on the aggregate rate).

| | |
|---|---|
| findings raised | **374** |
| terminated in the same answer | **307** |
| rate | **0.821** (median 1.00, bimodal, min 0.00) |

Termination *does* scale with findings raised — `terminated = -0.26 + 0.856 ×
raised`, r=0.80 — so the naive reading was wrong, and so was the assistant's
own first measurement: it reported 718 / 0.7 / 31% by a bold-span proxy that
**does not replicate** (the same method re-run gives 1062 / 1.06 / 43%) and
whose correlation with hand-counted terminations is 0.235.

The defect is real but **localised by answer genre**:

| stratum | n | rate | median |
|---|---|---|---|
| work / review | 41 | 0.914 | 1.00 |
| **expository / advisory** | 10 | **0.423** | **0.33** |

**61% of all orphaned findings live in 20% of the answers**, and the
expository intercept is −2.2: the first two findings of an explanatory answer
are structurally guaranteed to be orphaned. The convention therefore matters
most where it was least applied — when explaining, not when working.

Sixteen escalations to the operator were traced. Nine resolved. **Seven
disappeared with no repository trace**, including a suspected fail-open in
`arm-index --record-links` raised in the session's first answer and never
mentioned again. The assistant's own carry-forward section recovered one item
that had been absent for sixteen consecutive answers — and had **recall ≈45%**
against the auditor's independently compiled list, because it was a
hand-maintained roster: the failure class this repository has been defeated by
four times.

## Decision

Five sections: **Odpowiedź** (the verdict, before the evidence) · **Dowód**
(only what carries it) · **Co z tego wynika** (the implication, not the
observation) · **Domknięcie** (the table) · **Otwarte** (escalations carried
forward). Eight rules, each earned. (Five were written first; 6 and 7 were
added when the operator asked for addressable rows and a closing
recommendation, 8 when he asked what moves the work while the assistant has
none to do. **This line has now been wrong three times in one day** -- five
when there were seven, seven when there were eight -- each time corrected only
because somebody counted, and each time in the paragraph directly above the
rule about counted assertions. Three occurrences in one file in one day is
not a lapse of care; it is the argument that a hand-kept count in prose is
unmaintainable, and it is mechanically checkable without reading any meaning:
the number in this sentence against `grep -c "^[0-9]\. \*\*"` over the same
file. That check does not exist. It is the cheapest concrete instance of what
`wk-1fc6ab40` proposes.)

1. **Every finding raised in the body terminates in exactly one of three:
   `robię`, `Twoja decyzja`, `odpuszczam — z powodem`. Unclassified: zero.**
   `Twoja decyzja` is not one bucket but three, and collapsing them hides the
   only thing the operator needs in order to schedule: **a RULING** is a
   binary choice with something already waiting on it and costs a sentence;
   **a JUDGEMENT** costs thought and no working tree, so it can be answered
   at any time from anywhere; **a SPECIFICATION** changes a mechanism and
   costs a whole session, so it cannot be answered between other things and
   must be REFERRED rather than deferred. Three orders of magnitude under one
   label mean the label carries no cost information at all. Name the kind.

   **The domain is findings HANDED IN as well as findings raised.** A review,
   an audit or another agent's report arrives as a list, and reading it is not
   terminating it: an item nobody transcribes enters no partition and is
   counted by nothing. So a list received from elsewhere is **transcribed into
   `Domknięcie` item by item before any of it is acted on** -- one row per
   item, including the ones already handled, because the row is what makes an
   omission visible.

   Earned the same day the rest of this record was: a review returning nine
   findings plus one filed off-scope was read, five were repaired, and the
   commit message prepared for it said "five false assertions fixed" as though
   that were the whole of it. The remaining four were real and cheap -- four
   sentence edits, made within the hour once the list was walked. Nothing
   caught the gap; the operator pasting the full report caught it.

   That is rule 1's own partition mis-scoped, which is the failure this
   repository has now produced at four different levels: **total over the
   findings I raise, and read as total over findings.**
   A partition, not a search — the move this repository has made against every
   roster it has lost to. Its side effect is the point: *a finding not worth
   terminating is not worth raising*, which cures the ratio at source where an
   instruction to be brief does not.

2. **Provenance per finding — `cmd` / `hist` / `wnioskowanie`.** Earned three
   times in one session, each time by an inference wearing the clothes of a
   measurement: a sortal read where the split was by verb, a predicted
   fail-open a cross-check already covered, and a constant number read as
   staleness where it was blindness.

   **A `cmd` mark says a measurement was taken. It does not say the source
   was the right one for the claim's domain, and that is the harder half.**
   Same session, twice more, both times AFTER checking something:

   * A behavioural claim about a CLI flag — repeated three answers running,
     marked as fact — was compressed out of a register entry that carried the
     qualifier ("a **stored** oracle") the claim needed. The source was read;
     one word was dropped.
   * A claim that a hook's stdin contract omits a field, marked `cmd`, was
     read off an example given for **tool events** and taken as the universal
     contract. Both halves were false: the field is documented, and a second
     field made it unnecessary anyway.

   So the mark carries a second obligation: **name the source, and be able to
   say why that source governs this claim's domain.** One instance is not the
   domain — the failure this repository produces at every level, and the one
   provenance alone does not catch, because the measurement genuinely
   happened.

   Practically: where the source is a document, cite the file or URL beside
   the mark; where it is a command, cite the command. A `cmd` mark that
   cannot name what it read is `wnioskowanie` wearing better clothes.

3. **A warrant is required on every finding marked `wnioskowanie`** — one
   line: on what licence these data yield this claim. All three errors above
   were **warrant failures, not data failures**: the data were right and the
   inference licence was never examined. Backing only where the warrant is
   contested, or where a warrant of the same shape has already failed.
   Measured findings need none — the provenance mark already partitions the
   set, so the requirement lands exactly where the failures were.

4. **Every `robię` carries a defeat condition** — what would make abandoning
   it correct. ADR-061 turned on the assistant's own output.

5. **Every escalation persists in `Otwarte` until resolved, and carries what
   blocks it.** Order is derived from the blocking graph, never re-typed:
   a hand-ordered list is the same roster as a hand-maintained one. Seven
   escalations evaporated; ordering, stated in prose four times, evaporated
   with them.

6. **Every row in `Domknięcie` and `Otwarte` carries a local enumerator,
   prefixed by section — `D1..Dn`, `O1..On`, scoped to the one answer.** The
   operator answers by address instead of by quotation. Two sections numbered
   independently collide on a bare digit, hence the prefix. The enumerator is
   a convenience address and expires with the answer; where an item has a
   `wk-` id that id is the durable one and is carried beside the number.
   **An open item with no `wk-` has only the local number and dies with the
   answer** — the enumerator therefore shows, for free, what has not been
   anchored.

7. **The answer closes on a recommendation: the unblocked frontier, ordered,
   each with why it is next.** Approved en bloc by one word; a reservation
   removes one item by its address. The order is **derived** from the
   blocking graph, never chosen — a chosen order is the same roster as a
   maintained one. Two guards. **No item may appear for the first time in the
   recommendation**: it must already stand in `Domknięcie` or `Otwarte` of the
   same answer, because a standing one-word approval is an incentive to widen
   the batch, and a subset rule is the only cheap check on it. That is rule 1
   run backwards — no finding without a terminus, and now no action without a
   finding. And when nothing is unblocked, the section says so in one line
   rather than inventing a move.
   **Every recommended item names who EXECUTES it and who APPROVES it.** The
   subset guard above checks an item's PROVENANCE; nothing in it checks
   AGENCY, and that gap is not theoretical: the first recommendation written
   under this rule proposed three items of which two were the operator's
   alone (a commit -- ADR-062 rule 2 -- and a dispatch that must not
   originate in the answering session) and the third needed an
   `--accept-unsafe-ok`, which lifts a screen and is therefore an operator
   act. All three were offered under one word of approval. A one-word
   approval over a batch with unnamed actors approves the assistant's reading
   of who may do what, which is exactly the authority ADR-062 rule 2
   withholds.

8. **When the frontier holds nothing the assistant may execute, the answer
   does STAFF WORK on the cheapest pending decision and PUTS ONE QUESTION.**
   The process must move without the assistant's labour, and there are two
   ways an organ with no authority does that. **Completed staff work**: every
   option is drafted in full -- the actual sentence that would go in the
   actual file -- so the ruling costs a word rather than an afternoon of
   research. Its own test travels with it: *would I sign what I prepared, if
   the decision were mine?* If not, the staff work is not complete and must
   not be presented. **Putting the question** (Robert's Rules): the duty to
   call a question belongs to the one running the business, not to the one
   deciding it. Business does not drift because nobody asked; it drifts
   because nobody put it.

   **One question, never a menu.** A menu of three pending rulings is the
   mechanism of stall: each looks like it needs thought, so none gets any.
   Which one to put is chosen by AGE, which the work kernel already records
   in every item's `ts` -- no new mechanism, the kanban answer that aging is
   the signal.

   **Explicitly NOT a silence procedure.** A default that takes effect on a
   deadline is legitimate for the assistant's own procedural choices and
   never for anything that changes the repository: adopting-unless-objected
   transfers the decision to the passage of time, and ADR-062 rule 2 reserves
   it for the operator with no exception for a clock.

   Earned 2026-08-26: a ruling worth one letter (`register-index` red on
   `adr-unaccounted:ADR-063`, resolvable by a roadmap line or a baseline
   entry) was recited as "your decision" in three consecutive answers and
   moved on none of them. It was settled in one exchange the moment both
   options were drafted and a single question was put.

**Scheduling.** The answer to "when will there be room for this" is a
**limit, not a date**: at most one SPECIFICATION-sized item in flight at a
time, and the rest are ordered by the blocking graph. Every date offered from
memory in the session this record came from turned out to be unreproducible;
a limit is checkable at the moment it is checked.

**The limit governs EXECUTION, never RECORDING.** Filing an item is not
starting it; it is giving it an address. Conflating the two left three
specifications homeless for a whole session -- they lived in a table that dies
with the answer, while the work kernel that exists to hold them stood ready.
What was lost was not the direction, which is a sentence, but the **dead
ends**: that one hook event cannot block at all, that the obvious cheap test
would have passed all three violations it was meant to catch, that an oracle
was satisfied two days before its own issue was filed. An implementer without
those repeats every one of them. So the rationale goes in the item's `--text`,
where it is the implementer's brief -- the cheap form of what design-rationale
capture (gIBIS, QOC) exists to preserve, and what an ADR's *Rejected* section
holds once a decision has been made.

**Negative rule.** A one-sentence answer skips the skeleton entirely. Four
headers over one sentence is theatre — the same failure this repository names
for an assurance case that acquires a diagram before it acquires defeat
conditions.

## Lineage

Rules 1–4 restate, for one answer, what this repository already does for a set
of records: a partition with no unclassified remainder, provenance per datum,
and a defeat condition on anything asserted. Rules 6 and 7 are older and come
from outside. **Pinpoint citation** — legislation is numbered so a reader can
answer "s. 3(2)(b)", and ISO/IEC/IEEE 29148 makes identifiability a quality
characteristic of a requirement because traceability is impossible without a
stable address. **Audit finding numbering** (IIA, GAO) is the closest relative
of all: *Finding 3 · Recommendation 3.1 · Management response to 3.1* is
exactly `Domknięcie` answered by address. Rule 7 is a **consent agenda** — a
body adopts a batch in one act and any member removes an item by naming it —
with the **silence procedure** of NATO/EU council practice as its sibling:
adopted unless an objection is raised. The obligatory closing recommendation
is SBAR's R and the staff study's final section, where the approving authority
signs against it.

Rule 7's actor column is **RACI/DACI**, reduced to the two roles that carry
the weight here -- who executes, who approves -- a device invented against
precisely the failure of agreeing and nobody moving. The three kinds of
operator decision are the **agenda item types** every board secretary's manual
separates (action, discussion, information), for the same reason: a consent
agenda that mixes them approves in one act things that needed argument.
**Referral to committee** supplies what to do with a SPECIFICATION -- not
"later" but "elsewhere" -- and the **WIP limit** of kanban supplies the
scheduling rule, since a limit survives being read later and a date does not.
ISO/IEC/IEEE 29148 underwrites both this and rule 6: an instruction without an
actor is not unambiguous, and a requirement without an address is not
traceable.

## Rejected

- **Gating this inside the repository.** The evidence is the session
  transcript, which lives outside the repo, machine-local and unreproducible
  for any other reader. A gate that cannot run is worse than none (ADR-042
  rule 2). This record says so rather than shipping a check that measures
  nothing.
- **Use/mention markers in prose.** Hand-applied per citation: a forgotten
  marker fires a false failure, a misapplied one silently suppresses a true
  one. Fail-open, and a roster.
- **Self-audit as evidence.** The metric is authored by the party measured. A
  closure table is inflatable three ways — pad it, route everything outward,
  or **suppress the raise**, which the table cannot show. Self-audit is a
  necessary condition, never evidence.
- **A hand-ordered open list.** See rule 5.
- **A durable home for `odpuszczam`.** A dismissed finding is not work, so it
  does not belong in the work kernel; `done --cancel` is a G12 tombstone with
  a human ceremony, which costs more than the finding did. So **`odpuszczam`
  is session-scoped by design**: what was dismissed and later matters must be
  **raised again**, not looked up. This is the convention's weakest seam and
  it is stated rather than papered over — an independent audit named that
  column as the one where a finding can be buried under a plausible reason.

## Why these seven need a gate, and the measurement that says so

Not one of the seven is enforced by anything. That is stated here rather than
left to be discovered, because the same session produced the evidence for how
much an unenforced rule holds: **three rules were broken by their own author
AFTER the rule already existed and was in working memory.**

| rule | the violation | how long after |
|---|---|---|
| ADR-062 rule 4 — persist a measurement before dispatching the next role | a number quoted to the operator lived a full round in a chat message and nowhere else, and was wrong while it was cited | one exchange |
| rule 1 — every finding terminates | a review returned nine findings plus one off-scope; five were repaired and the prepared commit message said "five false assertions fixed" as though that were all of it | the convention was in memory at the time |
| rule 2 — provenance per finding | a behavioural claim about a CLI flag, asserted as fact in three consecutive answers, compressed out of a register entry whose qualifier it needed | provenance was already a rule |

The pattern is not that the author is careless. It is that **an instruction is
not a mechanism**, and this record is an instruction. Every catch in
`docs/governance/catch-log.md` was made by something that runs; every miss was
a judgement about content that nothing runs over. **The assistant's answer to
the operator is the one surface in this system with no gate at all** -- the
same seam the catch log measures as every-catch-structural,
every-miss-content, here applied to the output rather than the repository.

The narrative of how the seven rules arrived is deliberately NOT written down
beyond this table. It would be a seventh dated document in `docs/reviews/`
against six already written the same day, it is read to be understood rather
than acted on, and by the test this repository applies to its own frozen
reference that makes it a record, not an instruction. The table above is the
part that is actionable: it is the argument for building the gate.

## Falsifier

This decision dies if, across **≥10 post-adoption expository/advisory
answers**, the termination rate does not move from the 0.423 baseline — the
work/review stratum cannot carry the argument, being already at 0.914 with no
headroom.

The comparison means nothing unless: the definition is **frozen before** the
post period and applied by **someone who is not the author**, from the raw
transcript, with the per-finding enumeration published; **findings-raised is
reported alongside the rate**, because a rate that improves by raising less is
a loss that looks identical to a gain; and at least one **outcome outside the
author's control** is measured. Two are available and both have a baseline
from this session:

| outcome | baseline |
|---|---|
| escalations reaching a repository artefact | **9 of 16**; 7 evaporated |
| carry-forward recall against an independent list | **≈45%** (5 rows / ~11 live) |
| operator re-asks something already delivered | to be counted |

## Consequences

- `AGENTS.md` gains the operational form — **deferred**: that file is
  mid-review with five false assertions of its own
  (`docs/reviews/agents-md-review-2026-08-26.md`). This record stands alone
  until they land.
- `register-index` will report `adr-unaccounted:ADR-063` until the roadmap
  cites it or a baseline entry excuses it **with a reason**. That is an
  operator ruling of the same shape as ADR-062's, and it is named here rather
  than settled by side effect.
- Rule 5's carry-forward remains a hand-maintained roster until the work
  kernel carries it: `truth issue --deps` gives a blocking graph, and a
  topological order derived from it, which is what rule 5 actually wants.
  **The dependency is stated so that satisfying rule 5 by hand is understood
  as the interim, not the design.** Corrected 2026-08-26: an earlier draft of
  this paragraph said one work item was live and asked whether the kernel was
  dormant. `truth issues` reports **48 open, 53 closed, 2 cancelled** — the
  kernel is in heavy use and the figure came from `truth list --live`, which
  counts claims, not work items. The error is left recorded because it is the
  same shape as the three this record was written about: a measurement taken
  with the wrong instrument and reported with the confidence of a right one.
