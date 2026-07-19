# Field notes — batch-M spec-review & self-verification session (2026-07-19, v0.9.9)

> Reader: anyone revising the paper (§8 honest limits, the defect table) or the
> verification regime | Enables: citing what a review-and-fix session learned
> about its OWN failure modes — where the regime caught the verifier's
> reasoning, not just the code | Update-trigger: an item folds into an
> ADR/paper section, or a later session contradicts one

Review artifact, not a decision. Generated from the batch-M session: four
independent spec-review findings (M1 cross-surface version drift, M2 schema
permits-what-prose-forbids, M3 issue-event state machine, M4 screen/determinism
ordering) worked through the standard drill and shipped as **v0.9.9**
(ADR-026..029), forwarded to both deployments. The reviewer and the
implementer/verifier were **the same author-agent** across turns, with fresh
Fable subagents dispatched as adversaries — so the §8.1 conflict-of-interest
caveat applies doubly: these observations are about the *process*, and the
process's own author is reporting them. Each item is a drop-in proposal;
nothing in the existing docs was edited by writing this file.

The distinguishing feature of this session: **every high-value failure clustered
at the verifier's own conclusions, not at the findings.** All four findings were
confirmed. What needed adversarial pressure was the *dispositions* — the
downgrades, the evidence commands scribed, the "this is fine" judgments. A
regime that only points outward (at the code, at the finding) misses the
highest-frequency error source.

---

## 1. (HIGHEST VALUE) A severity *downgrade* is a claim — refute it before building

**Home:** paper §8 (new limit) + a methodology note; generalizes the H3/H5
"adversary refutes your conclusion" lesson.

**What happened.** M3 was filed "the issue-event state machine is undefined."
Re-verification found the machine fully defined *and* unit-tested
(`issue_event_error` + `fold_issues`, `test_transition_matrix`), so it was
downgraded to document-only. A **pre-build** Fable adversary, tasked to *refute
the downgrade*, then CLI-reproduced a real hole: a schema-valid future-dated
issue record makes every honest-clock event sort before it, so `fold_issues`
drops the event while intake prints `-> closed` at exit 0 (permanently open,
un-closable, un-cancellable). The downgrade — not the finding — was the false
claim. Same shape in M2: the disposition "just tighten `anchor_commit`'s
minLength" would have opened a *fresh* FS-2 violation (VERIFIED+`null`
schema-valid but mirror-invalid) that no mutant could surface.

**Proposal.** Make it regime: when re-verification *reduces* a finding's
severity (undefined→document-only, security→spec-precision, hole→dormant,
needs-fix→already-handled), that reduction is the claim to dispatch an
adversary against — **before** building, because the downgrade is what halts
work. Note the two distinct adversary jobs: PRE-build refutes the *disposition*
(reshapes the fix before a line is written); POST-build refutes the *artifact*
(re-runs the mutants). A downgrade or behavior-change earns both.

## 2. A VERIFIED completion claim can be hollow — the double-run passes stable *failure*

**Home:** paper §8 + `.truth/README` (a caution in the claim section); candidate
for a mechanical guard (see Proposal).

**What happened.** Two of the author's own completion claims were VERIFIED but
proved nothing, both caught by the independent verifier and neither by filing:
(a) `tr-3b69f8ff`'s evidence grepped `"sorts before its issue record"`, a phrase
the source splits across two lines, so `grep -q` never matched and the
`&& echo OK` chain silently failed; (b) `tr-22853f21`'s evidence hardcoded the
README string `"v0.9.8"`, which the v0.9.9 bump broke. `claim --class VERIFIED`
files on *determinism* (two intake runs hash-match), not on exit 0 — so a
stably-failing command files clean and "rechecks" forever by stable failure. It
is an INV-M dead tripwire one level up, inside a completion claim.

**Proposal.** (a) Operator discipline: run the evidence command and confirm
exit 0 before filing; grep INVARIANTS (def/test/`FAULT`/ADR-id names), never
volatile strings (versions, dates, line-spanning phrases). (b) Mechanical
candidate worth weighing: a soft warning at `claim --class VERIFIED` time when
the evidence command's own returncode is non-zero — "evidence exited N; a
VERIFIED claim usually demonstrates its fact with a passing command" — non-
blocking (a claim may legitimately record a non-zero-but-stable probe), but it
would have caught both hollow claims at filing. Left as a proposal, not shipped,
pending a judgment on false-positive noise.

## 3. Composition-seam incoherence: two correct layers, wrong at their join (M3, shipped ADR-028)

**Home:** paper defect table (a new row, F-class) — this is the deepest
technical find of the batch.

**What happened.** Intake validated an issue transition against the *folded*
status (correct in isolation); the fold applied events in `fold_key` order and
dropped a forward reference (correct in isolation). Neither layer checked the
*seam*: that an accepted event will actually land after its referent in fold
order. A future-dated referent breaks exactly there. The fix mirrored the
claim-side pattern — one coherence rule at BOTH enforcement points:
`issue_event_ts_error` (clock-based, at intake) and an `order_check` rule
(clock-free, at the commit gate, catching raw appends). Canary FAULT IF,
mutant-verified (neuter both gates → both arms MISS 162/2).

**Proposal.** Add an F-row: "*Intake-validated transition the fold silently
discards* — a future-dated `issue` record makes its events sort before it;
intake reports success, `fold_issues` drops them. Closed at intake + order_check
(ADR-028)." The transferable moral for §8: **when two independently-sound gates
compose, add a test at their seam, not just within each.** The class is not
"the transition table is wrong" — it is "the intake↔fold composition is
incoherent in one corner."

## 4. Correct-meets-correct: two right mechanisms that collide (open, wk-dfb65ccc)

**Home:** paper §8 (honest limit) — an unresolved corner, logged not fixed.

**What happened.** ADR-022's deny baseline correctly refuses shells as evidence
programs; the canary correctly *is* a `bash` script. So the P0 claim
`tr-3a31bfcf` ("the canary catches every fault"), whose evidence is
`bash …truth-canary.sh`, can no longer mechanically recheck — the deny screen
refuses it. The re-affirmation sweep had to run the canary by hand (166/0) and
file `agree` with a manual-run basis. Neither mechanism is wrong; they are
incompatible at one point.

**Proposal.** Note it in §8 as a genuine limit of the evidence model: a fact
whose demonstration is *inherently* a shell invocation cannot be VERIFIED
evidence under the deny baseline. Candidate resolutions (wk-dfb65ccc): re-file
such a claim as INFERRED with a manual-run basis, or express it as an ADR-014
acceptance-oracle (oracles run `bash` by design — the deny baseline is
evidence-screen-only). Do NOT weaken the deny baseline to accommodate it.

## 5. Not-fixing as discipline: recognizing the escape hatch working as specified

**Home:** ADR-029 already records the disposition; logged here as a *process*
note.

**What happened.** The M4 adversary found that `--evidence-unsafe-ok` bypasses
the deny baseline at intake, so a deny-listed `sh` executes though its message
says "never … even if allowlisted." The reflex is to make deny outrank the
override (code). The correct call was to NOT: the command runs in the *author's
own* session (no new capability), is stored `screened:false`, and `recheck`
refuses it — the deny baseline's real purpose (stop a *verifier* running an
accidentally-allowlisted shell) holds via recheck, not intake. A special case
would add code with no security gain.

**Proposal.** For §8: a bias-check against reflexive hardening. When a
scary-looking behavior traces to an *explicit* escape hatch and the security
property is enforced at a *different* seam (here: recheck, not intake), the fix
is precise documentation, not more code. The one lasting change was making the
lying "never" honest (ADR-029).

---

## Confirmations already shipped (no action — logged for completeness)

- The **mutant test maps coverage, not just liveness**: under the AN-gate
  mutation, arms AN2/AN5 stayed CAUGHT because they gate *different* mechanisms
  (INV-B truthiness; the not-over-tightened property) while AN1/AN3/AN4 flipped
  — the mutation revealed the coverage split, catching redundant-arm risk. Same
  for FAULT IF and SD. Reinforces the v0.9.8 "mutant-verify every lock" lesson.
- The **quantifier-in-claim-text gate (ADR-007)** fired three more times this
  session on completion-claim text containing `never` — the gate is working;
  the operator habit ("describe tests/behavior, don't quote quantifier words")
  is the standing tax. No change.
- **M1 was the doc-sync residual, exactly as predicted**: version-pin drift was
  the class the doc-coverage tripwires did *not* watch. Now mechanized
  (README==CLI test + schema shape-fingerprint, ADR-026), converting a
  manual-audit residual into a battery gate.
