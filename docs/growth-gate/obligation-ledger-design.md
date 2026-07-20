# The Obligation Ledger — three-tier standards enforcement (design sketch)

Status: **demand-gated future work** — NOT current architecture, NOT
roadmapped. Trigger: a real team adopting the truth ledger against a
real compliance regime (ISO/IEC/IEEE 29148, 12207, 29119, 42010, ISO
10007, SQuaRE) and asking for obligation-level enforcement. Until that
demand signal exists, this document is the design answer to "could the
ledger enforce the standards end-to-end?" — kept here so the answer is
not re-derived. Unlike the TLR archive beside it, no executable oracle
exists yet; §6 states what one must pin before any build.

Date: 2026-07-20. Derived from the paper's §6.4 standards mapping and
the session review that established what the current artifact does NOT
address end-to-end (set-quantified obligations, semantic judgment
calibration, unconditional enforcement).

## 1. The claim, precisely bounded

No mechanism can *prove* an open-world obligation ("the requirement set
is complete"). What a three-tier design can achieve — and what this
design claims, no more — is:

> Every obligation is either (a) mechanically enforced, or (b) covered
> by a **recorded bounded search** plus a **fresh, accountable, decaying
> human attestation** — and the moment the covered reality changes, the
> attestation mechanically re-opens.

That is strictly stronger than the human-process ISO regime (whose
signatures never expire and whose searches are unrecorded) and strictly
weaker than proof. The residual — the hazard nobody can imagine — is
permanent and is named, not hidden.

## 2. The three tiers are three different JOBS

- **Mechanical (gate):** decides the decidable. Refusals at intake,
  prefix/schema gates, trace-link resolution, oracle exit codes.
  Enforcement moves from opt-in local hooks to a **server-side merge
  queue / required CI check** — the one change that makes the borrowed
  event loop unconditional (closes the §8-item-5 conditionality for
  obligation-bearing repos).
- **LLM (tribunal):** two roles, never conflated.
  - *Judge* — semantic verdicts (does evidence support this sentence;
    do these two requirements contradict), N independent sessions with
    diverse lenses above a cost tier; the existing dispatch protocol
    generalized.
  - *Adversary* — **negative-space search**: generate candidate
    counterexamples to set-quantified obligations ("what requirement is
    missing given this diff?", "which pair cannot both hold?", "which
    stakeholder concern has no view?"), run loop-until-dry (K
    consecutive empty rounds). Converts "no gap found" from silence
    into a recorded, bounded effort.
- **Human (ceremony):** exactly two scarce acts.
  - *Quantifier closure* — signing an obligation's attestation over an
    LLM-compressed one-screen evidence bundle, via the existing ADR-011
    exact-id ceremony, **with a TTL**, watched so it re-stales when the
    frame changes.
  - *Terminal decisions* — retraction, waiver, risk acceptance
    (unchanged from ADR-011/G12).

## 3. New record kinds

- **obligation** — a standard's requirement instantiated against a
  **frame**: an enumerable denominator (all files under a path, all
  rows of a requirements doc, all public API symbols, all stakeholder
  register entries). Frames defeat the quantifier problem by scoping
  it: "complete relative to frame F at commit C" is checkable and
  invalidatable; "complete" simpliciter is not.
- **attestation** — the human closure event: signer, obligation id,
  bundle hash, TTL, frame snapshot. Re-staled by frame change or TTL,
  exactly as claims are today.
- **audit** — sampled human review of an LLM verdict (see §4).

All fold, queue, and readiness semantics reuse the existing machinery;
an obligation with a stale attestation blocks whatever declares it as a
premise, through the unchanged ADR-001 matrix.

## 4. The calibration loop

Every LLM verdict is subject to sampled human audit (e.g. 5%,
stratified by cost tier). Audit outcomes are records; `stats` reports
per-obligation-type precision/recall of the tribunal. Sampling and
escalation thresholds adapt to the measured agreement. This makes
verifier calibration — unmeasured in the current artifact (§8 item 7) —
a first-class measured quantity instead of a hope.

## 5. Anti-rubber-stamping

Human ceremonies rot into ritual (the `--scope-ok` rot worry,
generalized). Countermeasures, all mandatory in this design:
- **One-screen bundles** — compression is the tribunal's job; a bundle
  that cannot fit one screen is a refusal, not a longer read.
- **Seeded challenges** — known-injected gaps in a sampled fraction of
  bundles; signing over one flags the review process (the canary
  discipline applied to humans).
- **Dual control** on the highest tiers; **decay** on everything (no
  attestation outlives its TTL or its frame).

## 6. Per-standard decomposition

| Obligation | Mechanical | LLM tribunal | Human ceremony |
|---|---|---|---|
| 29148 individual characteristics | testable-shape lint; quantifier/scope gate (shipped) | judge: ambiguity/feasibility/singularity at intake | contested verdicts only |
| 29148 set completeness | frame defined; attestation freshness | adversary: missing-requirement search per diff, loop-until-dry | signs closure, TTL'd |
| 29148 set consistency | declared contradicts → DISPUTED (shipped) | adversary: pairwise contradiction sweep | resolves confirmed pairs |
| 24765 forward trace | req id → ≥1 resolving code/test link (CI) | judge: link semantically real vs token match | waives orphans |
| 24765 backward trace | premise records + ready (shipped) | adversary: undeclared-assumption search per hunk | attests closure per epic |
| 12207 verification | recheck: re-run + hash (shipped; fully mechanical) | — | — |
| 12207 validation | — | judge: output-vs-text, N-session, calibrated (§4) | sampled audit |
| 12207 requirements analysis | intake refuses unmeasurable wishes | judge: transform/flag raw statements | approves negotiated set |
| 10007 status accounting | derived status, all kinds (shipped — solved) | — | — |
| 25010/25023 functional completeness | implemented/specified computed from frame (CI) | adversary: inverse count (in code, absent from spec) | accepts the frame |
| 29119 requirement-based coverage | req id → ≥1 executed exit-0 test (extends done-oracle) | judge: does the test exercise or merely touch | per-req waivers, recorded |
| 42010 correspondence rules | doc-coverage claims per declared view pair (shipped), frame-scoped | adversary: cross-view contradiction + drift sweep | architect signs per release, TTL'd |

Acceptance oracle to write before any build (TLR discipline): confluence
of obligation/attestation folds under permutation; attestation re-opens
on frame change and TTL; seeded-challenge detection; calibration-stats
correctness on a synthetic audit stream; a negative control per property.

## 7. What this still does not give — the permanent residual

The unknown unknown. Worked example: a login-page requirement set;
mechanical proves every requirement tested; the adversary surfaces
password reset, rate limiting, lockout across three rounds to dry; a
human signs completeness. Months later an account is hijacked via a
re-registered expired email domain — an attack nobody, human or model,
had imagined. No tier could catch it: search finds only what is
conceivable to the searcher. The system's guarantee at that moment is
not "the gap did not exist" but: *the search that missed it is on
record, the signature that accepted the residual risk is attributable
and was still fresh, and the question had been mechanically re-opened
at every change since.* "Proven complete" is impossible; "accountably
searched and freshly signed" is the ceiling — and this design claims
exactly that ceiling.

## 8. Cost honesty

Roughly 3–5× the current mechanism surface, plus standing tribunal
compute and human sampling load. Efficacy would need its own trial by
the paper's own discipline (§7/§8): mechanism-exists ≠ net-helps. Which
is why this stays demand-gated behind a real compliance adopter, and
the current artifact's trial (roadmap R11) runs first.
