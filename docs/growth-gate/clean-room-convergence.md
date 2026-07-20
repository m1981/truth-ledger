# Clean-room convergence check (2026-07-20)

Method: an independent Fable 5 designer was given ONLY the eleven SDLC
problems and their ISO obligations (29148, 24765, 12207, 10007,
25010/25023, 29119, 42010) plus the accepted open-world premise — with
NO knowledge of the truth ledger, the paper, or the obligation-ledger
design — and asked to imagine a solution per problem. Under the §8
item 1 single-observer limit, independent convergence is the nearest
available substitute for external review (paper §6.3's own argument).
The full clean-room output is reproduced at the end of this file.

## Convergences (validation)

The designer's five cross-cutting invariants map onto shipped or
archived decisions almost one-to-one:

| Clean-room invariant | Ours |
|---|---|
| "Everything is a card in git; no ID → doesn't exist" | Claims/records with ids; citation-over-restatement (§5) |
| "Determinism checks structure; LLMs check meaning; humans routed by dissent and stakes" | The obligation-ledger three-tier split, verbatim in effect |
| "Evidence must be shown able to fail" | Seeded-fault canary + negative controls; "a method that cannot be surprised isn't testing anything" (§4) |
| "Every guarantee is bounded and dated" | Frames + TTL'd attestations; evidence anchored at commits |
| "Waivers over silence" | Recorded overrides with basis (--scope-ok etc.) |

Mechanism-level convergences: dirty-propagation staleness over a trace
graph (= invalidation scan); immutable verbatim wish records with
falsifiable assumption cards (= event-sourced claims/premises); blind
reading — the checker never sees the spec author's reasoning (= the
dispatch seam, ADR-010); incident-to-gap ritual growing question banks
monotonically (= loophole map + ADR discipline); seeded challenges
against the pipeline's own checks and humans (= canary discipline;
obligation-ledger §5); signed baseline tags over cards+trace (= anchor
commits; the solved 10007 case).

## Divergences — adoption candidates (ranked)

1. **Interpretation-divergence test** (its #1): two LLM workers
   independently derive concrete input/output examples from a
   requirement's text; a comparator diffs the example sets — divergent
   examples = detected ambiguity, attached to the refusal. Semantic
   where our ADR-007 quantifier gate is lexical. Candidate: intake
   QUEUE warning (per the gate-vs-queue rule; too costly/noisy as a
   hard gate).
2. **Requirement mutants / discriminating witnesses** (its #10): a
   witness test counts toward coverage only if it kills ≥1
   LLM-authored requirement-specific mutant. Mutation testing lifted
   from code level to requirement level. Candidate: obligation-ledger
   29119 row upgrade; also a stronger acceptance-oracle discipline.
3. **Constraint sketches + neighborhood consistency** (its #3): cards
   compile to typed numeric claims (unit-aware, arithmetically
   checkable) + shared-noun index; new cards pairwise-checked only
   against their neighborhood. Semi-automatic contradiction *detection*
   where our contradicts edges are manual declarations. Candidate:
   obligation-ledger 29148-consistency row.
4. **Expiring waivers with default-to-removal** (its #5): an
   UNJUSTIFIED/deferral entry expires; on expiry the covered thing
   auto-enters quarantine → deletion PR. Inverts the parking-lot
   failure: not deciding defaults to removal, not accumulation. Our
   overrides never expire — this is a direct improvement candidate.
5. **Forced-choice anti-rubber-stamp** (its #8): every question to a
   human ships with two defensible candidate answers with visibly
   different consequences — a nod is impossible. Complements the
   obligation-ledger's one-screen bundles + seeded challenges.
6. **Amendment-velocity tripwire** (its #11): a constraint amended
   twice a quarter triggers "was this ever real?" review — a concrete
   detector for the surrender-diary failure mode (our --scope-ok-rot
   worry, given a metric).

## Where the clean-room design is weaker (litigated ground it would re-lose)

- **Concurrency/confluence unaddressed**: "approval is the merge"
  assumes merge machinery; nothing handles union-merge ordering,
  duplicate ids, or tombstone resurrection — the entire F1–F8 defect
  class this artifact spent an audit closing. A build would rediscover
  them in week one.
- **No identity/threat model**: who may write cards, forge approvals,
  or backdate is unstated (our §8 items 5–6, ADR-010/011).
- **No re-affirmation economics**: dirty-propagation staleness with no
  cost story for re-checking — it would hit the measured 1.5%-hit-rate
  churn wall that forced `reaffirm` (ADR-030).
- **No judge calibration loop**: adversarial spot-audits exist but no
  measured precision/recall feedback (obligation-ledger §4).

## Disposition

No current work item. Candidates 1–6 join the obligation-ledger design
as amendments to consider at its demand gate; candidate 4 (expiring
waivers) is small enough to promote to the roadmap backlog if the
operator wants it in the current artifact.

---

## Appendix: the clean-room design, verbatim

(Preserved unedited as the convergence evidence; treat as an external
reviewer's artifact, not house style.)

Shared substrate assumed throughout: every claim (requirement, intent, decision, waiver) is a small YAML "card" with a stable ID, living in `/spec` in the same git repo as the code. Links between cards, code, and tests are data, not prose. CI is the deterministic enforcer; LLM sessions are cheap semantic workers; humans are routed to *disagreement and stakes*, never to volume.

### 1. The untestable sentence
**Mechanism.** A requirement card is not accepted until it carries an **oracle**: an executable check, or a written observation procedure with concrete pass/fail values. Ambiguity detection: on card creation, two LLM workers with different prompts each independently produce (a) a paraphrase and (b) three concrete input/output examples they believe the requirement demands. A comparator diffs the example sets. If both readings are plausible but their examples disagree — the **interpretation-divergence test** — the card is bounced with the divergent case attached. **Split.** Deterministic: schema requires the oracle field; oracle must execute in CI. LLM: rival interpretations and candidate examples. Human: signs oracles for high-stakes cards only. **Guarantee.** Every accepted requirement has a machine-decidable "done" agreed before implementation; cannot guarantee the oracle encodes what the stakeholder meant. **Failure mode.** Trivially-passable oracles; countered by a periodic LLM audit asking "what obviously wrong implementation would still pass this oracle?"

### 2. The missing requirement
**Mechanism.** Probe from known directions: (1) versioned **question banks** (failure modes, abuse, operations, data lifecycle, compliance) run by LLM workers against every new feature card — each question gets an answer, a card, or an explicit "not applicable because…"; (2) a **consequence miner** on every diff ("what else must be true for this to work?"); (3) the **incident-to-gap ritual** — every bug/ticket classified: was the expectation ever written? If no, a card is born AND a new question joins the bank, so each surprise permanently widens the probe surface. **Split.** Deterministic: the queue cannot be silently emptied (card, rejection-with-reason, or expiring deferral). LLM: candidate generation and triage. Human: accept/reject (value judgment). **Guarantee.** Gaps of kinds the banks encode get asked about before integration; gaps outside every bank stay invisible until an incident converts them. **Failure mode.** Candidate flood → bulk rejection; countered by a hard cap per diff, LLM-ranked by cost-of-late-discovery.

### 3. The contradicting pair
**Mechanism.** Neighborhood consistency: each card compiles (LLM, author-verified) to a **constraint sketch** — nouns/resources touched, typed numeric claims with units, ordering/invariant claims. A shared-vocabulary index maps nouns to cards. A new card is pairwise-checked only against its neighborhood: numeric claims via a deterministic unit-aware checker; semantic pairs via an LLM judge asked to construct a single scenario satisfying both or explain why none exists. **Split.** Deterministic: indexing, blast-radius selection, numeric conflicts. LLM: semantic contradiction hunting. Human: resolving confirmed conflicts. **Guarantee.** Contradictions between cards sharing vocabulary/typed resources are caught at authoring; those behind synonym mismatch survive. **Failure mode.** Vocabulary fragmentation; countered by a scheduled synonym-merge pass whose merges are human-approved cards.

### 4. The orphaned requirement
**Mechanism.** Every approved card accumulates **witness edges** (test files annotated with the card id). CI builds the forward trace matrix per merge; release refused while any approved, non-waived card has zero passing witnesses. Edges are live: a vanished annotation deletes the edge and reverts the card to "unevidenced" — loudly. **Split.** Deterministic: scanning, matrix, release gate. LLM: proposing edges for legacy code; auditing edge plausibility. Human: waivers (expiring, owner-named). **Guarantee.** Nothing approved ships with zero attached passing evidence; sufficiency is problem 10's job. **Failure mode.** Annotation spam; countered by sampled blind audits — a judge names the requirement a test verifies WITHOUT seeing the annotation; mismatch invalidates the edge and flags the author's other edges.

### 5. The orphaned implementation
**Mechanism.** A `justifies` index maps every module/public symbol to a card, an ADR, or an explicit UNJUSTIFIED entry. CI blocks diffs introducing symbols reachable from no card. An **LLM archaeologist** sweeps legacy code producing dossiers (inferred purpose, callers, deletion blast radius). Confirmed-unjustified modules enter **quarantine** (usage canary one cycle) then an auto-drafted deletion PR with dossier. **Split.** Deterministic: reachability, gates, canary wiring. LLM: archaeology. Human: approving deletions (irreversible). **Guarantee.** Every piece of code has an answer-of-record to "who asked for this?"; the answer can be stale or sincerely wrong. **Failure mode.** UNJUSTIFIED as parking lot; countered by expiry → auto-quarantine, so not-deciding defaults to removal.

### 6. The unfaithful implementation
**Mechanism.** Faithfulness checks per pipeline transformation, triggered by dirty-propagation over the trace graph. Two layers: deterministic **extract-and-compare** (signatures, constants, limits, enums parsed from both sides and diffed); and **blind reading** — one worker summarizes what the implementation actually does without seeing the spec; a separate comparator diffs summary vs spec. Blindness matters: a worker shown the spec hallucinates conformance. **Split.** Deterministic: staleness propagation, literal comparison, no-merge-while-stale. LLM: blind reading. Human: adjudicating material discrepancies. **Guarantee.** Drift in checked properties surfaces within one commit; unextracted properties drift silently. **Failure mode.** Discrepancy noise → auto-dismissal; countered by injected deliberate mismatches — waved through means the check is declared dead and rebuilt.

### 7. The right-built wrong product
**Mechanism.** Validation gets its own artifact: **intent cards** (world-observable outcomes) authored before requirements and linked. Per release: **persona simulation** (LLM agents given only the intent and the staging UI attempt the task cold; transcripts of confusion) and **telemetry contracts** (each intent declares its post-release signal, checked in a window). A standing **wrong-product review**: "every test is green — construct the story in which this is still useless." **Split.** Deterministic: linkage rule, telemetry evaluation. LLM: simulations and story generation. Human: validation sign-off, non-delegable, by someone other than the spec's author. **Guarantee.** Every release confronts recorded intents via an uninvested examiner; cannot guarantee the intents captured the real need. **Failure mode.** Personas converge on happy paths; countered by per-release persona mutation and tracking simulation FAILURE rate — a suite that never fails is broken.

### 8. The stakeholder-to-spec chasm
**Mechanism.** Verbatim immutable **wish records**. An LLM **intake refinery**: vague adjectives must resolve to measurables; every wish states its trade; clarification questions ranked by decision impact; only top-k (3–5) go to the human, the tail becomes recorded falsifiable assumptions. Derived cards link to the wish record; acceptance disputes replay original words + interrogation transcript. **Split.** Deterministic: no design entry without a transcript; unresolved-adjective lint. LLM: interrogation, quantification, ranking. Human: answering top-k only. **Guarantee.** No wish reaches design unexamined; cannot guarantee the answers are right or that the highest-impact question was asked. **Failure mode.** Rubber-stamped suggested answers; countered by shipping each question with two defensible candidate answers with visibly different consequences.

### 9. State blindness
**Mechanism.** If it isn't in the repo, it isn't decided. Cards, code, edges, waivers share the repo; a **baseline** is a signed git tag over approved cards + code + trace matrix. Status fields mutate only by merge machinery (approval IS the merge of an approval card). Query tool answers current/pending/as-of-tag mechanically, including what was evidenced. **Split.** Almost entirely deterministic; LLM only as a decision-capture bot drafting change cards from chat/meetings. Human: signing baselines. **Guarantee.** Any as-of question about tracked artifacts is exact; out-of-repo decisions are invisible (behavioral residual). **Failure mode.** Ceremonial signing; countered because the tag embeds the trace matrix — signing over red evidence is self-documenting and attributable.

### 10. The coverage illusion
**Mechanism.** Real denominator: approved cards with oracles. Real numerator: cards whose witness tests are **discriminating** — LLM workers author **requirement mutants** (plausible implementations violating the requirement specifically); a witness counts only if ≥1 mutant makes it fail. Headline is a list (zero-evidence cards; never-shown-able-to-fail evidence), not a percentage. **Split.** Deterministic: mutant execution, kill-tracking, gates. LLM: authoring mutants. Human: reviewing surviving mutants (real hole or spec ambiguity). **Guarantee.** Every counted unit of coverage is a test demonstrably capable of failing against a real violation of a written promise; unwritten requirements stay outside the denominator (problem 2's residual, and the dashboard says so). **Failure mode.** Strawman mutants inflate kill rates; countered by cross-examination — a judge rates whether each mutant would plausibly arise from a rushed implementation.

### 11. Architecture fiction
**Mechanism.** Two layers with opposite trust: the **extracted view**, regenerated deterministically per merge from code (dependency graph, boundaries, manifests, data-access map) — cannot be fiction; and the **asserted view** (constraints, intents, ADRs), each constraint a machine-checkable predicate over extracted facts where possible. **Correspondence checking** diffs the two per merge; a violated constraint blocks until code is fixed or the ADR formally amended — silent divergence is the one forbidden outcome. **Split.** Deterministic: extraction, predicates, gate. LLM: narrating architectural change, drafting amendments, flagging prose that should be a predicate. Human: approving constraint changes. **Guarantee.** Constraints expressible over extractable facts cannot silently diverge longer than one merge; emergent runtime qualities remain narrative and are labeled as such. **Failure mode.** Deadline amendments turn the description into a diary of surrenders; countered by tracking amendment velocity per constraint — twice a quarter triggers "was this ever real?" review.

### Cross-cutting invariants (clean-room)
1. Everything is a card in git — no ID, no existence.
2. Determinism checks structure; LLMs check meaning; humans are routed by dissent and stakes.
3. Evidence must be shown able to fail.
4. Every guarantee is bounded and dated; probe sets grow monotonically from incidents.
5. Waivers over silence — every bypass is a recorded, expiring, owner-named card.
