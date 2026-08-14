# A6 — the arm index: make 781 arms answer "what do you guard?"

> Reader: an agent executing this brief, or the operator deciding whether to
> commission it | Enables: asking which arms guard a given ADR, and failing an
> arm that guards nothing nameable | Update-trigger: the arm inventory or the
> `FAULT X (SUBJECT):` convention changes

Written in the same form as `architecture-repairs-2026-08-13.md` (A1–A5) and
executable by the same rules: one brief per session, the session that writes
an arm never verifies it (ADR-010), stop and report rather than choose when
preserving behaviour and fixing a defect conflict.

**This brief is deliberately sequenced AFTER A1–A5.** A2 splits `advisory`
and A4 rewrites `main()`; an arm map drawn before them would have to be
redrawn after, which is precisely the cost this brief exists to remove.

---

## 0. Numbers, and where they were measured

Measured on macOS at `0a4a38f`, with the command that produces each. Treat
them as the expected output of your own run (§0b of the A1–A5 brief); if one
differs, report it, do not adjust it.

One row has been re-measured since, and it is named here rather than quietly
swapped: **the fingerprint went from 50 probes to 99** under wk-24db9abe,
which closed the eight verbs it had never driven. That is a deliberate
increase with its own commit, not drift — which is exactly the distinction
this table exists to make visible.

| measured | command |
|---|---|
| 283 canary arms | `cd template && bash scripts/truth-canary.sh` |
| 382 core + 13 v04 tests | `cd template && PYTHONPATH=$HOME/.cache/truth-ledger-pylib python3 scripts/test-truth-core.py` |
| 23 instrument arms | `bash scripts/test-instruments.sh` |
| 11 or 12 battery meta arms | `bash scripts/test-release-battery.sh` — **environment-dependent, see below** |
| 10 / 5 / 3 arms | `test-fact-health.sh` / `test-whisper-hook.sh` / `test-session-digest.sh` |
| 99 fingerprint probes | `bash instruments/fingerprint.sh \| grep -c '^=== '` |
| 122 FAULT headers, **90 citing an ADR/INV/G** | `grep -E '^say "FAULT ' template/scripts/truth-canary.sh` |
| 125 distinct FAULT labels | `grep -oE 'FAULT [A-Z][A-Z0-9-]*' template/scripts/truth-canary.sh \| sort -u` |

**≈830 arms across nine instruments** (≈781 before the fingerprint's +49). The battery meta count is 11 with
`jsonschema` importable and 12 without, because ARM 4 asserts that a missing
`jsonschema` blocks with exit 2 and cannot be exercised on a machine that has
it. The arm says so in its body; the summary line does not.

## The finding

The machinery has three structural levels. Two are pinned mechanically. The
third does not exist.

| level | nodes | pinned by | can a human hold it? |
|---|---|---|---|
| modules | 8 | `TestStructureDocMatchesDisk` — both sides derived at run time | yes |
| checks (files) | 13 | `gate-reachability.sh` — transitive closure from roots | yes |
| **arms** | **≈781** | **nothing** | **no** |

There is no mechanical link from an arm to what it guards. "Which arms guard
ADR-051?" is answerable only by grep. When an ADR changes, nothing says which
arms must move with it — and when an arm stops guarding what its name claims,
nothing notices.

**This is not hypothetical, and it is not cheap.** Three defects of exactly
this shape were found in one session (2026-08-13/14):

1. **Three ADR-011 arms were dark.** `FAULT H1`, its `done --cancel` twin and
   `RX3B` assert the HEADLESS refusal but did not redirect stdin. From a
   terminal the CLI took the interactive branch, blocked on `input()`, and
   then reported CAUGHT on the typed-text mismatch — never on the rule the arm
   names. The miss text said "with no TTY" while a TTY was attached. Green for
   the wrong reason on every developer machine, correct only in CI.
2. **The atlas drifted from the thing it describes.** `docs/machinery-atlas.md`
   is hand-transcribed ("the facts were re-read from disk on 2026-08-03/04");
   it states "273 seeded faults, 1 known miss: UM4" where the measurement is
   274/0 at that commit and 283/0 today. The claim guarding it greps the
   literal `273` in the atlas and never compares it to the canary, so the
   sentence promises more than the capsule checks.
3. **Two seeded mutations missed, silently.** Both looked like proof. One
   patched `cmd_reaffirm` instead of `cmd_reproduce` (the same string appears
   twice; `.replace(..., 1)` takes the first). One inserted plain text where
   the test parses `<b>name</b>`. Nothing distinguishes "the arm held" from
   "the mutation never reached it".

Defect 3 is the general case: **red-proof is done by hand, and a hand-run
mutation that misses is indistinguishable from an arm that held.**

## Why the data already exists

This is the reason the brief is feasible rather than aspirational. The canary
already carries the subject in a consistent, parseable form:

```
say "FAULT DG (ADR-025): doctor decides the commit gate via CI when no hook exists"
say "FAULT B  (INV-C):   commit touching evidence paths must mark the claim stale"
```

**90 of 122 headers (74%) already name an ADR, an invariant, or a G-number.**
The remaining 32 are a finite, nameable backlog — the same shape as F1.4's
payload fields without a reader, applied to arms.

## Scope

`instruments/arm-index.py`, a meta-repo Tier C instrument (ADR-003 rule 2,
ADR-046 tiering: it sweeps THIS repo's instruments and is never shipped).

1. **Enumerate** every arm across the nine instruments: label, family, the
   instrument it lives in, `file:line`. Mechanically, from source — never a
   hardcoded list, for the reason F1.4 states: a fixed list lies the day a new
   arm ships.
2. **Extract the subject** from the family header (`ADR-nnn`, `INV-X`, `Gn`,
   `TL-n`, `Rn`).
3. **Emit the reverse index**: subject → the arms that guard it, with
   `file:line`. This is the view that does not exist today.
4. **FAIL on an arm whose family has no traceable subject.** Opt-out file
   `.truth/arm-subject-opt-out` under SI-4 with ADR-053's attestation rule:
   absent → loud warning; committed-empty → conscious, silent, and dated; a
   stale entry (a family that has since acquired a subject) → also a failure.
5. **FAIL on zero arms examined** (ADR-042 rule 2), with its own exit code.

## Constraints

- **Parse, do not execute.** The index must not run the suites; it reads
  source. An index that costs 10 minutes will not be run.
- **The four species stay distinguishable** in the output, because they are
  not the same kind of thing and conflating them is half the cognitive load:
  seeded-fault arms (canary, 283), unit tests (core+v04, 395), meta-arms
  (`test-*.sh`, ≈53), and behavioural probes (fingerprint, 99 — which assert
  nothing and are compared as a whole file).
- **Do not rename the 125 FAULT labels in this brief.** The duplicates and
  collisions are real (`FAULT AN1` beside `FAULT AN1-AN5`, `FAULT SD` beside
  `FAULT SD-`, and `FAULT R` meaning both a PATH-manipulation arm and the
  roadmap items R2–R11), but a rename touches every arm and would bury the
  index's own diff. File it as the follow-up it is.
- **Environment-dependent totals are reported, not hidden.** The battery
  meta-gate is 11 or 12 depending on `jsonschema`. The index must state the
  condition beside the count, per §0b's rule: the total is the invariant, the
  split is the signal.
- Stdlib only, `--json`, and a rollback trap if it ever writes anything —
  three instruments in this repo have now been caught leaving state behind on
  an interrupted run.

## Acceptance

1. `python3 instruments/arm-index.py --json` emits every arm with its
   instrument, family, species and `file:line`, and the reverse index.
2. The count per instrument **equals** what that instrument reports when run
   — derived on both sides, compared, no literal written down
   (`TestStructureDocMatchesDisk`'s rule, which is why that test is the model
   for this one).
3. The sweep FAILS on the 32 subject-less families at first run, and the
   failure names them. **That first red is the deliverable**, not a defect to
   suppress.
4. It does NOT fail on any family that already cites a subject — the two
   facts together are the sweep's own red-proof, exactly as F1.4's
   `reaffirm_cleared`/`blast_forecast` pair was.
5. Every new arm the brief adds is seen RED against a named seeded mutation
   before it is credited.

## Falsifier

An arm whose family header names ADR-051 while its body exercises something
else — reported by this index as guarding ADR-051. The index maps *declared*
subjects; it cannot verify that an arm does what its header says. That limit
must be written into the instrument's docstring as a **declared coverage
limit**, beside the fingerprint's own (four when this brief was written,
twelve since wk-24db9abe found that the instrument's stated coverage and its
actual coverage had diverged), rather than discovered later.

## What this deliberately does not do

- **It does not judge whether an arm judges well.** That stays red-proof, by
  hand, per arm. What changes is that you can now see *where* to run it.
- **It does not replace the atlas.** It supplies the inventory the atlas
  should have been generated from. Whether the atlas is then regenerated from
  it is a separate decision with a separate cost.
- **It does not touch the arms.** No arm is renamed, moved, or rewritten under
  this brief.
