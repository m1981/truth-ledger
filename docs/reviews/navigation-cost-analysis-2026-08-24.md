# Analysis: why navigation in this repository is expensive

A diagnostic brief. It records the measurements and the reasoning that produced
`mechanism-layers-brief-2026-08-24.md`, which carries only the resulting work
plan. Written by an agent reading the repository cold over one session; every
number below was measured here, and the ones that were wrong are marked.

---

## 1. The thesis

> The system pays for consistency in a currency it does not mint: **mechanical
> identity**. Every cross-reference is a hand-maintained **name**; every
> relocation re-mints that name; nothing forwards the old one. The discipline's
> obligations fan out to N places while its enforcement covers one, and the
> difference is paid by a human doing archaeology.

Shorter: the cost is not the size of the vocabulary, it is the **absence of
referential integrity** in it.

**The datum.** Repairing one cell in one table (INV-U's `Gate`) took fourteen
steps, ten of them archaeology: read Appendix A → find `FAULT OV` → learn
ADR-046 retired it → read ADR-046's migration table → find the target file gone
→ find the deleting commit → read its *message* to learn the successor → grep
the successor → verify the assertion → discover `arm-index` never saw it → fix
`SOURCES` → fix its fail-open → close the reverse pointer → fix three matcher
bugs.

**Three mechanisms.**

1. **Relocation mints a new name and abandons the old.** `FAULT B (INV-C)` →
   `FAULT B (step 2.5)`; `FAULT OV` → `test-instruments.sh` → a Python test;
   INV-C's demotion → "reproduce-on-read (INV-C successor)"; five deleted test
   scripts → one runner, no forward. Each move was **locally correct**. The sum
   is unnavigable.
2. **Obligation is central, enforcement is not.** One semantic change ("retire
   the path invalidator") fans out to: invert the arm, update the ADR, the
   Appendix A row, `explained.md`, check the instruments. The discipline says
   keep them consistent; one mechanism watches one place.
3. **Append-only grows the past without compressing it.** INV-A makes a
   correction an *addition*. 42% of ledger records are now inert; three
   archived copies of the same invariant table coexist. "Which name is current"
   gets harder with time, not easier.

**The asymmetry that explains it.** A referentially rigorous database was built
for claims *about the code* — ids, a total order, ADR-031's duplicate rule,
`order_check`. Claims *about the system itself* were left as free text.
Verification asks "does this sentence still match the code **now**", which git
can answer. Navigation asks "where did this go", which is a question about
**history**, and nothing here indexes it. That cost falls hardest on agents,
who have no memory across sessions and for whom archaeology is the most
expensive operation available.

---

## 2. Measurements

| what | value | note |
|---|---|---|
| declared relations in the reference graph | **44 of 1433 (3%)** | the self-describing layer declares 3% of its own relations |
| reference edges resting only on inherited ownership | **818 of 1433 (57%)** | direction is inferred from layout, not stated |
| dead backtick paths across 57 live docs | **20 of 183 (11%)** | two inside the paper itself |
| ADR-046 named paths still alive | **4 of 6** | name references |
| `gate-reachability.sh` dead references | **0** (12 globs + 8 literal names) | pattern references |
| `arm-index` sources actually read | **4 of 9**, for nine days | fail-open on a missing input |
| ledger records naming a label that are `claim` | **243**; the other **545 are echo (69%)** | verdict/invalidation carry the claim text forward |
| ledger entities vs events | **359 vs 4301** | the store is event-sourced; state is a fold |
| ledger records citing an ADR | **514 of 4763 (10.8%)**, 115 citing two or more | claim-mediated links between decisions |
| ADRs with no ledger record naming them | **7**: ADR-004 and ADR-054…059 | almost the whole recent tail |
| ledger ids cited by the paper | **0** | ops-guide 20, explained 7, AGENTS 3, README 2 |
| labels the paper leans on with ledger backing | **42 of 49 (86%)** | the 7 without are all invariants |
| Appendix A rows naming a specific arm | **16 of 21** | the remaining 5 were where the decay was |
| Appendix A rows found describing retired machinery | **4** | INV-C, INV-F, INV-J, and INV-E's parenthetical |

---

## 3. What reading paper v3 changed

Three corrections to a reading formed from the code alone.

**The scope is declared, and narrower than it looks.** §0: *"In 12207 terms the
whole ledger sits below the baseline: it catches sentences drifting from code,
never code drifting from intent."* The system does not do validation, and says
so first. An earlier reading of mine — that axiology is the load-bearing layer,
expressed through gates — is **wrong**: gates encode verification obligations,
not judgements about what is worth doing.

**The dominant real fault is semiotic, not epistemic.** §6.1: zero
hallucinations in 32 dispatches; the dominant fault is *scope overreach by an
honest actor with honest evidence* — a mismatch between a natural-language
quantifier and the domain of the command meant to support it. BFT's taxonomy
has **no row** for it. Their defects live at the seam where syntax (a command's
output) is asked to warrant semantics (a universally quantified sentence).

**§8 item 1a undercuts the property most worth admiring.** INV-O ("a verifier
cannot agree with its own session") is enforced by comparing two strings one
process can choose. Measured: 133 first-agree pairs, none same-session — but
*"a refusal writes no record, so this is what the ledger can show, not proof the
gate ever fired"* — while **14 agrees landed within one second of filing, the
fastest at 0.282s**, against 0.285s for a scripted zero-read cycle. Two are
live. Disclosed rather than solved.

Two general rules fall out, both worth keeping:

- **A refusal writes no record**, so the whole gate apparatus is unobservable
  from the ledger. This is a design property, not a bug, and it is why INV-O
  cannot be settled.
- **A refusal must not teach its own bypass** — a gate keyed on elapsed time is
  defeated by `sleep` and would advertise it.

---

## 4. A hypothesis that was falsified, kept because it was

**Proposed:** generic wording in Appendix A's `Gate` column ("Seeded fault")
marks decay rather than sloppiness — 3 of the 4 rows with such wording
described retired machinery.

**Falsified the same session:** INV-B ("Intake tests") and INV-L
("Armed-detector test") both carry generic wording and live mechanisms
(`policy.py:374`, `kernel.py:803`; the CI step "Arm the drift detector").

It is recorded rather than deleted because narrowing it to rescue it — "bare
`Seeded fault` with no letter" — would have been fitting the hypothesis to the
data at n=4 with a known counterexample. The real mechanism turned out to be
different and is in §1.3 above: the subject was rewritten at the moment of
inversion.

**Two more, still standing.** *Pattern references do not rot, name references
do* — confirmed (`gate-reachability` 0 dead, ADR-046 2 of 6 dead).
*Mechanisms catch only what has an address* — falsified by any mechanism
catching drift in unaddressed prose.

---

## 5. Method notes for whoever repeats this

- **Read the whole table before generalising from one row.** An earlier claim
  here — that Appendix A's `Gate` column says only "Seeded fault" — was wrong:
  16 of 21 rows name their arm precisely. The claim was generalised from the
  single row that had been grepped.
- **Look for the strongest counter-evidence to your own finding first.**
  Appendix A itself is the traceability table whose absence was being alleged;
  finding it turned a wrong diagnosis into a correct, narrower one.
- **A count of "backing" is not backing.** 69% of what first looked like ledger
  coverage was event echo.
- **Absence of a label in the test corpus is not absence of a test.** The
  behaviour of INV-D/F/K is exercised under other names; the gap is
  traceability, not coverage. `label-coupling` declares this same blind spot
  about itself.
