# Grounding note: what actually holds this project up

Written 2026-08-26, at the operator's request, after a session that produced
nineteen catches and fourteen misses. It answers two questions they asked as a
specifier rather than as a user: **how should this have started on a clean
canvas**, and **how do other IV&V implementers ground themselves**.

It is a reference, not a decision. Nothing here is gated and nothing here
should be. It is filed as a brief because it is a dated analysis, and if it
needs revising the revision is a new dated brief.

---

## 1. The diagnosis, which is the reverse of the one that prompted it

The felt problem was: *the knowledge reaches back to Aristotle and dozens of
later authors, and I have not mastered it.*

Look at what actually found defects in this repository. Not ontology. Four
very flat things, each of which is a shape rather than a theory:

- a check that walks one direction only
- a count fitted to the list beside it
- a measurement living only in a message
- a partition whose domain is unstated

The use/mention distinction did not find the two-marker defect — **a gate
firing on itself did, and Tarski named it afterwards.** ADR-062 did not come
from epistemology; it came from an incident in which an agent demonstrated its
own gate going red and a defect passed anyway. The carrier taxonomy did not
come from a theory of genera; it came from asking *"what is the domain of this
partition"* **after** a partition had already failed.

That order — practice first, name second — is normal and is not a deficiency.
But it means the philosophy here functions as **retrospective vocabulary, not
as generative method**, and the crisis assumes the opposite.

**Two philosophical commitments do carry weight, and it is worth knowing it is
only two:**

- **§0, the scope decision.** Verification, not validation; below the 12207
  baseline. This stops the system claiming what it cannot deliver, which is
  the single most load-bearing sentence in the corpus.
- **Defeasibility.** INV-C/D/E/F state *defeat conditions*, not truth
  conditions. That is a real epistemological choice and it is why the ledger
  is append-only and why "warranted until defeated" beats "proven".

Everything else — sortals included — has so far been ornament or after-the-fact
naming. Naming is worth something: a named class is findable next time. It is
not worth a crisis.

---

## 2. The recurring defect shapes — the actually reusable part

Every one of these was measured here, most of them more than once. Each has a
signature you can look for and a test you can run. This is the cheat sheet.

| shape | signature | the test |
|---|---|---|
| **Roster without a return** | a hand-maintained list, and nothing asks the other direction | *what happens when something appears that is not on the list?* If the answer is "nothing", it will rot |
| **Count fitted to the list** | a number that agrees with an enumeration printed beside it | recount from the **source**, never from the list. "SIX of the ten" sat above a list of six |
| **Unstated domain** | a partition whose title quantifies over more than its content | *this is total over WHAT?* An unstated domain reads as universal |
| **Unpersisted measurement** | a figure quoted in a report | `grep` the record the report cites. If it is not there, it is testimony — and it decays before anyone checks it |
| **Inverted arm** | an assertion message that describes an **observation** rather than a **requirement** | *"X was reported as Y"* is a sentence about what is; a requirement reads *"X must not be Y"*. A gate certifying a defect turns a hole into a requirement |
| **Check below a `continue`** | a correct check applying to a subset nobody declared | coverage cannot see this: the line executes every run. *Over what domain does this check apply, and does the documentation say the same?* |
| **Shrinking reading** | a finding that gets **smaller** after a regression | remove an input. If the count goes down instead of up, the reading is fail-open |
| **Over-suppression** | "unmeasurable", "not countable", "cannot be checked" | a claim that no predicate exists must **name the predicate that was tried**. 209 excusals were one `wc -l` away |
| **Use / mention** | a marker about another file, read as a declaration about this one | a declaration must be about its own file to be one. Object language vs metalanguage, found empirically by a gate shooting at itself |

Two meta-rules that sit above the table:

- **A gate that has not been made to fail is not evidence** (ADR-061). Applies
  to arms as much as to instruments — an arm whose fixture cannot express the
  defect is not an arm.
- **Self-demonstration is necessary and not sufficient** (ADR-062). Measured
  here three times: the author demonstrated their own gate red and shipped a
  defect anyway, in three separate rounds.

---

## 3. How IV&V implementers actually cope

Shorter than expected: **less theory, more standardised bookkeeping, and a
case database.**

- **IEEE 1012** defines independence **organisationally** — technical,
  managerial, financial — not epistemologically. ADR-062 is that question,
  re-derived from zero.
- **NASA IV&V** carries its value in an issue database, not a doctrine. A
  practitioner learns from incidents, not axioms.
- **DO-178C** ships a table of objectives marked *"with independence"* — a
  ready-made answer to which activities need a separate actor.
- **IEC 61508 / ISO 26262** require a formal deviation register: rationale,
  scope, owner, **expiry**, and review of the open population *as a
  population*.

**The important part: three of those forms already exist here, invented from
first principles.**

| what this repository built | the standard form it is |
|---|---|
| `docs/governance/catch-log.md` | a discrepancy / issue log |
| `docs/registers.md` | a traceability matrix |
| `docs/waivers.md` | a deviation register |

The sense that this requires Aristotle comes from having derived those forms
instead of taking them. Taking them costs nothing and would have saved a week.

---

## 4. Clean canvas: what would go first

Not the ledger. The ledger answers *"does this sentence still match the code"*.
The actual pain was navigation, provenance, and the escape surface — and all
three were discovered late.

1. **The catch log, empty, on day one.** It is the only artefact that answers
   *"did this pay"*, and it was built last. Its rule 4 — a mechanism with no
   catches is a cost with no measured return — is the only cost function in
   the whole system.
2. **The provenance rule: every artefact names its emitter.** `instruments/map.py`
   sits in the tree and no session can be identified as its author. In a system
   whose subject is knowing where a fact came from, that is a hole in the thing
   itself.
3. **No list without a reverse check, and the reverse check written BEFORE the
   list.** Three defeats here were one defeat: a roster with no way back.
4. **Only then a mechanism — and only one that closes a catch already recorded.**

That is an architecture driven by **incident** rather than by **model**. The
current one is driven by model, which is why the subject of the system keeps
being discovered after the fact.

---

## 5. Where reading actually pays, tied to open problems

Not Aristotle. These map onto questions that are open right now.

- **Lakatos**, progressive vs degenerating research programmes. *This is the
  real question* — not "is my ontology right" but "does this programme still
  predict new facts, or does it only rescue itself with auxiliary
  hypotheses". The catch log is the data for it.
- **Leveson, *Engineering a Safer World*** (STAMP). Gates are controllers, not
  tests. Her critique of assurance-by-decomposition lands directly on this
  design.
- **Hollnagel, ETTO / Safety-II.** The efficiency–thoroughness trade-off.
  §8 item 2 says efficacy is unknown and cost unfavourable — that is an ETTO
  question, not an epistemological one.
- **Hacking, *Representing and Intervening***. The *intervening* half is
  ADR-061 exactly: a gate not forced red is not evidence.
- **Perrow, *Normal Accidents***. When the apparatus itself becomes the
  hazard — relevant with 36 waivers of which 15 leave no trace.
- **Rushby** on assurance cases, if the argument is to be formalised rather
  than only the mechanisms.

---

## 6. The honest open problem

The crisis has a real object, and it is not the reading list.

**The efficacy of this system is unmeasured, the cost is unfavourable, and a
sample of nineteen catches against fourteen misses is far too small to
conclude anything.** That is the genuine problem, it is stated in §8 item 2,
and it is not treated by study. It is treated by the catch log running for
months until the numbers mean something — which has already started.

One datum against the despair, and it is a measurement rather than
encouragement: `instruments/map.py`, written by a session nobody can identify,
independently names the roster class **three times** — arm-index's source
list, register-index's table parser, gate-reachability's eleven globs. The
thesis reproduces without its author. That is stronger evidence of having
understood this system than any reading that could be caught up on.
