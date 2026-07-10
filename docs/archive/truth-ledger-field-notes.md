# Truth Ledger — Field Notes from the First Pilot Deployment

> Reader: anyone who has read the paper (truth-ledger-paper.md) and wants to know what happened when the artifact met a real repository | Enables: judging which of the paper's claims now carry field evidence, and which new defect classes the pilot surfaced | Update-trigger: each verification round, hand-audit, or newly confirmed defect class in the pilot

**Status:** FROZEN 2026-07-09 — superseded by
[truth-ledger-paper-v2.md](../truth-ledger-paper-v2.md), which absorbed this
document's field evidence into the single living paper. This document no
longer accumulates anything; it is kept verbatim for the record, and its
counts and version references are those of its freeze date. (At freeze:
artifact v0.5.2 in the field — work kernel, spec-health, doc-health;
canary then at 48 seeded faults.)

**Setting.** One pilot repository: a multi-component kitchen-manufacturing
monorepo (domain core, catalog service, ERP, CAM, two adapters), operated by
a solo developer with LLM agent sessions doing the implementation work — the
exact regime the design targets. Day-0 baseline: 2026-07-08. Everything below
is from the ledger's own history (`git log -p .truth/claims.jsonl` in the
pilot) — the forensics property doing double duty as research instrument.

The headline surprise is the *density*: the first two days of operation
produced two genuine divergences, one falsified operator habit, one new
defect class, three satellite mechanisms, and field exercise of nearly every
v0.4 repair. Decay is not a slow background process; at agent speed it is a
daily event.

---

## 1. Interim numbers

| Measure | Value (as of 2026-07-09) |
|---|---|
| Verifier dispatches | 31 |
| — agree | 29 |
| — diverge (genuine, true positives) | 2 |
| — diverge (mechanical: evidence recipe changed, fact still true) | 1 |
| — cannot_verify | 0 |
| Claims in pilot ledger | 21 (15 live, 6 retracted tombstones) |
| Human retractions via `TRUTH_HUMAN=1` | 6 — all by the human, none by an agent |
| Tripwire precision (post-commit scan on a real refactor) | 1 staled / 1 should-have-staled, 0 false alarms that round |
| Concurrent agent sessions writing one ledger | 6 interleaved, zero corruption, coherent fold |
| Canary growth (every satellite gated at birth) | 19 → 42 → 45 → 48 faults |

These are mechanism-adjacent numbers, not the efficacy trial (§8 of the
paper); the first monthly hand-audit against the day-0 baseline is due
~2026-08-08 and will be recorded here.

---

## 2. Where practice confirmed theory

**2.1 The reproducibility/interpretation gap is where real failures live
(paper §7.2) — confirmed with precision.** Both genuine divergences were the
same shape: a *correct* evidence command with an *overreaching* claim text —
a repo-wide clause ("the only occurrences in the repo are…") backed by a
package-scoped grep (`--include` filters doing hidden work). Same author,
same defect, caught twice by independent verifiers. The paper predicted the
location of failure; the field confirmed it and added the frequency: in this
pilot, **scope overreach is the dominant real failure mode — hallucination
has not yet been observed at all.** The earned rule is now in the template
README's "Claim discipline" section: *never write a repo-wide clause backed
by a package-scoped command; name the by-design survivors (tests, attic)
explicitly.*

**2.2 Scripted independence (G11) works — and verifiers exceed the script.**
The correlated-verifier fear (paper §1.2, fourth row) did not materialize:
fresh verifiers receiving dispatch-only context caught the author twice.
More striking, two verifiers independently *exceeded* the dispatch's
ambitions: asked to confirm "enforced at commit time," each traced
`git config core.hooksPath` to the active hook manager rather than trusting
the vestigial `.git/hooks/` — unprompted norms-versus-properties skepticism
(§7.1) applied by the verifier to the claim's enforcement clause.

**2.3 The v0.4 repairs are load-bearing in practice.**
- **F2 (durable re-verification):** re-verified claims stayed live across
  subsequent scans; no re-staling loop, no warning fatigue.
- **F4 (human-gated retraction):** exercised six times, always by the human
  (the operating convention is that agents never execute the
  `TRUTH_HUMAN=1` command even when they draft it — the human runs it).
- **G8 (near-duplicate intake):** fired correctly against a successor claim
  and was consciously overridden with `--duplicate-ok` and a basis — exactly
  the friction the gate is meant to create.
- **Confluence + `O_APPEND` folklore:** six concurrent sessions interleaved
  appends with zero corruption and an order-independent fold. Small-scale
  evidence only; the paper's single-regime caveat stands.

**2.4 The growth-gate discipline transferred from repairs to features.**
Post-paper, every new mechanism (work kernel v0.5, spec-health v0.5.1,
doc-health v0.5.2) shipped with seeded canary faults at birth, each with a
fault-injection assert so the canary cannot lie in either direction. "Every
repair gated" generalized, unforced, into "every feature gated."

**2.5 The falsification loop still binds its practitioners.** The pilot's
gates repeatedly caught their own installers: the dead-name pre-commit check
fired on the commit *introducing* the spec convention (a spec citing a
rename ADR by its full filename); it fired again on its author's roster
edit. The paper's recursive episode (§6.3) was not a one-off — turning the
machinery on its operator is the normal operating mode.

---

## 3. What the field found that the theory did not name

**3.1 The dead-tripwire defect class (proposed INV-M).** The pilot's most
instructive find, discovered by inspection — no gate fired. A claim was
filed with space-separated `--paths` ("a.sh b.sh"); the CLI, expecting
commas, stored **one literal path that matches nothing**. The result is a
claim whose text is true, whose evidence recheck matches, which every
verifier honestly agrees with — and whose invalidation tripwire can never
fire. Invisible to recheck (hash matches), to the verifier (text is sound),
to `validate` (record is well-formed), to doctor and canary alike.

This extends the paper's detector-of-detectors observation (§7.3) one level
down: *the protection metadata of a claim has invariants of its own, which
nothing checks.* A claim's `evidence_paths` are load-bearing exactly like a
test suite's skip conditions — and they can be silently dead on arrival.

Proposed repair, in the paper's own format:

| ID | Property | Falsified by | Gate |
|----|----------|--------------|------|
| INV-M *(proposed)* | Every `evidence_path` on an accepted claim matches ≥1 tracked file at filing time, or is an explicit glob | One accepted claim whose tripwire can never fire | Intake check (warn or refuse on whitespace-but-no-comma paths and zero-match literals); canary fault seeding a dead tripwire |

Field handling until then: the successor-claim pattern (file corrected claim
with `--duplicate-ok`, human retracts the mis-filed original). G8
demonstrably makes this deliberate rather than accidental.

**3.2 A threat-table row the BFT transposition missed: the scoping fault.**
The paper's §1.2 table maps crash/omission/Byzantine/correlated faults. The
empirically hot failure mode fits none of them: an honest actor, honest
evidence, and a *quantifier* in the text that the evidence does not support.
Suggested row: *scoping fault — claim text quantifies beyond the evidence
command's domain*. Its defense is not redundancy but discipline plus
independent decode (the verifier prompt's step 2, which is what caught both
instances).

**3.3 Lifecycle ordering: claim-at-death vs. its own tripwire.** The work
kernel (post-paper, ADR-002) lets `done --claim` file a completion claim
atomically with closing an issue. Field wrinkle: filed *before* the shipping
commit, the claim's own evidence paths are touched by that commit and the
claim stales within seconds of birth. Earned operating rule, now in the
template README: **commit the work first, then `done --claim`.** A
first-class fix (intake noticing staged-but-uncommitted evidence paths)
remains open.

**3.4 "Diverged" conflates two different deaths.** When a template update
changed a health script's output strings, recheck correctly auto-diverged a
claim whose *fact* was still true — the evidence recipe had changed, not
reality. The status vocabulary does not distinguish *reality moved* from
*the measuring stick moved*. The successor-claim pattern absorbs this in
practice; a `re-anchor` verb or a distinct mechanical-divergence reason
would name it properly. Recorded here as vocabulary debt, not urgent.

**3.5 Evidence hashing wants stable output by construction.** Health-gate
evidence commands whose raw output embeds counts ("0 failures across 70
docs") mechanically diverge whenever the corpus grows, while the claimed
fact ("corpus is clean") stays true. Field convention, now documented:
pin the output — `bash scripts/doc-health.sh >/dev/null 2>&1 && echo CLEAN`.
An intake lint ("evidence output contains digits that look like counts —
consider pinning") would make the convention mechanical.

---

## 4. Satellite mechanisms the pilot grew (and what they generalize)

The pilot repeatedly hit one meta-pattern: **facts restated in prose rot;
facts cited by id stay checkable.** Three mechanisms fell out, all now
upstream in the template:

- **Work kernel (v0.5, ADR-002):** issues as ledger records with
  premise-at-birth and claim-at-death; `truth ready` = open ∧ deps closed ∧
  premises valid.
- **spec-health (v0.5.1):** feature specs may carry facts only as ledger
  ids; a sweeper judges every spec by the ADR-001 matrix of the ids it
  cites. A cold review of the pilot's first spec found the convention's
  blind spot immediately: a spec's ground truth that is premise of no cited
  issue is invisible to `truth ready` — now a WARN.
- **doc-health (v0.5.2):** the same idea for the prose fabric itself
  (forbidden post-rename names, broken relative links). A two-detector sweep
  of the pilot's 105 live markdown files found the rot **concentrated 100%
  in pre-ledger prose** — every post-convention document came back clean
  except one routing gap. That distribution is the strongest field evidence
  yet for the design thesis: the ledger's citation discipline prevents decay
  at the source, rather than detecting it after the fact.

The satellite pattern is itself the transferable part: *any* artifact class
admitted into the repo needs its own health tripwire at birth, or it is
future archive material.

---

## 5. Open items the field is watching

1. **The efficacy trial** (paper §8, "the largest open claim"): first
   monthly hand-audit vs. day-0 baseline due ~2026-08-08; results land here.
2. **INV-M intake gate + canary fault** (§3.1) — highest-value hardening.
3. **Scoping-fault countermeasure** beyond discipline: an intake heuristic
   flagging universal quantifiers ("only", "no ... anywhere", "the repo")
   when the evidence command carries path or `--include` filters.
4. **Re-anchor vocabulary** for mechanical divergence (§3.4).
5. **Multi-human concurrency** remains unexercised; six agent sessions on
   one machine is not two humans on two machines.
6. **Agent compliance** (the paper's stated weakest link) has held in the
   pilot — every session discovered the layer via the instruction snippet —
   but the pilot's operator is also the layer's author; discovery by
   unbriefed agents in unrelated repos is untested.
