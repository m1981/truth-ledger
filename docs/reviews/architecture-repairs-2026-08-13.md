# Architectural repairs — agent briefs

Findings A1–A5 from the 2026-08-13 architecture review. Written so an
independent agent can execute one brief per session, and a different agent can
verify it, per ADR-010's own rule: the session that writes an arm never
verifies it.

---

## 0. The acceptance instrument — read this before any brief

`instruments/fingerprint.sh` drives the real CLI through **99 probes** covering
**all 23 verbs** — every intake gate that can refuse, the execution boundary,
the verdict surface, the work kernel, the tracker seam, and every exit code the
CLI emits (0–8) — and records `(exit code, stderr, stdout)` as one canonical
file. Ids, hashes, timestamps and abbreviated shas are normalised; both the wall
clock and git's clock are pinned, so the output is byte-deterministic across
runs, and two runs may execute concurrently without disturbing each other.

**That sentence was false until wk-24db9abe, and how it was false is the
warning.** It read "every refusal path … every intake gate … every non-trivial
exit code" while **8 of the 23 verbs had no probe at all** (`ready`, `baseline`,
`dispatch`, `stats`, `queue`, `issues`, `invalidate-scan`, `reaffirm` — plus
`list`, which the instrument *used* to find a claim id but never recorded, so
nine verbs were unrecorded and only eight were unexercised). Exit codes 4 and 7
were emitted by no probe. The ADR-037 generated-artifact refusal was unreachable
because the sandbox committed an EMPTY `.truth/generated-paths`, which SI-4
reads as "consciously nothing is generated". And the tracker refusal in
`shellio.tracker_issues` — moved there by a refactor whose own commit message
certified *"the refusal strings are unchanged"* **against this instrument** —
could have any word replaced with an empty diff.

None of those verbs were forgotten in a hurry; each was omitted because it
needed sandbox state (a stale claim, a committed ledger, a tracker) that the
instrument did not build. **The cost of a probe is the reason the gap forms,
and a coverage claim written from intent rather than from a count is how it
survives.** The count above is `grep -c '^probe ' instruments/fingerprint.sh`;
the verb list is the subparsers in `cli.main()`. Check both rather than
believing this paragraph.

```bash
./instruments/fingerprint.sh > /tmp/after.txt
diff instruments/fingerprint-baseline.txt /tmp/after.txt    # MUST be empty
```

**Why this exists, and why "the tests pass" is not the acceptance criterion.**
For a refactor the tests are the thing an agent can bend to make green. ADR-044
got this right: its acceptance was *the old corpus unchanged*, and any arm-count
delta meant the phase had exceeded its licence. The fingerprint generalises
that to observable behaviour.

### Re-prove it here before you trust it

The four mutations below were run and detected during authoring, in a
throwaway clone. **That is a result you cannot check, so do not take it.** Run
this first, in your own tree, and read the table as the expected output of
your own run rather than as a finding of mine:

```bash
bash instruments/reprove-fingerprint.sh
```

It seeds each mutation, runs the fingerprint, restores, and prints DETECTED or
MISSED per row. Expected:

| seeded change | expected |
|---|---|
| two `INTAKE_GATES` rows swapped | DETECTED |
| `CITATIONS_EXIT_CITED` → `1` | DETECTED |
| one word changed in a refusal message | DETECTED |
| one CC-1 advisory line dropped | DETECTED |
| nothing (control) | IDENTICAL |

**Any MISSED means the instrument is blind for that class and no brief below
may be accepted against it.** A MISSED on the control means the fingerprint is
not deterministic in your environment — report that before anything else.

Note how the guard actually fires, because it is not where you would expect:
blinding the instrument (deleting a probe) shifts every later probe, so the
**control** goes non-IDENTICAL before the seeded row goes MISSED. Either way
the script refuses, but read the control line first — it is the arm that
catches tampering with the instrument itself.

Those four rows prove four **classes** are visible. They do not prove any
particular probe can fail, and that gap is exactly how eight verbs stayed
unprobed while this table read PROVEN. So the verb sweep has its own harness:

```bash
bash instruments/reprove-verbs.sh    # 28 rows, all must read DETECTED
```

It seeds one mutation per appended probe block — the tracker refusal, the
ADR-037 refusal, `events_at_ref`'s exit 2, `baseline`'s exit 5, `reproduce`'s
exit 7, `impact --inverse`'s exit 4, each `reaffirm` arm, the `queue` reason,
the E1 `--ready-json` contract, the G11 envelope header, and the rest — and
distinguishes MISSED (the probe cannot fail) from SEED FAILED (the mutation
never landed, which is evidence about nothing at all).

**The instrument's own first draft missed two of the four**, which is why this
step is mandatory rather than advisory. The order probe was tuned to Jaccard
0.556 — *below* G8's 0.6 threshold — so G8 never fired and the order of the
two gates was unobservable. And no probe reached the `cited` branch of
`citations`, so the only non-trivial exit code in that file was never
exercised. Both are the dark-arm class: an arm that cannot report a miss.
**Assume your own new arms have this defect until a seeded mutation proves
otherwise.**

### Declared coverage limits of this instrument

Written because a reviewer asked whether `doctor`'s absence from the probes was
scope or oversight. It was oversight — twice, at two different scales: `doctor`
first, then the eight verbs above. Both times the gap was found by someone
mutating the code, never by reading the instrument. So this list is maintained
as the thing you check BEFORE certifying anything against a clean diff. **Every
verb is now driven; no verb is exhaustively driven.** What is still dark, after
wk-24db9abe:

- **Verb coverage is not branch coverage.** The whole work kernel is probed
  through refusals and two filings: **no issue is ever started or closed**, so
  `start`, `done`, `done --claim` (claim-at-death), `--cancel` (G12), `--reopen`
  and the entire ADR-014 acceptance-oracle path — screened, executed, refused on
  non-zero exit — have no successful execution anywhere in this file. Likewise
  on the verdict surface: `agree` is filed three times, but **`diverge`,
  `diverge --mechanical`, `cannot_verify` and `retracted` never succeed**, so
  the `diverged`/`disputed`/`retracted` statuses, the ADR-049 `--cause` arms and
  `--successor` are pinned only by their refusals. `contradicts` never
  completes, so DISPUTED is unreachable and `queue`'s disputed and diverged
  reasons are unprobed (its stale-P0 reason is). `premise --supersedes` (the
  ADR-013 redirect) is pinned only by its bad-id refusal.
- **Arms the pinned clock makes unreachable.** `TRUTH_NOW` is frozen, so **no
  TTL ever expires**: `invalidate-scan` only ever reports `paths changed` (never
  the TTL or anchor-lost reasons), and `reaffirm`'s `ttl` arm is dead. Its
  `manual` arm is reached only through *never agreed*, not through
  `evidence.screened=false` or a missing command. This is the ADR-032/ADR-019
  decay machinery: real, and unpinned here.
- **Only reachable branches, generally.** The `doctor` probe runs after claims
  have been filed, so its `ledger exists` FAIL branch is dead. The sandbox has
  no hooks and no CI, so the commit-gate banner is always the *not wired* arm —
  **the wired arm is unprobed**, in an instrument whose own baseline carries
  that banner on 51 lines. A mutation on a dead branch reads as MISSED, and that is the
  instrument being honest, not broken — but "the fingerprint is empty" has never
  meant "every branch is pinned".
- **ADR-037 has three loader states and this pins two.** `.truth/generated-paths`
  is committed-EMPTY for the first 68 probes (`source='empty'`) and armed with a
  real glob after (`source='file'`, which is what makes the refusal and the
  `--generated-ok` override reachable at all). **`source='absent'` — no file, the
  state that drives the "the generated check is dark" advisory — is unprobed**,
  because the sandbox always writes the file.
- **`--json` twins are pinned for 9 verbs, not for all.** `list`, `issues`,
  `ready`, `queue`, `stats`, `baseline`, `reaffirm`, `reproduce` and `doctor`
  have both arms. `citations`, `impact`, `staling`, `claim`, `verdict`, `issue`
  and `done` have only the human arm; `validate --stdin` is unprobed entirely.
  `staling` is probed over an EMPTY population only, so the ADR-050 split it
  exists to report — and its `--since`/`--append-order` flags — is unpinned.
- **Windowed reports are pinned only at their edges.** `stats --since` uses a
  timestamp that filters EVERYTHING, deliberately: a cut through the middle of
  the run would depend on how many probes preceded it, so appending a probe
  later would silently rewrite existing baseline lines and destroy the
  append-only property the next brief needs. The partially-filtered window, and
  `reproduce --since`, are therefore unprobed.
- **What `norm()` erases cannot be pinned.** Ids, hashes, timestamps and fold
  latency, plus two additions made for this work: git's own wording inside the
  `events_at_ref` exit-2 refusal (`<GIT-ERR>` — git has reworded it across
  releases, and leaving it raw would fingerprint the reviewer's git version),
  and abbreviated shas in `baseline` (`<SHORT>`). A change to HOW truthlib
  interpolates git's stderr into that line is invisible; the prefix, the ref and
  exit 2 are pinned.
- **A live defect in `norm()`, declared rather than fixed.** The rule
  `s/\b[0-9a-f]{40}\b/<COMMIT>/g` **is a no-op on macOS**: BSD `sed` has no
  `\b`. The committed baseline therefore carries two RAW 40-hex commit shas (the
  `head` field of `reproduce --json`). It is not a determinism fault — the
  sandbox pins both git dates, so its commit shas are a pure function of its
  tree — but the same instrument normalises those lines under GNU sed and not
  here, so a baseline generated on Linux and one generated on macOS disagree for
  a reason that has nothing to do with truthlib. **Repairing it rewrites two
  existing baseline lines, which wk-24db9abe's append-only acceptance forbade.**
  The rules added for the new probes are keyed to their own fields
  (`anchor_commit`, `commit`) so no third leak was introduced. Whoever fixes the
  `\b` rule owns a non-append-only baseline regeneration and must say so.
- **Not the canary, not the suites.** The fingerprint pins the CLI's observable
  surface. Test-count and arm-count regressions are a separate acceptance
  criterion and must be checked separately.
- **Not concurrency of the SYSTEM, though the instrument is now concurrency-
  safe.** Each run spools per-probe stderr to its own `mktemp` (it used to write
  a hardcoded `/tmp/fp.err`, so two runs — the ordinary shape of `diff
  before.txt after.txt`, and of any agent fleet — clobbered each other; measured
  at 83 and 114 wrong lines with a two-second offset, including a torn read of a
  half-written refusal). What is still unprobed is the system under test:
  ADR-045's ledger lock is never contended, because every probe is one process.
- **Not multi-machine.** Single sandbox, one platform per baseline.
- **Not performance.** Fold latency is normalised away deliberately; a refactor
  that makes the fold ten times slower passes the fingerprint clean.

## 0b. Numbers in this document, and where they were measured

The figures this document was FIRST written with — `354 tests`, `273 caught,
1 missed`, the four DETECTED rows — were measured **in an ephemeral
container**, on a clean clone of `8fa0706` with this series applied. Not on
the maintainer's machine, and not in the repository you are reading this in.
They have since been replaced by the table at the end of this section, which
was measured here; the originals are kept below only because the gap between
them is the lesson.

That is a pattern worth naming rather than patching case by case, because it
has now occurred three times in this work:

1. §0's red-proof table was originally written in the past tense about a file
   that did not exist in the repository — a plan described as a result.
2. `273 caught, 1 missed` is quoted as an expected value. Measured on the
   maintainer's macOS at the same commit: **274 caught, 0 missed**.

   The first diagnosis offered for that gap — that the canary's count is
   *branch-dependent*, so `286 ok(` call sites resolve to 273 — does not
   survive arithmetic, and the correction matters more than the original
   claim. **The totals are identical: 273 + 1 = 274 + 0 = 274.** Branch
   dependence would move the TOTAL; here the total is fixed and only the
   split moves. Both arms named as evidence (`FAULT D1`, `FAULT R`) are
   plain if/else pairs, each contributing exactly one to PASS *or* to
   FAIL, so neither can change the total at all.

   So this is not a counting artifact. **UM4 genuinely fails in a Linux
   container and genuinely passes on macOS** — an environment-dependent
   test outcome, which is a finding about UM4 (it presumably needs git or
   filesystem behaviour the container lacks) and is worth its own
   investigation rather than a footnote.

   The sharper rule that follows: quote **both** numbers, always. The
   total is the invariant — it changes only when arms are added or
   removed. The split is the signal — it changes only when an arm's
   OUTCOME changes, which is always either an environment finding or a
   regression, and never noise.

3. A third instance, found while landing this series, and the most
   expensive of the three because the number was *plausible*: the canary
   read `282 caught, 1 missed` (FAULT TG6) on the maintainer's tree while
   a clean worktree at the same commit read `283 / 0`. The cause was not
   the environment and not a regression — `reprove-fingerprint.sh` had
   been interrupted by a closed pipe and had left one of its own seeded
   mutations (`CITATIONS_EXIT_CITED -> 1`) in `cli.py`. The instrument
   that certifies the refactor had silently broken the tree it was
   certifying. Fixed in the same series (rollback trap); recorded here
   because the lesson is the rule above: the split moved, so an arm's
   outcome had changed, so something real was wrong — and adjusting the
   number would have buried it.

**The rule this establishes.** A number produced in a throwaway environment is
not a fact about the repository — it is a *prediction* about what the
repository will report. State it as an expected value with the command that
produces it, never as a finding. Where the number could vary by environment,
say so.

Concretely, for this document: every figure below is the **expected output of
your own run**, with the command that produces it. If one differs, that is
information about your environment or about a real regression — report it
before proceeding, and do not adjust the number to match.

| expected | command |
|---|---|
| `Ran 382 tests` `OK`, 0 skipped | `cd template && PYTHONPATH=~/.cache/truth-ledger-pylib python3 scripts/test-truth-core.py` |
| `283 caught, 0 missed` | `cd template && bash scripts/truth-canary.sh` |
| `SENSITIVITY PROVEN`, 50 probes | `bash instruments/reprove-fingerprint.sh` |

Measured on macOS at the tip of this series, in a **clean tree** — run
`git status` first, because a dirty one has already produced a false canary
number here once (item 3 above). The core suite needs `PYTHONPATH` pointing
at the local jsonschema cache; without it the run is not wrong, it is
*narrower* — three schema tests skip and the suite still says `OK`, which is
the same silent-green shape this section is about.

This is the same defect the ledger itself catches at the claim layer (an
attestation nothing can re-run) and the same one the atlas hit (a count that
had moved). It reaches documents too, and documents have no invalidation scan.

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
