# Candidate-adoption analysis — clean-room gold vs. the truth ledger

You are an architect-implementer deciding which of six externally-derived
mechanisms ("the candidates") to adopt into the truth-ledger artifact,
how, and how to verify each — and, just as importantly, **which NOT to
adopt and why**. Rejection with a named reason is a first-class outcome;
an adopt-everything result would itself be evidence you have not
analyzed. You inherit a heavily litigated design: your job is to extend
it without re-losing any argument it already won.

## Materials

Repository root: `/Users/michal/PycharmProjects/truth-ledger`.

- The candidates and their provenance: `docs/growth-gate/clean-room-convergence.md`
  (§Divergences — the ranked six; the appendix has each mechanism's full
  clean-room description including its own failure mode and countermeasure).
- The artifact: `template/scripts/truth` (v0.9.13; pure core banner ~line
  560 — decisions in the core, I/O in the shell), `template/CHANGELOG.md`,
  `template/docs/adr/` (read 007, 009, 012, 018, 030, 031 at minimum).
- Settled law: `docs/roadmap-v3.md` (governing constraints + do-not-do
  list — binding, not advisory), the gate-vs-queue decision rule in
  `docs/truth-ledger-operations-guide.md`, `docs/growth-gate/README.md`
  (what is demand-gated and must stay there),
  `docs/growth-gate/obligation-ledger-design.md` (the OTHER valid
  destination for a candidate — adoption there costs nothing now).
- The paper: `docs/truth-ledger-paper-v3.md` — §2 for the measured
  operating regime (~1.5% verification hit rate, sub-day half-lives,
  scope overreach as the dominant real failure), §8 for the ranked
  limits any adoption must not worsen.
- Environment: `PYTHONPATH="$(ls -d ~/.cache/truth-ledger-pylib)"`;
  `TRUTH_SESSION="adoption-analysis-$(git -C . rev-parse --short HEAD)"`;
  suites baseline **201 core / 13 v0.4 / 170 canary, all green** — the
  floor under every proposal.

## The candidates

- **C1 Interpretation-divergence test** — two LLM workers independently
  derive concrete I/O examples from a claim/requirement text; divergent
  example sets = detected ambiguity, attached as evidence.
- **C2 Requirement mutants** — evidence counts as discriminating only if
  it fails against an LLM-authored violation of the specific claim.
- **C3 Neighborhood consistency** — records compile to typed, unit-aware
  numeric claims + a shared-noun index; contradictions detected
  arithmetically or by narrow scenario-construction judgment.
- **C4 Expiring waivers, default-to-removal** — overrides/deferrals
  carry an expiry; on expiry the covered thing auto-enters quarantine
  rather than persisting.
- **C5 Forced-choice questions** — any question routed to a human ships
  with two defensible answers with visibly different consequences.
- **C6 Amendment-velocity tripwire** — an override/justification class
  amended N times per window triggers a "was this ever real?" review.

## Hard rules

- The roadmap's do-not-do list and constraint budget are **binding**.
  Any candidate whose honest implementation violates them is a REJECT or
  DEFER, never a "small exception."
- The paper's own rule stands: **a gate that needs a model is a review,
  not a refusal.** Any LLM-dependent candidate (C1, C2, C3's semantic
  half) may ship at most as a queue warning or a dispatch-time
  instrument in the current artifact — never as an intake gate.
- Nothing may worsen the measured churn (§2.2) without shipping its own
  countermeasure in the same batch. State the churn delta you expect,
  and how you would measure that you were wrong.
- Verdict discipline per candidate: **ADOPT-NOW** (serves the current
  solo regime at S/M effort), **BACKLOG** (serves it, but sequencing or
  evidence is missing — say which), **DEFER-TO-GATE** (belongs to the
  obligation-ledger design — write the amendment into that doc's file,
  one paragraph, no code), or **REJECT** (name the argument it re-loses
  or the constraint it breaks). An unanchored verdict is not a verdict.
- READ everything you cite; run nothing that writes to
  `.truth/claims.jsonl`; commit nothing.

## Method — perform ALL passes, in order

### Pass 1 — Fit analysis (all six)
For each candidate: which measured pain or named residual does it
address (cite §2/§8/ADR by name — "would be nice" is not a pain)? What
does it cost in mechanism surface, LLM spend, and operator attention?
Does an existing mechanism already cover 80% of it (check before
inventing — e.g., is C6 partially the existing `--scope-ok` rot worry;
is C4 adjacent to ADR-013 supersede or the loophole-map deferral idea)?
Then the verdict, with the one-sentence anchor.

### Pass 2 — Design sketch (ADOPT-NOW and BACKLOG only)
For each: where it lives under the pure-core/shell split (the decision
must be a pure function; I/O and LLM calls stay in the shell or in
dispatch); its placement under the gate-vs-queue rule, justified by
that rule's own predicate (irreversible? automated consumer? cheap +
field-validated?); record kinds/fields touched (schema AND stdlib
mirror — remember they are two independent implementations, FS-2);
the ADR it needs (next free number) and what it supersedes or amends;
version bump; the overengineering trap it deliberately avoids (name the
tempting bigger version and why not).

### Pass 3 — Implementation & verification plan (ADOPT-NOW only)
Per item, an acceptance contract a follow-up implementation agent could
execute without judgment calls:
- Unit tests for the pure decision (all arms), integration test in a
  sandbox repo, and **at least one canary fault with a negative
  control** — the mechanism must be shown able to fail (a seeded defect
  it catches, and proof the suite goes red when the mechanism is
  disabled).
- Suites: 201/13/170 floor, plus your additions; nothing removed.
- For any mechanism making or consuming a semantic judgment: the
  **calibration debt** it opens (false-positive rate, agreement rate)
  and the cheapest measurement that would pay it — do not ship the
  judgment without shipping its counter (the ADR-007 lesson: the
  quantifier gate shipped with its FP rate unmeasured and §10 still
  carries that debt).
- The red-team question a post-implementation adversarial pass must
  answer (one sentence per item — what abuse or laundering would YOU
  attempt against it?).
- Docs: which paper section, invariant row, loophole-map entry, and
  ops-guide paragraph the item obligates. An adopted mechanism that is
  not in the invariant table is not adopted; it is loose.

### Pass 4 — Portfolio check
Read your own output as a reviewer: does the adopted set cohere (no two
items solving the same pain twice, no item whose countermeasure is
another unadopted item)? Sequence the adopted items into batches sized
like roadmap Batches 1–3, state what the roadmap file gains (new items,
Backlog changes), and state explicitly what you chose NOT to do and
what evidence would reopen each rejection. If everything landed in
ADOPT-NOW, or everything in REJECT, explain why that is not a
calibration failure.

## Output format

1. **Verdict table** — candidate | pain addressed (cited) | verdict |
   one-sentence anchor.
2. **Per-adopted-item spec** (Pass 2 + Pass 3 content, compact).
3. **Deferred amendments** — the exact paragraphs to append to
   `obligation-ledger-design.md` for every DEFER-TO-GATE.
4. **Roadmap delta** — the batch/backlog edits, ready to apply.
5. **Register of rejections** — candidate, the argument it re-loses or
   constraint it breaks, and the observation that would reopen it.

Do not pad. A REJECT that names the settled argument it would re-lose is
worth more than an ADOPT with an unpriced churn bill.
