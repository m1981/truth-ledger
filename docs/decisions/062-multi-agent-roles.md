# ADR-062: Agent roles are separated by what each is NOT told

Status: **PROPOSED** (2026-08-24, agent-authored, from one session's measured
experience). The operational form belongs in `AGENTS.md`; this record carries
the decision and its falsifier.

## Context

One session dispatched three agents: a measurer, an implementer, and two
adversarial reviewers. The decisive datum:

> **The implementing agent demonstrated its own gate going red on all three of
> its checks, restored byte-identically, and reported honestly. A defect still
> passed under it** — a malformed table row was silently dropped, un-adminis-
> tering its register: the same shape as an instrument that named nine sources
> and read four for nine days, reproduced inside the tool built to catch it.

Self-demonstration is **necessary and not sufficient**. This is §8 item 1a of
the paper — a single observer verifying its own work — reproduced under
controlled conditions, twice: the second review then found a measure defeated
by one line of HTML comment.

Two further observations from the same session:

- The measuring agent was given a specification and **no hypotheses**. It
  noticed the specification was wrong (counting sandbox residency by variable
  name is near-meaningless when `mkrepo` inherits the working directory) and
  added a tracking pass unprompted. Told the thesis, it would likely have
  confirmed it.
- The session's own worst act was patching a shipped Tier A gate while out of
  context, guessing a variable name the script does not have. An agent with
  fresh context reads the script first.

## Decision

Four roles, separated by **what each is not told**.

| role | receives | must NOT receive | must produce |
|---|---|---|---|
| **measure** | a measurement spec | any hypothesis about the result | numbers, and a note if it changed the spec |
| **implement** | a spec + house conventions | — | the change **and a demonstration of its gate going red**, restored byte-identically |
| **review** | the diff + house conventions | **the specification** | confirmed defects, each with the command that reproduces it |
| **operator** | everything | — | the commit |

Four rules follow, each earned. (Three were written first; rule 4 was
added below after it was learned the expensive way, and this line is
corrected with it rather than left counting the original three.)

1. **The reviewer's ignorance of the spec is load-bearing.** Given the spec it
   checks compliance — "was what was asked built" — not correctness. The
   defects found here were of the second kind.
2. **An agent never commits.** The dispatcher cannot honestly review with an
   exhausted context, and writing "verified" without verifying is the failure
   INV-O exists to prevent.
3. **The review travels with the change.** Commit them together, so the
   evidence against a change cannot be separated from it.
4. **A measurement is persisted before the next role is dispatched.** A finding
   that lives only in a task notification cannot be cited, because there is
   nothing for a later reader to check it against. Write it to
   `docs/reviews/` first, then dispatch.

**Delegate implementation when your own context is thin, not only when the task
is large.** Thin context produces blind patches, and this session has a Tier A
gate it broke to prove it.

Rule 4 was learned the expensive way, after this ADR was first written. An
audit of `AGENTS.md` found four false claims and was never written to disk. The
redrafting agent dispatched next cited *"the 2026-08-24 audit of this file"* —
a document that exists nowhere — and that phantom citation is what licensed its
whole restructuring. The audit was real; the record was not.

That is the same class as every other finding this effort has produced — a true
statement with nothing holding it — **reproduced inside the workflow built to
prevent it**, by the dispatcher, one exchange after writing the rules down.
See `docs/reviews/agents-md-audit-and-review-2026-08-24.md`, which is that
persistence performed after the fact.

## Rejected

- **One agent doing implement-and-verify.** Measured to fail here, twice.
- **Reviewer given the specification.** Turns review into a conformance check.
- **Agent commits after a green review.** A review reduces risk; it does not
  transfer authorship. Two reviews here each found defects the previous pass
  had cleared.
- **Putting this only in AGENTS.md.** A norm without a red-gate condition is
  not DONE (ADR-061). AGENTS.md carries the operational form; the decision and
  its falsifier live here, and what can be gated should be.

## Consequences

- `AGENTS.md` gains a short operational section: the four roles, the three
  rules, and the instruction that a review is dispatched on the diff, never in
  parallel with the work that produces it.
- Mechanisable residue, for whoever wants it: a commit that adds or edits a
  file under `instruments/` without an accompanying review document is a
  candidate finding. So is a change whose message cites an analysis that no
  file in `docs/reviews/` provides. Those are the parts of this decision a gate
  can hold; the rest is norm, and is marked as such.
- Cost is real. Two review cycles on one small instrument produced fifteen
  distinct defects and no finished artifact. The alternative was committing the
  first version, which contained the exact bug class the session had spent its
  length removing.

**Falsifier:** if a defect of the class a reviewer is dispatched to catch
reaches a commit despite a review pass, the separation is wrong — the roles
divide something other than what matters.
