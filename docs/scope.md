# Scope

Status: **ACCEPTED** (2026-08-26, operator ruling). Drafted by an agent
2026-08-25 and ruled on unchanged: all four refusals stand as written.

This is the only document in this repository that no measurement produced.
Everything else here is either a decision somebody ruled on or an artifact
an instrument emitted. A boundary cannot be measured from inside; it has to
be declared, and declaring it is the operator's act, not an agent's. That
is why it carried PROPOSED for a day and why the ruling is dated
separately from the drafting.

## The sentence this system is built on

> Program testing can be used to show the presence of bugs, but never to
> show their absence. — Dijkstra, 1969

Everything below follows from it, including the refusals.

## What this is

An apparatus that answers **one** question:

> Does a written sentence still correspond to the repository it describes?

In ISO/IEC/IEEE 12207 terms it sits **below** the baseline. It is
verification, not validation.

Three properties carry most of the design, and knowing them explains most
decisions without reading the decisions:

1. **There are only events.** `.truth/claims.jsonl` is append-only. State is
   `fold(events)` in the total order `(ts, id, canonical-serialisation)` and
   is never stored (ADR-016, ADR-020).
2. **The clock is a parameter.** `stale` is a projection computed at read
   time from `now_dt`; `now_dt=None` means *do not ask the clock*. A claim's
   status is a function of when you ask (ADR-057).
3. **Warrant is defeasible, not true.** INV-C/D/E/F specify **defeat**
   conditions, not verification conditions. A claim stands until something
   defeats it.

## What this is NOT — the refusals

A finding that falls under one of these is **closed as out of scope**. It is
not baselined, not excused, not deferred. Excusing means *we owe this*;
refusing means *we do not*.

**R1 — Whether the work was worth doing.** That is validation and it lives
above the baseline. No green run here is evidence that anything was worth
building, and no amount of green will ever become that evidence. Whoever
wants that number must count it outside this apparatus.

**R2 — Whether a true sentence is about the right thing.** This system can
tell you that a sentence still corresponds to the repository. It cannot tell
you the sentence describes something that matters.

**R3 — Consumer-repository policy.** The template ships; the meta-repo's
instruments do not (ADR-003 rule 2, ADR-046 Tier C). What a downstream
repository ought to do with the template is out of scope here.

**R4 — Anything that requires a stored status.** Proposals whose mechanism
needs status written down rather than folded are refused on sight; they
contradict property 1 and every such proposal has been a re-invention of
the invalidation records that were retired at PPV 3.6%.

## What this system cannot detect, by construction

State it plainly, because a system that hides its blind spot is worse than
one that has a bigger one:

- A **live check the coverage sweep cannot enumerate.**
  `scripts/gate-reachability.sh` reports *"every one reached by a root"* over
  the set it recognises by filename pattern, and `scripts/retracted-figures.sh`
  runs on every push — `scripts/release-battery.sh:151` invokes it — without
  appearing in that list. The measure of gate coverage is itself enumerated by
  pattern, which is the RULING-8 class one register over, and
  `instruments/capsule-blindness.py` cannot see it because it reads
  `.truth/claims.jsonl` only.
  *Corrected 2026-08-28.* This entry previously read "a check that no root
  invokes AND whose filename does not match the patterns" and named the same
  file. The second conjunct held; **the first was false**, so the example
  failed as stated while the blind spot behind it was real and larger. The
  correction is dated rather than quietly applied because the false version
  was copied into `docs/assurance.md` C6 within an hour of that case being
  written, by an author who checked neither half. The Status line above is
  untouched: this is a descriptive sentence, not one of the refusals, and a
  description is overturned by measurement rather than by a new ruling.
- A **sentence that is false and cites nothing.** `fact-health.sh` polices
  citations; a false recital carrying no citation is invisible to it. This
  is stated in ADR-060 and accepted.
- **Whether a mechanism a document names is wired into any gate.**
  `docs/registers.md` delegates this to `gate-reachability.sh`, which cannot
  see three of the five instruments it names.

## The word this repository never defined

`gate-reachability.sh` partitions the world on the word **check** and
nothing in the executable surface says what it means. Proposed definition,
so that the partition has a domain:

> A **check** is an executable that can exit non-zero on a finding AND whose
> exit code is read by another executable or by a documented human gate.

An executable that only prints is an instrument, not a check. An executable
whose exit code nobody reads is not a check that is unreachable — it is not
a check.

## Boundary maintenance

This document has a hard ceiling of 120 lines, enforced by
`instruments/map.py`. The ceiling is the mechanism: a scope statement that
may grow becomes the thing it replaces. When it will not fit, something in
it has stopped being a boundary and belongs in a decision record instead.

## Do not read further to start

You are not expected to read the registers, the paper, or the decisions
before doing work. Query the map:

    python3 instruments/map.py --for <path-you-are-about-to-touch>

`docs/map.txt` is generated. If it disagrees with the tree, the tree wins
and the map is stale — regenerate it, do not correct it by hand.
