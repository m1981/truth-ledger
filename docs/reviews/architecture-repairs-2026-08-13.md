# Architectural repairs — agent briefs

Findings A1–A5 from the 2026-08-13 architecture review. Written so an
independent agent can execute one brief per session, and a different agent can
verify it, per ADR-010's own rule: the session that writes an arm never
verifies it.

---

## 0. The acceptance instrument — read this before any brief

`instruments/fingerprint.sh` drives the real CLI through **43 probes** — every
intake gate, the execution boundary, the verdict surface, the work kernel, and
every non-trivial exit code — and records `(exit code, stderr, stdout)` as one
canonical file. Ids, hashes, timestamps and commit shas are normalised; both
the wall clock and git's clock are pinned, so the output is byte-deterministic
across runs.

```bash
./instruments/fingerprint.sh > /tmp/after.txt
diff instruments/fingerprint-baseline.txt /tmp/after.txt    # MUST be empty
```

**Why this exists, and why "the tests pass" is not the acceptance criterion.**
For a refactor the tests are the thing an agent can bend to make green. ADR-044
got this right: its acceptance was *the old corpus unchanged*, and any arm-count
delta meant the phase had exceeded its licence. The fingerprint generalises
that to observable behaviour.

**It is red-proven**, and the proof found two holes in its own first draft:

| seeded change | detected |
|---|---|
| two `INTAKE_GATES` rows swapped | ✅ 4 lines |
| `CITATIONS_EXIT_CITED` → `1` | ✅ 2 lines |
| one word changed in a refusal message | ✅ 2 lines |
| one CC-1 advisory line dropped | ✅ 1 line |

The first draft missed the first two. The order probe was tuned to Jaccard
0.556 — *below* G8's 0.6 threshold, so G8 never fired and the order of the two
gates was unobservable. And no probe reached the `cited` branch of `citations`,
so the only non-trivial exit code in that file was never exercised. Both are
the dark-arm class: an arm that cannot report a miss. **Assume your own new
arms have this defect until a seeded mutation proves otherwise.**

---

## 1. Sequencing

```
S1 (sequential, one stream)        S2 (parallel)
  A1 sys.exit boundary               A4 verb table
  A2 advisory split
        │                                │
        └────────────┬───────────────────┘
                     │
              V1 adversary  ·  V2 equivalence
                     │
                  A3 retire the mirror
                     │
                  A5 docs (me)
```

**Why A1 → A2 are one stream, not parallel.** Both touch `cli.py` and both move
the decide/act boundary; run in parallel they conflict on every call site.

**Why A4 is parallel.** It is confined to `main()`, which neither A1 nor A2
enters.

**Why A3 is last.** It retires the monkeypatch seam that the current test
corpus depends on. Doing it first would remove the safety net under A1, A2 and
A4 exactly when they need it most.

---

## S1a — A1: refusals return, the shell exits

**The finding.** `gates.run_intake_stage` terminates the process. `shellio`
does it ten times. The pure core correctly returns refusal *strings*; the edge
kills the process from library depth. Consequences: nothing composes (no batch
mode, no embedding, no recover-and-continue), and testing needs a subprocess
instead of a function call.

**Why this is not a style preference.** ADR-043's R14a already fixed exactly
this for two policy loaders, with this reasoning: *they `sys.exit`-ed two frames
below a gate table whose stated contract is "gate fns return a refusal string."*
The argument is correct and was not applied to `run_intake_stage` itself — the
function that enforces the contract breaks it, one frame up.

**Scope.**

- `run_intake_stage(stage, ctx)` returns `refusal_string | None`; it stops at
  the first refusal exactly as now.
- Its two call sites in `build_claim_payload` exit on a non-None return.
- `shellio`'s ten exits become returns where the caller can act on them. Where
  a caller genuinely cannot (no git repo at all), leave the exit and **write
  the reason in a comment** — an undeclared exception is the defect; a declared
  one is a decision.

**Out of scope.** `cli`'s 54 exits. `cli` is the shell; exiting is its job.

**Acceptance.**

1. `diff instruments/fingerprint-baseline.txt <(./instruments/fingerprint.sh)`
   — empty. Every refusal message and exit code byte-identical.
2. Canary arm count **unchanged**. A delta means the refactor changed
   behaviour; stop and report rather than updating the arm.
3. Core suite green with **no test edited**. If a test needs changing, that is
   the same signal — report it, do not absorb it.
4. New: one test proving `run_intake_stage` returns rather than exits — call it
   directly with a ctx that trips a gate and assert on the returned string.

**Falsifier.** Any refusal that reaches a user through a different path, or in
different bytes, than before.

---

## S1b — A2: split `advisory`, by criterion

**The finding.** 932 lines, 25 functions, at least four concerns: advisory
assembly, git-output parsers, the pure report family, and `dispatch_text` —
which builds the verifier's G11 envelope with an integrity hash and terminator.
That is a **trust boundary**, not advice.

The module docstring says "advisory assembly and the pure report family". The
word *family* is the tell: it is a collection, not a criterion. Compare the
rest, where the criterion is one sentence — `registry`: it is vocabulary.
`kernel`: it is a fold or the mirror. `evidence`: it is a screen or a recipe.
`policy`: it is a refusal. `advisory`: *none of the above.*

A module defined negatively is where the next drift lands, and one already has:
`reaffirm_cleared` is written in `cli` and read — as a bare presence boolean —
in `advisory`, with its contents read by nothing.

**Scope.** Minimum viable split, in priority order:

1. `dispatch_text` → its own module. Different concern, different risk class.
2. Reports (`stats_report`, `queue_rows`, `impact_report`, `baseline_*`,
   `inverse_report`, `staling_report`, `blast_report`, `override_report`,
   `separation_report`, `retraction_cause_report`) → `reports`.
3. What remains in `advisory` must be describable in **one sentence**. Write
   that sentence in the docstring. If you cannot, the split is not finished.

**Constraints.**

- Pure file moves and imports. **Zero logic edits.** ADR-044's licence,
  reused verbatim.
- The DAG must stay acyclic and `TestModulePurity` must keep passing without
  its allowlists being widened.
- `docs/structure.md` **must be redrawn**, and
  `TestStructureDocMatchesDisk` will fail you until it is — that is the test
  doing its job, not an obstacle. It checks the diagram names exactly the
  modules on disk, that every drawn arrow is a real import, and that the drawn
  DAG's reachability equals the real one.

**Acceptance.** Fingerprint empty diff · canary arm count unchanged · core
green with no test edited except the structure test's *expected* side, which is
the diagram, not the assertion.

**Falsifier.** A function that ends up in a module whose one-sentence criterion
does not admit it.

---

## S2 — A4: `main()` becomes a table

**The finding.** `cli.py` is 1702 lines; `main()` is 348 of them, a flat
argparse declaration for ~20 verbs, hand-copied. ADR-043's R7 already found one
real bug here — `done --claim` silently lost `--json` — and fixed it for *one*
shared flag group (`add_claim_intake_flags`). The rest is still hand-copied,
and `--refresh-evidence` was added by hand a week ago.

**Scope.** Apply the trick the codebase already uses in `INTAKE_GATES`:
declaration as data. A verb table of `(name, help, flags, fn)`, with shared
flag groups declared once and referenced.

**Constraints.**

- `truth <verb> --help` output byte-identical for every verb. Capture before
  and after with a loop; that is this brief's own fingerprint.
- Flag order within each verb preserved — argparse renders in declaration
  order and the help text is a user-facing surface.
- Do not "improve" any help string. Not this brief.

**Acceptance.** Fingerprint empty diff · all `--help` outputs identical ·
canary unchanged · core green with no test edited.

**Falsifier.** A flag that exists on one verb before and not after, or a help
line that moved.

---

## S3 — A3: retire the entry-point mirror

**The finding.** `scripts/truth` installs `_MirrorModule.__setattr__`, which
walks eight modules on every attribute assignment, and `_self_module()` uses
`gc.get_referrers` to find its own module object. This exists solely so the
suite's `tm.ledger_path = ...` monkeypatching survived the ADR-044 package
split.

That was a **good decision at the time** — preserving 100% of the old corpus
was the equivalence proof for the split. But the migration is over, the proof
is delivered, and the hack is still in the production loading path.
`gc.get_referrers` there is the kind of thing that breaks on a Python upgrade
and produces a failure nobody can read.

**Scope.** Replace the monkeypatch seam with an explicit one — a `configure()`
entry, or injection of the paths the tests currently patch. Then delete
`_MirrorModule` and `_self_module`.

**Constraints.**

- `SourceFileLoader("truth", "scripts/truth")` compatibility is a **shipped
  contract** (ADR-044) — consumers and suites load it that way. It must survive.
- No install step, no dependencies, copier-copyable. Those are the properties
  that made the thin entry right; the hack is not one of them.

**Acceptance.** Fingerprint empty diff · core green · `scripts/truth` contains
no `gc` import · loading works under all three styles the current docstring
names (as `__main__`, via `load_module`, via `spec/exec_module`).

**This brief may edit tests** — uniquely, because the seam *is* the test
surface. That makes it the highest-risk brief and the reason it runs last, with
the fingerprint as the only unbendable check.

---

## V1 — Adversary *(fresh session; never an implementer)*

Given the diffs and nothing else:

1. **Hunt dark arms.** Any new assertion that matches both the pass and the
   fail line. This is the AL2 class, it has already occurred here once, and it
   occurred twice in the fingerprint's own first draft.
2. **Attack the fingerprint itself.** Find a behaviour change it does not
   catch. A hole here is worth more than a hole in any brief, because it is the
   instrument the other briefs were accepted against.
3. **Check the exception list from A1.** Every remaining `sys.exit` in
   `shellio` must carry a stated reason. An undeclared one is the finding.
4. **Check A2's criterion.** Read each new module's one-sentence docstring, then
   read its functions. Name any that the sentence does not admit.

Every finding reproduced **live in a sandbox against the real CLI**, never
argued abstractly.

---

## V2 — Equivalence *(fresh session)*

Independently, without reading the briefs:

1. Regenerate the fingerprint on the base commit and on the result. Confirm the
   diff is empty.
2. Confirm the canary arm count is unchanged across all four briefs.
3. Confirm no test file was edited except `docs/structure.md`'s diagram (S1b)
   and the seam tests (S3). **Any other test edit is a finding**, not a detail.
4. Re-run the four seeded mutations from §0 against the refactored tree and
   confirm the fingerprint still detects all four. A refactor that makes the
   instrument blind is worse than the defect it fixed.

Step 4 is the one that matters most and is easiest to skip.

---

## A5 — Documentation *(mine, not delegated)*

How many times an evidence command runs now has no single documented answer:
twice at intake (the G6 double-run), once on a manual `agree` for a path-claim
(ADR-051, which I added), once on `--recheck`, once per `reaffirm` pass. One
table in the machinery doc. I introduced the third execution and I will
document it.

---

## What is deliberately not delegated

**The ADRs.** Each of A1–A4 deserves a record, and an ADR is an *argument*. An
argument written by an agent is precisely the substance that leaks across
session boundaries — the failure class this entire body of work exists to
close. Write the decision; delegate the diff.

**Any judgement about whether a residual is acceptable.** If a brief hits a
case where preserving behaviour and fixing the defect conflict, the answer is
to stop and report, never to choose. That choice is an ADR.
