# Assurance case

Status: **PROPOSED** (2026-08-28, agent-authored). Structure: **CAE** — Claim,
Argument, Evidence — the lighter of the two forms normalised in ISO/IEC
15026-2; GSN is the other. Chosen because this repository argues in prose and
a diagram would be the first thing to rot.

Everything here is bounded by `docs/scope.md`, which the operator accepted
unchanged on 2026-08-26. A finding that falls under one of its refusals is
**closed as out of scope** and does not appear below.

## Why this document exists

Every artifact in this repository is evidence. Until now none of them was
evidence **for** anything stated: there was no sentence the instruments could
be said to support, so the question *"is this apparatus worth its cost"*
returned silence however green the run. That silence was structural, not
neglect — but it also meant no instrument could be asked the one question that
makes a zero meaningful: **which claim are you evidence for?**

## The rule that governs every leaf

**Each leaf carries a DEFEAT CONDITION — what would kill it — not a list of
what supports it.** An assurance case becomes theatre the moment it argues
towards a conclusion already reached, and the only cheap defence is that every
node states how it dies. A leaf with no defeat condition is not evidence here;
it is decoration, and it is marked as such below.

---

## C0 — the top claim

> **Every normative sentence in this repository either corresponds to the
> repository state, or is marked as not corresponding.**

**Context.** Dijkstra, 1969, quoted in `docs/scope.md` as the sentence this
system is built on: *program testing can be used to show the presence of bugs,
but never to show their absence.* C0 is therefore a claim about **detection**,
never about correctness: it says divergence becomes visible, not that
divergence is absent.

**Assumption, stated so it can be attacked.** That the ways a sentence and a
repository can diverge are enumerable. They are enumerated in the argument
below, and the enumeration is the case's weakest joint: a mode nobody named is
a mode nothing watches, and no instrument here can report one.

**What C0 deliberately does not claim.** Not that a sentence is worth writing
(`scope.md` R1: validation, above the baseline). Not that a true sentence is
about the right thing. Not that an unwatched sentence is watched.

**Defeat condition for C0.** A normative sentence found false, and neither
marked nor detectable by any leaf below — where the miss is a MODE, not an
instance. One such finding retires the enumeration; it does not patch it.

---

## Argument — decomposition by divergence mode

The strategy is: **enumerate the ways a sentence and the repository can come
apart, and give each one a leaf.** Not by subsystem, not by instrument — those
decompositions let an instrument exist without a claim, which is the condition
this document was written to end.

### C1 — the thing a sentence describes has moved or vanished

**Evidence.** `truth reproduce` at the push boundary re-executes every live
claim's recorded capsule; a watch set whose paths moved raises
`capsule-stale`. `arm-index` hashes the link target of each Appendix A row and
each cited position, so a moved target makes the citing row SUSPECT rather
than silently wrong.

**Defeat condition.** A sentence whose subject moved, whose capsule still
reproduces, and whose row stays unsuspect. Reachable today: a claim whose
recipe greps by content rather than by path survives a move that invalidates
it.

**Status: HELD, with a known hole.** The hole is in `scope.md`'s own blind-spot
list — a false sentence citing nothing is invisible.

### C2 — the content changed under a sentence that still points at it

**Evidence.** The capsule's `output_hash` and `returncode`; `truth reproduce`
exit 7 on divergence. Demonstrated on this repository three times in three
days, once catching a claim invalidated by a commit made minutes earlier.

**Defeat condition.** A recipe whose output is stable across the change it was
meant to detect. Instanced: `tr-a00459ec` pinned a COUNT, so it caught an
addition; a recipe pinning presence would not have.

**Status: HELD.**

### C3 — the sentence changed, and the fact it stood on did not

**Evidence.** ADR-060: normative prose cites a position, and the citation is
freshness-checked; `arm-index` carries 221 prose-citation hashes, so an edited
position makes the citing paragraph SUSPECT.

**Defeat condition.** A normative paragraph outside `PROSE_DOCS` — which is
exactly two files, `instruments/arm-index.py:116`. **`AGENTS.md` is not one of
them.** Every rule in the file agents read first is NORM here, not ENFORCED.

**Status: HELD FOR TWO FILES.** Named as partial, because the corpus is two
documents and the repository has fourteen registers.

### C4 — the sentence was never true

**Evidence.** Author/verifier separation (INV-O, G11): `TRUTH_SELF_VERDICT`
exists as a registered waiver precisely because agreeing with one's own claim
is refused by default. ADR-062: the reviewer is not told the specification.
Measured across this session: nine catches by a reviewer denied the spec, more
than any single instrument.

**Defeat condition.** A false sentence filed and verified by parties who are
formally separate but share a premise — the failure independence cannot see.
**Nothing here detects that**, and the review that named it (C4 Independence in
`premise-index`) is the only one of six defeaters this repository has never
gated.

**Status: HELD BY PRACTICE, NOT BY MECHANISM.** The strongest leaf and the
least mechanised.

### C5 — a sentence stands on a fact that has since died

**Evidence.** `scripts/fact-health.sh` judges every `tr-` id cited in live
markdown by its ledger status; FAIL on stale, diverged, retracted, missing.
Demonstrated 2026-08-28: it refused a draft **as it was being written**, when
an operator-actions entry ruling on citation hygiene cited a retracted claim.

**Defeat condition.** A dead fact recited without its id. `scope.md` states
this blind spot and accepts it. Also: the frozen-reference exclusions —
`docs/reviews/`, `docs/archive/`, the journals, the catch log — are outside
the corpus by design, so a dead citation there is not a finding.

**Status: HELD, with a declared domain limit.**

### C6 — the mechanism a sentence names is wired to nothing

**Evidence.** `scripts/gate-reachability.sh` — transitive closure from the
roots, **and, since 2026-08-28, an assertion that its own complement is
empty**: every file a root reaches which the CHECK patterns do not name must
be declared `not-a-check:<path> -- <reason>` or the sweep fails.
`instruments/register-index.py` (every register's location and currency, both
directions). No count is quoted here on purpose; both figures move, and a
count in prose is the drift this repository produced three times in one day.

**Defeat condition.** Not "a check no root invokes" — that formulation was
wrong here and is corrected below. The real one: **a live check the
reachability sweep cannot enumerate, while the sweep reports that every check
it found was reached.** The sweep's answer is true over the set it can see and
is read as true over the set that exists.

**Instanced, and then closed — the same day, which is why the instance is
recorded rather than deleted.** `scripts/retracted-figures.sh` runs on every
push (`scripts/release-battery.sh:151`) and did not appear in the sweep's
CHECK patterns, while the verdict said every check found was reached. Adding
the complement assertion surfaced **nine** reached files outside the
enumeration, of which **three were live gates**: that file, the whisper hook
that denies edits, and `scripts/check-truth.sh` — **the commit gate, running
on every commit, outside the measure of gate coverage**. All are now
enumerated; the four genuine non-gates carry declarations with reasons.

The class is not closed by that repair, only this instance. The patterns
remain a hand list — **guarded by its complement**, which is the whole
difference: anything a root reaches and the list does not name now fails the
hour it is written.

This corrects a claim made in `docs/scope.md` and copied into an earlier draft
of this leaf without checking either half: that file's blind-spot list calls
`retracted-figures.sh` "a check that no root invokes AND whose filename does
not match the sweep's patterns". The second conjunct holds; **the first is
false**, so the example failed as stated while the underlying blind spot was
real and worse than described. The correction is recorded rather than quietly
applied, because the original stood in the charter and was carried into this
case within an hour of the case being written.

Also standing: `docs/registers.md` delegates this question to a sweep that
cannot see three of the five instruments it names.

**Residual, and it is in the sweep's own header:** a check dispatched through
a variable-built path is invisible to the textual edge-finder and reads as
UNREACHABLE — the fail-safe direction, a loud false alarm rather than a quiet
blessing. That is the remaining way past C6 and it is chosen, not overlooked.

**Status: HELD, with a named residual and a repair dated 2026-08-28.**

### C7 — a measure reports green having examined nothing

**Evidence.** ADR-042 rule 2 and ADR-061: DONE requires a gate that can go
red for a named reason and someone who demonstrated it. `arm-index` (1279
arms, 238 families) reconciles arms against the faults they claim to guard.
`instruments/capsule-blindness.py` exists for the fail-open capsule class,
commissioned by operator RULING 8 after a pattern counter reported 10 arms
against 12, green for four days.

**Defeat condition.** A counter that enumerates by pattern in a surface
`capsule-blindness.py` cannot read — it reads `.truth/claims.jsonl` only.
**`scripts/gate-reachability.sh` WAS one such counter** (see C6): it
enumerated by filename pattern and reported completeness over what it
recognised — the RULING-8 shape one register over — until 2026-08-28, when it
gained the complement assertion this class requires. That is the third time
this repository has applied the same remedy to the same disease:
`arm-index`'s reconciliation pass, `waiver-index`'s total classification, and
now the sweep. The remedy is known; what is missing is anything that finds the
next instance before a person does.
**Instanced twice more this week, in `scripts/release-battery.sh`, both withdrawn**
(`docs/reviews/plan-mode-review-2026-08-26.md`,
`docs/reviews/battery-nested-stub-review-2026-08-28.md`).

**Status: HELD FOR THE LEDGER, OPEN FOR CODE.**

### C8 — the list of ways past a gate is itself incomplete

**Evidence.** `instruments/waiver-index.py`: 36 waivers over 6 carriers, both
directions against the CLI parser, 0 unclassified.

**Defeat condition.** A bypass carried by something that is not a flag.
`docs/waivers.md` says so in its own first section — **THIS REGISTER IS NOT
TOTAL** — and names five carriers it records by hand from no list at all, a
`<path>#<selector>` exemption among them.

**Status: HELD PER HARVESTED CARRIER, declared not total.**

---

## Instruments assigned to no leaf

The census in `docs/governance/catch-log.md` classifies fourteen instruments
from their own docstrings: **seven detectors, seven reporters**. Every
detector above serves a leaf. The seven reporters — `map`, `blast-report`,
`concern-tag`, `override-velocity`, `retraction-causes`, `semantic-audit`,
`separation-report` — serve **none**, and that is correct, not a gap: a
reporter emits a measurement for a person to read. It is not evidence for C0
and its zero-catch record carries no information.

Two detectors serve leaves only indirectly and are named here rather than
stretched into one: `field-consumers` (every payload field has a reader) and
`watch-derivation` (a claim watches what its recipe reads). Both defend C1 and
C2 from underneath by keeping the evidence machinery honest.

---

## What this case does NOT cover, stated where it cannot be missed

- **Whether the work was worth doing.** `scope.md` R1. No leaf, ever.
- **Whether a true sentence is about the right thing.** Verification sits
  below the 12207 baseline; paper §0.
- **`AGENTS.md` and thirteen of fourteen registers**, for C3: the
  freshness-checked prose corpus is two files.
- **Premise independence** (C4): formally separate parties sharing a premise
  is the one defeater of six with no gate at all.
- **Any divergence mode nobody has named.** C0's assumption. This is the
  case's weakest joint and no instrument can report a violation of it.

## How this document dies

It is retired, not amended, if a normative sentence is found false by a MODE
absent from C1–C8. Amending the enumeration after such a find would be
fitting the case to the evidence — the failure this repository has caught in
its own instruments five times.

It is theatre, and should be deleted, if any leaf ever acquires a support list
in place of its defeat condition.
