# Architect's primer

Status: **PROPOSED** (2026-08-26, written for the operator). Like
`docs/scope.md`, no measurement produced this and none can: it is orientation,
not a finding. Nothing enforces it. Read it when the system stops feeling like
one thing.

---

## 1. What the disorientation is actually tracking

This system was built **bottom-up, from pain**. Every mechanism here exists
because something concrete broke. That is why the parts are unusually good —
and why there is no shape. Bottom-up construction produces **correct parts and
no roof**. At sixty-two decisions, twelve hundred arms and fifteen instruments,
the absence of a roof stops being an aesthetic complaint and starts feeling
like personal incompetence.

It is not. It is one missing document, and the missing document is small.

The diagnostic question that separates the two conditions:

> Can I name the single sentence that all of this is evidence *for*?

If not, the problem is the roof, not the knowledge.

## 2. What the philosophy is for, and what it is not for

Trace how each mechanism here actually arrived. The partition did not come
from Reiter; it came from the `-ok` heuristic missing a tenth flag. Role
separation did not come from mechanism design; it came from an implementer
shipping a defect twice after demonstrating its own gate red.

**Philosophy here is diagnostic and communicative, never generative.** It
supplies names for failure classes, so the second instance is recognised more
cheaply than the first, and so it can be handed to somebody else. That is a
real function. It is not a prerequisite.

Evidence that the knowledge is not what is missing: this repository arrived
independently at role independence (DO-178C), suspect links (DOORS), diagnostic
coverage (IEC 61508) and fail-safe defaults (Saltzer & Schroeder 1975). What
was missing was never the knowledge. It was **a frame that would have supplied
it cheaply**.

## 3. What IV&V practitioners actually do

None of it depends on erudition.

**They borrow the skeleton.** Nobody in safety-critical work writes their own
conceptual framework. They take IEC 61508, DO-178C, ISO 26262, EN 50128,
ISO/IEC 15288 and 12207, and **inherit the ontology** — objectives, life-cycle
data items, independence levels. They argue with it and tailor it; they do not
invent it. The value is not that the standard is right. The value is that it is
**finished and external**, so argument about the frame ends and argument about
the system begins.

**They put an assurance case on top.** GSN or CAE, normalised in
ISO/IEC 15026-2. One claim at the top, decomposed into subclaims, each
terminating in evidence. *This is the thing this repository does not have.*
Everything here is evidence with no claim above it, which is exactly why the
question "is this worth its cost" returns silence: there is no sentence for the
evidence to be evidence of.

**They start from a hazard list, not a feature list.** HAZOP, FMEA, STPA.
First "what can go wrong", then "what shall we build".

**Traceability is the backbone, not a feature.** DOORS and Polarion exist
because the chain requirement → design → test → evidence *is* the artifact. Link
hashes arrived here late; in the standards world they are day one.

**Independence is organisational, not technical.** DO-178C specifies who may
verify what. ADR-062 rediscovered this empirically. That is a strong
confirmation of the instinct — and it shows the shape: the standards *begin*
where this repository arrived.

## 4. Clean canvas — the first five days

**Day 1 — one sentence of purpose, one of non-purpose.** The scope charter.
It was written here in month N; it is day-one material.

**Day 2 — the hazard list.** How can a sentence and a repository diverge?
File moved. File deleted. Content changed. Sentence changed. Sentence was never
true. Sentence is true but about the wrong thing. That last one would have been
identified as **out of reach on day two**, instead of in month N.

**Day 3 — the top claim and its decomposition.** For instance: *every
normative sentence in this repository corresponds to the repository state, or
is marked as not corresponding.* Decompose it. Every leaf terminates in
evidence. **Now every instrument has a parent**, and an instrument with no
parent claim is visibly unmotivated. That structure alone prevents fifteen
instruments of which twelve have never caught anything.

**Day 4 — the ontology of the evidence store.** Events in a total order, state
as `fold`, defeasibility rather than truth. This repository chose well here,
and better than the stateful database most projects would have reached for.

**Day 5 — independence rules, before the first instrument.** ADR-062 on day
five, not in month N.

Only then, code.

## 5. What follows for the system that exists

**Do not rewrite.** The parts are good, and a rewrite trades good parts for
worse parts with a better narrative.

**Add the roof: one assurance case, and it is a small document.** A top claim,
four to six subclaims, and every existing instrument assigned to a leaf. A day
of work. After it exists, two standing questions stop being questions about
mood:

| the question | what it becomes |
|---|---|
| does this do valuable work? | does the evidence support the top claim? |
| what shape does this have? | the tree, on one page |

And the twelve instruments at zero catches acquire the test they currently
lack: **which leaf are you evidence for?**

## 6. The reasoning ladder, as a checklist

Applied in this order when auditing anything here. Each level's characteristic
move is worthless if the level below it has not been answered — that mistake
was made three times in the session this document came out of.

| # | ask | tradition |
|---|---|---|
| L0 | did I measure the world, or my own apparatus? (`$?` after a pipe is the pipe's) | metrology; Hacking |
| L1 | of *what* kind? "how many" is parasitic on "of what" | Aristotle → Strawson → Wiggins |
| L2 | is this a **search** (open world, silent about non-matches) or a **partition** (closed world, unclassified must be 0)? | Halmos; Reiter |
| L3 | what is the partition **over**? total over flags is not total over bypasses | Tarski (domain); Saltzer & Schroeder (complete mediation) |
| L4 | does this sentence **stipulate** or **report**? a description hidden in a norm inherits its immunity | Hume; Searle; Hart |
| L5 | what has its own truth-maker? derived prose has no standing to disagree with its source | foundationalism; topological order |
| L6 | has this check ever been **red**? if not it may be vacuous | Popper → Lakatos → Mayo; mutation testing |
| L7 | is this **use** or **mention**? a declaration must be about its own file | Tarski; Franzén as restraint |
| L8 | who knows what? the arrangement is the mechanism | Machamer/Darden/Craver; Hurwicz/Myerson |

**The seam.** L0–L2 are measurable. **L3 is declarable but not measurable —
a boundary cannot be measured from inside.** L4–L8 are normative. This
repository's apparatus lives entirely in L0–L2 and is very good there; it
cannot by construction reach L3 and above. The catch log shows this as a
number: every recorded catch is about structure, every recorded miss is about
content.

## 7. The one caution

An assurance case becomes theatre with alarming ease — a diagram arguing for a
conclusion already reached. The defence is the one already practised here:
**every leaf carries a defeat condition.** Not "what supports this" but "what
would kill it". Without that column the result is a handsome tree that asserts
nothing, and the disorientation returns in a month, better documented.
