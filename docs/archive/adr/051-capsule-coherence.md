# ADR-051: an agree carries the capsule with the anchor

Status: Accepted (2026-08-09, operator) — prompted by an independent audit of
the kuchnie ledger (2,182 records, 221 claims, HEAD `571d1b4`) run with a
reimplemented fold rather than `truthlib`, which found 13 of 126 live claims
carrying an evidence capsule that no longer reproduces. Implemented in CLI
v0.9.36, schema `$id` v0.18. Core tests `TestCapsuleCoherence` (19); canary
FAULT EF (5 arms incl. a negative control); end-to-end
`scripts/test-adr051-e2e.sh`.
Date: 2026-08-09
Extends: ADR-012 (the mechanical/genuine split, applied to the AGREE side —
this is that ADR's twin, and the argument below is its argument), F2 (the
effective anchor, whose purpose is preserved and whose side effect is
closed), ADR-030 (reaffirm's hash-match arm, which this restores access to),
ADR-009/029 (the screen gates execution — the gate's single run goes through
it), ADR-046 (envelope admission: `effective_evidence()` is the reader that
admits the field), ADR-049 (the refusal-vs-advisory test, applied verbatim).
Cites: ADR-026 (`$id` v0.17 → v0.18 — the verdict shape changed), ADR-027
(the cross-field rules are mirror-only), ADR-016 (the refresh reader walks
fold order, never file order).
Supersedes: —

## Context

F2 gave a re-verified claim an **effective anchor**: an `agree` on a
path-carrying claim stamps `anchor_commit = HEAD`, so the next scan diffs from
there and the claim stops re-staling against a frozen base. That fixed a real
problem and is unchanged here.

What went with it was never decided, only omitted. The evidence capsule —
`command`, `output_hash`, `returncode` — lives in the **claim** record, which
is first-wins immutable (ADR-006, for good reason). So the anchor moves and
the capsule does not. Nothing in the system ever asked whether they should
move together.

The consequence is not cosmetic. Once a watched change alters the command's
output, an `agree` filed over it leaves a claim that is:

- **`live`** — it reads as current, in `list`, in `queue`, in `ready`;
- **permanently un-recheckable** — every later `verdict --recheck` compares
  against a hash nobody can produce and auto-files `diverge`;
- **outside reaffirm forever** — the hash-match arm (ADR-030), which exists to
  absorb the regime's dominant operating cost, can never take it back.

And the verifier protocol closes the loop: `prompts/truth-verifier.md` step 1
says run `--recheck` first and *"if the recheck diverges, you are done"* — so
the next verifier stops **before** step 2, the step that would have read the
sentence. A human's correct judgment is undone mechanically, by protocol,
without a second judgment.

**Measured on the kuchnie ledger before the gate:**

| | |
|---|---|
| live claims with paths + a capsule | 102 |
| anchor advanced past a commit touching their own watched paths | 70 (69%) |
| capsule confirmed non-reproducing in a clean clone | **13** |
| retractions that had passed through the shape | **10 of 77 (13%)** |
| claims that ever diverged and came back to live | **1** |

That last row is the shape of the trap: ADR-020 declares `diverged`
recoverable and in practice it is terminal.

## The missing vocabulary, and why it is ADR-012's

ADR-012 split `diverged` because it conflated two facts: *reality changed*
versus *the measuring recipe changed while the fact held*. `agree` carries the
identical conflation and had no vocabulary for it — "the evidence reproduces
AND supports the sentence" and "the evidence no longer reproduces but I judge
the sentence still holds" file the same record.

The ledger shows humans hitting the second case and writing the reason in
prose, because there was nowhere else to put it:

> *"The recipe uses grep -n, so the schema_version field ..."* — the last
> agree on `tr-0ba0f782`, which is now an orphan.

That is the unrecorded-judgment shape ADR-049 measured at 65% of retraction
bases, appearing again. The information was known, correct, and unstructured.

## Decision

**An `agree` may not advance an anchor past a capsule that no longer
reproduces, unless the verifier states why.**

1. **The gate.** On a manual `agree` for a claim carrying `evidence_paths` and
   a capsule command, the shell screens the command (ADR-009/029, the same
   screen — a second implementation is forbidden) and runs it **once**. The
   pure predicate `capsule_coherence_error` decides:
   - output and returncode match the effective capsule → pass, silent;
   - they differ → **refuse**, unless `--refresh-evidence "<sentence>"`.

   The refusal names **both** exits — refresh if the sentence holds, `diverge`
   (`--mechanical` if only the recipe drifted) if the fact moved. A gate that
   teaches one exit funnels honest divergences into agrees.

2. **The field.** `--refresh-evidence` stores
   `evidence_refresh: {output_hash, returncode, basis}` on the **verdict**
   record — never by editing the claim, whose immutability closed a real
   attack (ADR-006). It records an **act**: the capsule this session actually
   observed, plus the judgment.

3. **The reader.** `effective_evidence(capsule, refresh)` returns the claim's
   capsule with hash and returncode overridden by the newest refresh, found by
   `latest_evidence_refresh` in **fold order** (ADR-016 — a reader keying off
   append order disagrees with the fold on a union-merged ledger, the ADR-050
   lesson). Both `--recheck` and `reaffirm` compare against it. This function
   is what admits the field under ADR-046's envelope rule; without a consumer
   the field would be decoration and must not exist.

4. **Abstentions, each for a stated reason.** No `evidence_paths` (no anchor
   advance, so no capsule can fall behind); no capsule command; command
   unscreenable or unrunnable (`--recheck` cannot execute it either, so there
   is no freshness to protect). A `--refresh-evidence` in any of those
   positions is refused as a basis with nothing to excuse — the ADR-035 `X5`
   symmetry.

**Refusal, not advisory** — ADR-049's three-part test, applied:

- **Volume** is low: a *mismatching* manual agree, not every filing.
- **Decidability** is total: two hashes. It cannot produce a false refusal, so
  it cannot teach its own bypass — the ADR-014 confused-deputy objection that
  made ADR-037's lints warnings does not reach it.
- **The convention equivalent is measured to fail:** ADR-012's `--mechanical`
  exists on the diverge side and was used 6 times in 99 diverges; the agree
  side recorded nothing at all, 13 times.

**Decay: declined, with reason** (the ADR-032 exclusions form). A refresh
records an observation at an instant; nothing later re-asks it, and the next
drift re-fires this gate anyway.

**Counted** in the ADR-033 override report as `evidence_refresh_filings`
(CC-2, single home). It is the gate's own health metric: a rising count means
recipes are drifting faster than the facts they measure — a signal to re-file
recipes, not to widen the gate.

## The behaviour change, stated plainly

**A manual `agree` on a path-claim now executes the evidence command once.**
That is new, and it is the price of the gate's decidability.

The alternative was considered and rejected: the orphaning condition is
detectable from git alone (has the anchor advanced past a watched change?),
with no execution. But roughly half of such advances leave the output
unchanged — that is the entire premise of reaffirm's hash-match arm, 263
instances in the pilot — so the structural test would refuse ~50% falsely.
That would destroy the "cannot produce a false refusal" property, which is the
only reason this may be a refusal at all. Accuracy costs one screened run.

Bounded: only `agree`, only path-claims, only screenable capsules — and the
verifier prompt already mandates `--recheck` before agreeing, so the command
was going to run anyway.

Canary FAULT L is where this surfaced, and its own fixture is an instance of
the class: it appends a line to a file watched by `wc -l`, so the count grows,
the sentence ("multiple lines") still holds, and the arm now carries the
capsule with the anchor instead of leaving it behind.

## Verifier protocol

`prompts/truth-verifier.md` gains two clauses:

1. Step 1's stop rule is qualified: if the recheck diverges **and** the claim's
   anchor has advanced past its own watched paths, the divergence may be
   capsule orphaning rather than a fact change — continue to step 2 rather
   than stopping.
2. A new reproducibility question: state whether the evidence could be
   reproduced by another person on another machine. If not, that is
   `cannot_verify` unless the claim is explicitly a TTL attestation with no
   watched paths.

Clause 2 is not decorative. `tr-8ed0a7ff` asserts a path under
`/Users/michal/...`, is `live`, and carries **three** independent agrees —
every one from the one filesystem where that path exists. ADR-010 compares
session strings and cannot see that the environment is a constant.

## Consequences

The mechanical re-confirmation path stops closing behind every human rescue.
Before this, each hand-repaired claim became permanently hand-only, which is
why `human_agree` (293) outran `mechanical_agree` (263) in the pilot despite
reaffirm shipping.

**Legacy tolerance is permanent, not transitional.** Absent
`evidence_refresh` stays valid forever: every pre-ADR-051 verdict lacks it,
history is append-only, and `validate` runs *inside* the commit gate — a
mirror that refused history would wedge every consumer repo permanently
(ADR-049's reasoning, unchanged). Intake stricter than validate is the safe
direction.

**The existing 70 drain naturally.** Each passes through a human
`agree --refresh-evidence` at its next staling and leaves the class. A bulk
refresh script is forbidden: it would be exactly the judgment-laundering
ADR-030 declines, and would convert 13 visible orphans into 70 unexamined
refreshes.

**Cost:** one screened execution per manual agree on a path-claim; one new
flag; one optional verdict field; `$id` v0.18 with the mirror and the
shape-fingerprint pin moved in the same diff (ADR-026).

## Non-goals — residuals owned

Not identity, not environment verification: clause 2 of the prompt asks a
human to judge reproducibility; nothing enforces it. The mechanical form is
running `truth reproduce` (proposed separately) in CI, where a different
machine makes the question answer itself.

Not a claim that the capsule now always reproduces. It reproduces as of the
last refresh; the next drift re-fires the gate, which is the intended loop.

Not a fold change, not a status change, not a new record kind.

Not retroactive: existing orphans keep their state until a human touches them.

## Adoption gate (ADR-047)

**Metric:** `evidence_refresh_filings` in the override report, and the
`capsule-stale` population (`truth reproduce`, once it ships).
**Data source:** `instruments/override-velocity.py --json`.
**Next review:** 2026-11-09, in the R11 monthly slot.
**Retirement test:** if `evidence_refresh_filings` stays at zero across two
consecutive reviews **and** no capsule-stale claim appears, the drift class
this gate names is not occurring in the field and the gate drops to an
advisory. If instead refreshes dominate agrees, the finding is about recipe
quality (ADR-037's territory), not about this gate.

**Falsifier:** a claim that reports `capsule-stale` after a successful
`--refresh-evidence` — i.e. the refresh failing to do the one thing it exists
to do.
