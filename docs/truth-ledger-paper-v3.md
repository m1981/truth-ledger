# The Truth Ledger: A Claim-Invalidation Layer for Agentic Software Development

**Status:** v3 (2026-07-20). Consolidation of v2: the accumulated dated
in-place corrections are collapsed into current-state text; the
correction history is Appendix C. v2 remains at
`docs/truth-ledger-paper-v2.md` until the operator retires it to
`docs/archive/`. Artifact audited: v0.4; deployed in the pilot at day-0:
v0.5.3 (the template has moved well beyond that — it states its own
version in `scripts/truth`, and the ADRs below note where each mechanism
landed; the pilot re-synced to v0.6.4 on 2026-07-13). Pilot: one
kitchen-manufacturing monorepo, one solo developer, LLM agent sessions
doing the implementation, day-0 2026-07-08. All §2 window-1 numbers are
self-reported by that developer, also this paper's sole author and
auditor — §8 item 1.

**How to read.** Sections are ordered by evidence class: mechanism and
measurement first, interpretation last. §6.2–§6.5 are explicitly
optional (§6.4 the practitioner motivation, §6.5 the nearest-kin
positioning); §6.1 isn't — it's the analysis §2 promises. §7 applies the
artifact's own discipline to this document: what would falsify its
claims. Appendix C is the revision history, one dated line per
correction.

---

## 0. What this is, in one paragraph

Language-model agents assert facts about codebases — "this module owns
all currency conversion," "no call sites remain for this API" — with no
record of how the fact was established and no mechanism for a later code
change to invalidate it. The truth ledger is a cache-invalidation system
for those sentences: every trusted claim carries a command whose output
was hashed at a known commit, and any later git event or elapsed TTL
that could undermine the claim mechanically demotes it. That's the whole
idea. Sections 1–5 are that idea, its measured behavior in real
deployments, and the defects an adversarial audit found; §6 is the
theoretical vocabulary that motivated the design, presented after the
mechanism and its field correction.

---

## 1. The mechanism

**Storage.** A single append-only JSONL file, `.truth/claims.jsonl`,
beside a work tracker it never writes to. A dependency-free Python CLI
(`scripts/truth` — ~750 lines at the v0.4 audit scope, grown severalfold
since; it states its own version), two shell gates (commit-time prefix
check, post-merge invalidation scan), a fixed verifier prompt, a JSON
Schema. Concurrent writers are assumed: racing appends rely on
POSIX `O_APPEND` atomicity for single-write-call, single-filesystem
safety — a load-bearing assumption, not only a caveat (§8).

**Seven record kinds**, one envelope (`id`, `kind`, `actor`, `session`,
`ts`):

- **claim** — an assertion with an `evidence_class` (VERIFIED / INFERRED
  / UNVERIFIED), a `cost_tier` (P0/P1/P2 — the cost of acting on it if
  false), and, for VERIFIED, an evidence capsule: command, output
  SHA-256, exit code, anchor commit, and watched `evidence_paths` (facts
  git can see) or `ttl_days` (facts outside the repository).
- **verdict** — a judgment (`agree` / `diverge` / `cannot_verify` /
  `retracted`), always with a `basis`.
- **invalidation** — a mechanical demotion: paths touched, TTL elapsed,
  or anchor unreachable after a history rewrite.
- **premise** — a work item's declared dependency on a claim.
- **issue** / **issue_event** — the work kernel (§5, ADR-002): work
  items folded the same way claims are — premise-at-birth and
  claim-at-death are events in one log, not a second system.
- **contradicts** (v0.9.0) — a *declared* edge between two claims that
  cannot both hold, with a required `basis`. No NLP, by design — the
  moment a gate needs a model to fire, it is a review, not a refusal.
  Intake refuses self-edges, unknown ids, retracted endpoints, and
  duplicates either direction.

**Derivation.** Status is never stored; a pure function replays the log.
The fold below covers claims; the work kernel adds `fold_issues`
(ADR-028): intake strict (a fixed transition table refuses nonsense
loudly), the fold permissive except that `cancelled` is terminal —
permissiveness buys merge confluence, intake is the gate. An
`issue_event` must sort after its issue record or the fold drops it as a
forward reference — enforced at intake and by `order_check` (ADR-028;
§4).

```
no events              → unverified
verdict agree          → live
verdict diverge        → diverged        (queued)
verdict cannot_verify   → cannot_verify   (queued if P0)
verdict retracted       → retracted       (terminal — later events ignored)
invalidation            → stale           (queued if P0/P1)
contradicts edge,       → disputed        (both sides; queued naming the
  both sides live                           counterpart; HOLDs work)
```

The `disputed` row is a **post-pass**: every `contradicts` edge is
judged against the *underlying* statuses the replay produced — never the
post-pass's own output — so the result is edge-order independent and
confluent. An edge fires only while *both* endpoints would
otherwise be `live`; `disputed` is recoverable by construction —
retract, supersede, or re-file either side; no resolution verb exists,
deliberately.

`invalidation → stale` is the *only* path to `stale`, complete: even TTL
expiry reaches `stale` only through an invalidation **record**. The scan
counts time from the claim's own `ts` and, strictly past `ttl_days`,
writes an invalidation; a TTL'd claim the scan has not visited is not
stale, however old the fact. The clock's effect is frozen into a record,
never recomputed on read (ADR-019).

A claim is born `unverified` regardless of its `evidence_class` — the
VERIFIED double-run at intake is a gate, not a verdict; only an explicit
`agree` advances it to `live`. Evidence attached at filing and evidence
independently confirmed are distinct events, never conflated. The
negative states are recoverable: a later `agree` returns `diverged`,
`cannot_verify`, or `stale` to `live` (re-anchoring a `stale` claim); a
TTL-staled claim re-lives too, but its TTL clock still counts from the
claim `ts` (ADR-019's non-goal), so the next scan re-stales it —
expired TTL claims are re-filed, not re-verified. Status is one total
function of the log (§6.3, ADR-020): fold in `(ts, id, canon)` order,
last-writer-wins per verdict/invalidation, `retracted` alone absorbing.
Only a human retraction is a dead end; a machine's "I could not check
this" is an invitation to check again, not a verdict.

Terminality of `retracted` is the system's strongest promise — **on the
paths this design defends against** — in two layers, both defended
(ADR-017, after an independent review found the second open):
the *status* stays `retracted` under any event, and the HELD block a
retracted premise imposes (ADR-001) is released only by matching human
authority — superseding it (ADR-013) requires the ADR-011 human gate,
exactly as retraction does. The mechanical dead states stay ungated,
because no human decided them.

**Fold semantics, precisely.** The fold replays every event in the
canonical total order `(timestamp, id, canonical-serialization)`,
ascending, regardless of file position — what makes replay
order-independent (F3). The third key came late (ADR-016):
`(timestamp, id)` alone is not total — a duplicate id with a copied,
byte-equal `ts` ties, letting a stable sort decide by file position, the
one thing the fold must ignore; the canonical serialization is a
deterministic function of content, so distinct records never tie. Within
that order, the *first* claim record for an id fixes its text and
evidence capsule; a later same-id record is ignored for content (F6) —
appendable, but changing no derived state.
Composing first-wins with the accepted timestamp-forgery threat yields
duplicate-id substitution attempts, governed since v0.9.13 by **one rule
(ADR-031)**: `validate` (hence the commit gate) refuses *any* record
whose id duplicates an earlier line's and whose canonical content
differs — whether its `ts` is earlier (the backdated shape ADR-008
caught), equal (ADR-016's copied-`ts` shape), or later. Corrections
always file under fresh ids, so no legitimate content-distinct duplicate
exists; only the byte-identical line a union merge duplicates passes,
and the comparison never parses a timestamp, so no forged-`ts` encoding
routes around it. The residual, accepted not detected: forgery on a
*fresh* id (§8 item 6).

**Intake gates.** `truth claim` refuses, before anything is written:
empty claim text (unverifiable, undivergeable, uncitable);
near-duplicates of active claims by symmetric Jaccard overlap ≥ 0.6
(ADR-018; overridable, always allowed for corrections of dead claims); a
universally quantified claim text over a scoped evidence command
(ADR-007, the §2 dominant-failure countermeasure — refused unless
`--scope-ok` states why the scope covers the quantifier);
*statically* dead-tripwire evidence paths (INV-M — a whitespace-no-comma
entry, a literal matching zero tracked files, or a
statically-unreachable glob; a *reachable* glob is exempt as a dormant
watch, ADR-023/024; no override); VERIFIED claims with no evidence
command, neither paths nor TTL, or no commit to anchor to; evidence
commands failing the read-only safety screen against the committed
allowlist (ADR-009; ADR-021 closed a tokenizer-parity bypass and
excludes `git`, `sed`, `awk`, and test-runners by design); evidence
commands whose two intake runs hash differently (nondeterministic,
overridable); and INFERRED claims with no `--basis`. The safety screen
is a **gate on execution**, not a flat peer: a command that fails it is
never run, unless `--evidence-unsafe-ok` bypasses it — which then
double-runs, applies the determinism check, and stores `screened: false`
for `recheck` to refuse forever (ADR-029).

**Override decay.** Since v0.9.14, a `--scope-ok` claim filed without an
explicit `--ttl-days` is stamped a default 30-day TTL (`ttl_default:
true`) rather than living forever; it is never refused (ADR-032).
Expiry rides the unchanged ADR-019 scan path, and ADR-030 arm 1 routes
the resulting stale claim to re-file — re-firing this same ADR-007
gate, so the scope judgment is mechanically re-asked on a schedule
rather than trusted once. An explicit `--ttl-days` remains the visible
opt-out.

**Invalidation.** A scan, wired to post-merge hooks or CI, demotes
claims whose premises git can check; anchor-loss after rebase/squash/gc
demotes as "anchor unreachable" — failing toward distrust.

**Verification.** `truth dispatch <id>` emits a fixed prompt plus the
claim record — never the authoring session's reasoning. The verifier
first runs a deterministic recheck (hash mismatch → diverge; command
missing → cannot_verify), then independently judges whether the evidence
supports the claim's *text* — "does this command still produce this
output" vs. "does this output support this sentence." Verifiers cannot
retract.

Since v0.9.12, `truth reaffirm` (ADR-030) automates the mechanical half
of that labor, never the judgment half. It walks stale claims, triaging
each into one of four arms: TTL-staled → skip (the re-file path,
ADR-019); mechanically unexecutable (`screened: false`,
screen-refused, or never agreed by any verifier — no prior judgment to
re-confirm) → skip, manual only; same-session → skip (ADR-010's seam,
batch edition); otherwise run the *same* screened recheck as `verdict
--recheck`. On a hash match it auto-files `agree` with basis
"reaffirm: hash-match, no judgment re-run", advancing the effective
anchor to HEAD (F2); on a **mismatch it files nothing** — the claim is
listed for real dispatch, never auto-agreed (INV-S). The distinction —
mechanical re-confirmation vs. first verification — extends ADR-012's
vocabulary from verdicts to labor. Named residual (ADR-030): when the
command reads less than the watch covers, a watched-but-unread change
stales the claim, the output still matches, and reaffirm re-agrees —
such agrees carry an audit field (`reaffirm_cleared`) for human
review.

**Policy.** `truth ready` intersects the tracker's unblocked issues with
premise validity, tier-sensitive: `live` passes; `unverified` passes
with a warning; `cannot_verify` blocks only P0; `stale`, `diverged`,
`disputed`, `retracted`, and missing always block. Work may proceed on
an unverified premise that later proves false — a stated trade for low
filing friction. Since v0.6.4 (ADR-013) a *genuinely dead* premise can
be redirected by an auditable supersede event, refused while the old
premise is live or unverified; the replacement is judged by the same
matrix, so the redirect re-targets protection rather than removing
it.

That is the entire mechanism: an event log, a derivation function, entry
gates, exit triggers, an independent recheck, a policy join. Nothing
above this line requires the word "Byzantine."

---

## 2. What it actually catches, with numbers

Two measurement windows, deliberately different in kind. **Window 1** is
the original pilot snapshot: an external repository, a 24–48 hour
window, self-reported, **not reproducible from this repository** — its
ledger is not part of this artifact; kept as the only measurement of the
target regime (a real product codebase under agent implementation work).
**Window 2** is longitudinal: the meta-repo's own ledger, ~12 days of
dogfooding, regenerated from a `truth stats --json` snapshot committed
beside this paper (`docs/paper-data/stats-snapshot-2026-07-20.json`) —
reproducible.

### 2.1 Window 1 — the pilot, 2026-07-08 → 2026-07-09 (external, unreproducible)

**Counting rule** (without which the verdict rows cannot be derived from
the raw ledger): "dispatches" counts verdicts filed under the trial's
dispatch protocol, per the pilot's trial log — excluding the author's
re-verification agrees after mechanical path-touch stalings, and
decay-event triage verdicts. The raw ledger holds 42 agree and 5
diverge; the delta is the exclusions.

| Measure | Value |
|---|---|
| Verifier dispatches (counting rule above) | 32 |
| — agree | 29 |
| — diverge, genuine (claim wrong) | 2 |
| — diverge, mechanical (recipe changed, fact true) | 1 |
| — cannot_verify | 0 |
| Diverges outside the protocol: decay (true when filed, later killed by a legitimate commit) | 2 |
| Claims in ledger | 21 (15 live, 6 retracted) |
| Human retractions (`TRUTH_HUMAN=1`) | 6 — all by the human, none by an agent |
| Agent sessions writing one ledger | dozens, zero corruption — but appends serialized: no session time-ranges overlap, so the `O_APPEND` race was never exercised |
| Tripwire recall & precision (two real refactors) | recall 2/2 — every fact-killing commit staled its claim; precision 1/3 in the first event (coarse tripwires on unrelated edits), 1/1 in the second |

**The dominant real failure mode is scope overreach, not
hallucination.** Both genuine divergences shared one shape: a *correct*
evidence command backing an *overreaching* claim text — a repo-wide
clause ("the only occurrences in the repo are…") backed by a
package-scoped grep whose `--include` filter did invisible work. Same
author, same defect shape, caught twice (n=2 — a signal, not a
distribution). Attribution honesty: one catch carries its verifier
session id in the verdict record; the other rests on the trial log.
Zero fabricated claims were observed — evidence about what kind of
failure this tool is built to catch (§6.1). Scripted
independence held and exceeded its brief: dispatch-only verifiers caught
the author both times, twice going further than asked — tracing a claim
about commit-time enforcement to the actually-active hook manager, not a
vestigial config path — F4's pattern (§4).

**A second deployment** (first records 2026-07-10): a distinct agent in
a distinct repository (`temporal-go-agent-sdk`) reproduced the taxonomy
— one genuine divergence, again the quantifier/scope shape; one
mechanical (ADR-012); zero fabrications. Same operator, so §8
item 1 extends — corroboration, not replication
(`docs/field-notes-sdk-session.md`; one finding became ADR-013).

**The repairs held in the field window.** Re-verified claims stayed live
across scans; human-gated retraction was exercised six times, correctly;
near-duplicate intake fired once, consciously overridden; confluence was
re-confirmed by shuffling the full pilot ledger and refolding. But the
concurrent-append race was never exercised, only provisioned for — one
machine, serialized sessions (§8).

### 2.2 Window 2 — the meta-repo, 2026-07-08 → 2026-07-20 (longitudinal, reproducible)

The template's repository operates its own ledger (a third deployment
site). Headline numbers from the committed snapshot: **1,363 records —
63 claims** (38 live, 8 retracted, 7 unverified, 7 stale, 3 diverged),
**614 verdicts** (597 agree, 7 genuine diverge, 2 mechanical, 0
cannot_verify, 8 retracted), **575 invalidations**, 41 issues with 70
issue events. Half-life medians: **~0.02 days in every tier** (n = 48 /
432 / 74 for P0/P1/P2) — claims watching hot paths re-stale within the
hour. Queue at snapshot: 3, max age 1 day.

**The churn finding.** ~9.5 agree verdicts per claim in twelve days; a
verification *hit rate* — verdicts finding anything (genuine +
mechanical) over all filed — of **~1.5%** (9/606). Re-verification
churn, not filing, is the dominant operating cost in this regime;
roughly 98.5% of that labor re-confirms what was already believed. This is the finding §8 item 2 weighs and the reaffirm
verb (§1, v0.9.12) exists to answer: the mechanical 98.5% is exactly the
hash-match arm reaffirm automates, and whether it recovers that labor
without leaking wrong auto-agrees is a measured question of the running
trial. §9's blast-radius convention is the older mitigation: narrow
watches shrink the denominator at filing time.

Window 2 is *not* a second independent measurement of the taxonomy —
same operator, and a meta-repo's claims are mostly about the tool. It
adds duration (12 days vs. 2), volume (614 verdicts vs. 37), and
reproducibility.

---
## 3. The audit method

Seven instruments, each targeting a defect class the others miss:

1. **Consistency audit of the specification** — diff every
   representation of the contract (README, schema, code, diagrams); two
   copies will drift.
2. **Seeded-fault acceptance testing** — run the shipped fault suite,
   then audit its *coverage*: which stated properties does no fault
   exercise?
3. **Property-based and permutation testing** — state invariants as
   universally quantified properties, search for counterexamples
   (Claessen & Hughes, 2000); for a union-merged event log the decisive
   property is confluence.
4. **Adversarial capability enumeration** — for each capability each
   actor *actually has*, attempt to violate an invariant using only it.
   Every property lands in one bucket — prevented, detected, or
   accepted-and-documented; anything in no bucket is a finding.
5. **Boundary and degenerate-case analysis** — empty logs, duplicate
   ids, same-timestamp events, glob edge cases, rewritten history.
6. **Fail-open analysis of the detectors** — does a detector run when
   its optional dependency is absent; if not, does the suite fail or
   silently pass?
7. **Independent reproduction and recursion** — every finding
   demonstrated by a runnable script against the real artifact in a
   fresh sandbox; every repair passes the *original* acceptance suite,
   unchanged.

The organizing rule: evidence is survival of a genuine attempt at
refutation, not accumulation of green runs — a hundred passing runs are
worth less than one well-aimed attack that fails to land. **Scope:** the battery ran in full against v0.4; mechanisms
shipped since (work kernel, satellites, the v0.6–v0.9.x hardening) are
canary- and unit-gated as they land but have had no equivalent full
audit pass.

---

## 4. Findings and repairs

Eleven defects: six from the original audit (v0.2/v0.3 → v0.4), three
found later by inspection in deployment, two by post-v0.4 reviews —
outside the frozen audit scope but the same evidence class: a stated
property falsified by a demonstration. Severity: Low (cosmetic / documented risk) < Medium (wrong status under
a narrow condition) < High (wrong status in normal operation) < Critical
(a headline invariant falsified by an attack no gate covered).

| # | Finding | Severity | Demonstration | Caught by shipped tests? | Fix |
|---|---|---|---|---|---|
| F1 | Schema stale against code on two features; drift detector fails open (silently skips) without an optional dependency | High | Real CLI produced a ledger the schema rejected; suite reported `OK (skipped=2)` | Only if the dependency was installed | Schema updated; a missing dependency is now a **test failure** unless waived — fails closed |
| F2 | Re-verified claims re-stale every scan — anchor frozen at filing, never advanced | High | stale → agree → live → next scan, zero edits → stale again | No | `agree` on path-anchored claims advances an **effective anchor**; the scan diffs from it |
| F3 | Fold not confluent under union merge — `{agree, diverge}` folds to `live` or `diverged` by merge direction | Medium | Exhaustive permutation check | No | Fold sorts into total order `(timestamp, id, canon)` before replay — CRDT total-order replay (Shapiro et al., 2011a) with per-field disciplines, only status LWW (§6.3, ADR-020); confluent on the verdict path too — backdating a verdict only lowers its key (ADR-008 warning) |
| F4 | "Retraction is humans-only" enforced nowhere — CLI checked a basis was present, never the actor | Medium | Verifier-actor retraction accepted | No | v0.4: requires `TRUTH_HUMAN=1` — self-attested. Hardened v0.6 (ADR-011): the variable alone refused — a tombstone also needs a typed-id confirmation or `TRUTH_HUMAN_ACK=<exact-id>`, closing the one-export bypass the refusal itself used to teach (§8 item 5) |
| F5 | Evidence-path globs cross directory separators (`src/*.py` matches `src/sub/deep.py`) | Low | Direct check | Partially | Custom translation: `*`/`?` stop at `/`, `**` spans |
| F6 | **Tombstone resurrection by pure append** — a duplicate claim record bearing a retracted id resets status to `unverified`; both shipped gates pass it | Critical | A retracted P0 claim — *"the database is safe to drop"* — resurrected through both gates and `validate` | No — the canary seeded this only on the verdict path | Fold ignores duplicate claim ids (first wins); commit gate replaced with a line-prefix check; duplicate-id *substitution* refused at commit by ADR-031 (§1) |
| INV-M | **Dead tripwire** — space-separated `--paths` silently stores as one literal matching nothing; the claim is true, the hash matches, the verifier agrees, the trigger can never fire | High | Found by inspection in the pilot ledger, not by any gate | No — nothing checked protection metadata | Shipped (v0.5.4): intake refuses whitespace-no-comma entries and literals matching zero tracked files; explicit globs exempt (a dormant watch is legitimate). `FAULT T`; the fix also caught a live canary fixture bug |
| F7 | **Issue-fold premise-stripping by pure append** — the issue fold was last-wins on duplicate `wk-` ids; an appended duplicate with `premises: []` silently disarmed ADR-001 protection | High\* | A HELD issue flipped to READY after one raw append; `validate` still passed | No — the one unit test on this path asserted the vulnerable behavior as a feature | `fold_issues` is now first-wins, identical to `fold()` (ADR-006); "update-by-refile" described a verb the CLI never implemented — last-wins was pure attack surface |
| F8 | **Schema-mirror drift, recurrence of F1's class** — the stdlib mirror accepted a claim with no `text`; `truth claim ""` filed a record the INV-B gate would then block — a CLI contradicting its own gate | Low | Live probe: `validate: 1 record(s) OK` on a text-less payload | No — the conformance corpus carried no missing-text fixture | Shipped (v0.5.5): mirror and intake refuse empty text; corpus fixtures added; the recurrence upgraded "keep the corpus exhaustive" to structural future work (FS-2, §10) |
| ADR-028 | **Intake↔fold seam on issue events** — a schema-valid *future-dated* issue record (raw-appended; no CLI path creates one) folds as `open`, but `done`/`--cancel` validate against the folded status, print success, and append an event whose honest `ts` sorts *before* the issue record — dropped as a forward reference; the issue stays open, un-closable, every attempt lies | Medium | CLI-reproduced by adversarial review | No — no test composed the transition check with fold order | Shipped (v0.9.9): intake refuses acting on a future-dated issue; `order_check` fails any `issue_event` sorting before its referent; tests + FAULT IF |
| Hollow VERIFIED | **A stably-failing evidence command verifies cleanly** — double-run and recheck compare hash and exit code for *stability*, not success; a deterministically failing command files VERIFIED and rechecks green — the class label promises a demonstration the evidence never made | Medium | Two real instances in field notes: VERIFIED completion claims with stably-failing evidence | No — nothing examined the exit code's sign | Shipped (v0.9.11): loud, non-blocking stderr warning on non-zero evidence exit; files normally — queue, not gate, since a legitimately-failing probe (`grep` proving absence) exists; TestEvidenceExitWarning |

\* By this table's own definition, F7 reads Critical: the gate `truth
ready` exists to enforce was falsified and nothing caught it. Rated High
because the enabling *capability* — an attributable forged append with a
chosen `ts` — is the already-accepted §8 item 6 class; F7 is an
unexamined application, not a new capability. A judgment call against
the scale — a second auditor may reasonably disagree.

**Verification effort at repair time (v0.4):** 41 unit and conformance
tests green with the schema detector armed; 12 new regression tests;
19/19 seeded faults caught, up from 14 — the original 14 unchanged and
green, which demonstrates behavior preservation.

**What survived attack** (negative results — a method that only reports
hits measures nothing): retraction terminality on the
verdict path; all intake gates as documented; scan idempotence;
degenerate ledgers; the readiness matrix cell-for-cell; anchor-loss
failing toward distrust; the dispatch seam leaking no reasoning; the
core a pure function of the **log**, touching no I/O (ADR-019) — the
log-purity that made unit-level attacks cheap.

**A prediction the evidence refuted:** F1's root cause was predicted to
be fixture-corpus omission. Wrong — the corpus contained both cases; the
real cause, a detector failing open on an absent dependency, was worse
for process and better for design. Recorded because a method that cannot
be surprised tests nothing.

**The recursive episode, twice.** The first F3 fix used
second-granularity timestamps; same-second ties fell to a random
tie-break — the original, unchanged acceptance suite caught its own
auditor's bug (fixed with microsecond timestamps). Months later a
dead-name pre-commit check fired on the very commit introducing the
naming convention it enforces, and again on its author's later edit. A
pattern worth watching, not an established mode — kept out of §7's
table, since two data points support no real falsifier.

---

## 5. What generalizes: citation over restatement

One pattern recurred across every mechanism the pilot grew: **facts
restated in prose rot; facts cited by id stay checkable** — Lehman's
structural growth absent counter-effort (1980), applied to knowledge
about code. Four mechanisms fell out of it — three grown in the pilot
and shipped upstream, the fourth in the meta-repo (§2.2's site):

- **Work kernel** — work items are ledger records with a premise at
  birth and a completion claim at death; readiness requires open
  status, closed dependencies, *and* valid premises.
- **spec-health** — specs may state facts only by citing ledger ids; a
  sweep judges every spec by the readiness of its cited ids. A cold
  review of the pilot's first spec found the convention's blind spot — a
  fact premised by no cited work item is invisible to the check — now a
  warning.
- **doc-health** — the same discipline for prose: forbidden post-rename
  names, broken relative links. A sweep of the pilot's live markdown
  corpus (105 files per the sweep agents; 99 per `git ls-files` — a
  counting-set difference on the record) found decay **concentrated
  entirely in pre-ledger prose**: every document written under the
  citation convention came back clean but one routing gap.
- **doc-coverage claims** — a VERIFIED claim binding a document's
  load-bearing coverage to the code surface it describes, watching
  *both* paths with a sentinel recipe: code growth then mechanically
  stales the claim, converting "does the doc still cover this?" from a
  hoped-for review into a queue item. Installed in the meta-repo after a
  manual review found its instruction file documenting half the CLI —
  the desync class spec-health cannot see, guarding cited ids, not
  coverage. Across the four template releases that followed, the
  tripwires forced doc re-review each time. Residuals, learned the same
  week: recipes narrower than their sentences survive intake (one claim
  retracted for it), and a watch on a tracked symlink can never fire —
  the undecidable end of the spectrum whose decidable end INV-M gates
  (Appendix A).

That last result is evidence for a claim the original design never
made: citing a fact by id, rather than restating it, may *prevent* decay
at authorship, not only detect it. One repository, one sweep, is not a
controlled trial; the distribution (100% clean post-convention, all rot
pre-convention) is a plausible signal worth a real test, not a
demonstrated effect. The transferable idea, held to the same caution, is
the pattern: an artifact class admitted into a repository plausibly
needs its own health tripwire at admission, or it risks becoming archive
material — a hypothesis this pilot is consistent with, not one it
proves.

---
## 6. Interpretive framings

This section names the theoretical vocabulary that motivated the
design, corrected against the field evidence. None of it is required to
operate the artifact — but §6.1 isn't decoration: it's the analysis §2
promises. §6.3 records the inverse — vocabulary the design *converged
on*
unmotivated, the more evidentially valuable kind for a single-author
artifact (§8 item 1); §6.5 positions the composition against its kin.

### 6.1 Byzantine fault tolerance — as analogy, corrected

Byzantine fault tolerance (Lamport, Shostak & Pease, 1982; Castro &
Liskov, 1999) formalizes agreement when components fail arbitrarily; its
transferable idea is structural — trust need not be a judgment about a
component but a checkable property of a protocol's redundancy. This
system borrows that *move* — replace "do I trust this claim" with "does
the structure guarantee a false claim is detected" — and none of BFT's
machinery: no quorum, no `3f+1` bound, no vote. Not a consensus
protocol; it targets one operator's sessions, not mutually distrusting
replicas.

The original motivation mapped failure classes directly: crashes to
unverified claims, omissions to silently outdated facts, Byzantine
faults to hallucinated or forged claims, correlated faults to a verifier
sharing the author's priors. Field measurement (§2) found none of the
pilot's real defects in the Byzantine or correlated rows — zero
hallucinations in 32 dispatches. The dominant real fault, scope
overreach by an honest actor with honest evidence, has no row at all:
not a crash, omission, lie, or shared bias, but a mismatch between a
natural-language quantifier and the domain of the command supposed to
support it — a fault category native to *this* domain. The honest conclusion: BFT
contributed a useful stance and an overclaimed taxonomy — a starting
enumeration, not a closed one.

### 6.2 Entropy — as unformalized metaphor

At verification, uncertainty about a claim drops to near zero and the
anchor commit timestamps the moment; every later event that *could*
invalidate it reinjects uncertainty, because the observer cannot know
without re-checking. Under this reading `evidence_paths` and `ttl_days`
model a fact's decay channels, and `stale` is the admission that
accumulated uncertainty crossed a threshold. A framing, not a formalism:
no entropy is computed anywhere. Since v0.6 the mechanical half exists
(FS-1): `truth stats` reports per-tier half-life from the ledger's
history, and past ≥5 observations intake prints the observed median
beside the author's TTL — a suggestion, never a substitute. §2.2's
medians (~0.02 days, every tier) are its first longitudinal output;
whether the suggestion is *calibrated* remains unmeasured, and the churn
it quantifies now has a shipped countermeasure (reaffirm, §1) whose
efficacy is part of the running trial.

### 6.3 Architectural lineage, corrected — vocabulary the design converged on

The v0.4–v0.6 mechanisms were designed against local evidence (§2, §4),
not from the literature; this section names, after the fact, the
classical constructions several turn out to be instances of, each with
the correction stating where the artifact stops short of its ancestor.
The point is not pedigree: under §8 item 1's single-observer limit,
independent convergence on decades-old results is the nearest available
substitute for external review — the original analysis applies, and its
known failure modes become checkable predictions here.

**The fold, as CRDT constructions.** The ledger is a grow-only set of
events (G-Set); the fold applies three per-field merge disciplines —
claim **content** first-writer-wins (a write-once register, F6's fix),
**status** last-writer-wins in `(ts, id, canon)` order (F3's fix, made
total by ADR-016), `retracted` **terminal** (the 2P-Set tombstone rule;
Shapiro et al., 2011a, catalog 2011b) — composed into one total status
function (ADR-020, §1) absorbing on the *folded* status, so a backdated
verdict only lowers its own key. Each discipline is standard; local is only the composition and the
audited record of why each was chosen. Correction: CRDT theory buys
convergence across unavailable *replicas*; this design spends it on
union-merged branches of one repository — §8 item 4 stands.

**The rest, one correction each.** *Local-first software* (Kleppmann et
al., 2019): no server, user-owned plain files, git as the trusted sync
transport — but local-first's ideal is real-time collaboration, and this
design claims none of it (the sync layer exists; the collaboration
layer, never built). *Optimistic concurrency control* (Kung & Robinson,
1981): never block an append, validate at commit — but OCC retries its
loser; here nothing retries, a validation failure feeds a human
decision, because the conflicting party may be a prompt-injected agent
whose "retry" must not happen. *The confused deputy*
(Hardy, 1988): ADR-011's `TRUTH_HUMAN_ACK=<exact-id>` designates the
object it authorizes, so a lingering ambient variable cannot be spent on
a later target — but there are no actual capabilities, identity stays
self-attested (F4, §8 item 5); corollary, **agent-facing refusal text
is itself attack surface** — the gates refuse without teaching the
override, prompt injection's hazard arriving in the tool's own
refusals. *The borrowed event loop*: the system owns no process — git
hooks supply transactional moments, harness hooks attention moments
(ADR-005, FS-4) — so liveness is only as strong as the hook wiring,
hence `doctor` checks the installation, decidably (ADR-025).
*Older lineage*: derive-don't-store is event sourcing (Fowler, 2005)
and half the immutability argument (Helland, 2015); `ttl_days` is DNS's
decay model (Mockapetris, 1987); journal → ledger → trial balance is
double-entry bookkeeping's pipeline — strictly metaphor.

### 6.4 Standards lineage — the obligations this mechanizes

The Standards table is not decoration: each entry names an obligation
the engineering standards have prescribed for decades and that teams
satisfy, in practice, with meetings, wikis, and hope. The artifact
invents no new obligations — it mechanizes existing ones at the one
point where they have been unaffordable: per sentence, at authorship.
Each bullet states the practitioner problem, anchored to the standard
that already names it.

- **Knowledge outlives its validity** — a fact confirmed Tuesday is
  silently falsified by Thursday's merge, and no artifact records the
  transition. ISO 10007 names the remedy *configuration status
  accounting*: at any time, every item's status is known. The ledger
  extends CSA to *statements about* artifacts — every claim has a
  derivable status, and a code change mechanically demotes what it may
  have invalidated (§1).
- **"Checked" and "believed" are typeset identically** in standups, PR
  summaries, and estimates. ISO/IEC/IEEE 12207 separates *verification*
  (was the check performed correctly) from *validation* (is it the right
  check). The artifact enforces the split twice: evidence classes make
  belief-vs-check explicit at filing, and the verifier protocol
  separates re-running the command from judging whether its output
  supports the *sentence*. §2's dominant failure — a correct grep
  backing an overreaching quantifier — is a validation failure hiding
  behind passing verification, which is why ADR-007 gates it at
  intake.
- **"What breaks if this assumption is wrong?" is unanswerable in either
  direction.** ISO/IEC/IEEE 24765's forward/backward traceability,
  usually requirements↔code↔tests, is applied assumptions↔work: premise
  records give backward traceability (this work rests on these claims);
  `impact` and watched paths give forward (this change reaches these
  claims, blocking that work). `ready` is the traceability graph as a
  gate.
- **Requirement hygiene is prescribed but never enforced at
  authorship.** ISO/IEC/IEEE 29148's characteristics — unambiguous,
  verifiable, singular; set-complete, set-consistent — are the intake
  gates (§1) restated as refusals: empty text, a universal quantifier
  over a scoped command, a near-duplicate, VERIFIED-without-evidence, a
  statically dead tripwire (unfalsifiable — INV-M).
- **"Done" means someone said so.** ISO/IEC/IEEE 29119's
  requirement-based coverage appears as the acceptance oracle (ADR-014):
  `done` refuses unless the committed command exits zero and the
  completion claim files with evidence — closure becomes measured.
- **Descriptions decay into fiction with nobody assigned to notice.**
  ISO/IEC/IEEE 42010's correspondence rules — a description must
  demonstrably correspond to the system — are mechanized by doc-coverage
  claims watching both the document and the code surface it describes
  (§5); ISO/IEC 25010/25023's functional completeness gets the same
  treatment, "module X covers Y" becoming a claim with a lifecycle.
- **The agent-era amplifier.** Every standard above assumes a human
  review loop; LLM agents produce confident assertions faster than any
  such loop scales, and §2 says their dominant failure is scope
  overreach, not fabrication. The artifact's answer: make the
  obligations cheap enough to apply per sentence — file with evidence,
  demote mechanically, verify independently, gate work on the result.

The calibration owed every framing applies here too: the mapping above
is the *problem statement*, not evidence that the mechanisms answer it
economically. Whether the ledger net-helps — caught staleness minus
§2.2's churn — is §8 item 2's open question, unresolved until §10's
control comparison runs. The standards establish that the obligations
are real, not that this is the cheapest way to meet them.

### 6.5 Nearest functional kin — and what remains unclaimed

§6.3 is ancestor-heavy; this section names the *systems* that already
mechanize part of the job (refs 16–20). Closest is assurance-case
maintenance: safety-case evidence going stale under change, maintenance
first-class but manual (Kelly & McDermid, 1999/2001), and Dynamic Safety
Cases proposing continuous automated invalidation of that evidence
(Denney, Pai & Habli, 2015) — the same concept, never shipped as
tooling. TUF's `expires` is TTL demotion with signatures, no
re-verification lifecycle (Samuel et al., 2010). in-toto's link
attestations are this design's evidence capsule, signed but static — no
invalidation, no staleness (Torres-Arias et al., 2019). Just-in-time
comment-code inconsistency detection mechanizes "this commit invalidated
that sentence" — learned, comments not claims, no ledger (Panthaplackel
et al., 2021). A commercial doc-freshness family ships watched-path
staleness checks in CI (Swimm, Dosu, Fiberplane — practice, not
literature). §3's method is fault seeding / mutation analysis by another
name (Mills; DeMillo, Lipton & Sayward, 1978 — ref. 10).

The novelty claim is deliberately narrow: **each element is known; the
composition is unprecedented** as far as this review could establish —
natural-language claims + executable evidence capsules + git-anchored
content-diff demotion + TTL decay + independent re-verification + a
confluent fold over a union-merged log, with a recoverable status
lifecycle, as zero-infrastructure developer tooling. A prior system with
that composition falsifies the claim, and §7's table gains a row.

---

## 7. This paper's own claims, and what would falsify them

Applied to this document the discipline it applies to the artifact —
Popper's demarcation as an acceptance criterion, not a philosophical
commitment (Appendix A is one row per property, naming falsifier and
gate; §3 attacks the falsifiers themselves, since a weak one passing
proves nothing): each claim below is falsifiable by a specific
observation.

| Claim | Falsified by |
|---|---|
| Hallucination is not the dominant failure mode in this deployment regime | One confirmed fabricated claim (no basis in reality, not merely scope overreach) anywhere in the pilot ledger's history |
| Scope overreach, not fabrication, is the pilot's dominant real failure | A third genuine divergence whose cause is not a quantifier/evidence-domain mismatch |
| The v0.4 repairs hold under the pilot's use | Any corruption, lost update, or non-confluent fold in the pilot's git history of `.truth/claims.jsonl`, scoped to commits made under an installed commit gate (§8 item 5 — a pre-gate day-0 restructure once deleted a committed ledger line, the standing demonstration of why the scope clause is needed) |
| Citation discipline is *hypothesized* to prevent documentation decay, not only detect it (§5) | A post-convention document containing undetected rot, discovered by any means other than the doc-health sweep itself |

**Falsifier scoreboard (first external audit, 2026-07-19).** Row 3's
falsifier was attacked and survived: a parent-aware audit of all 208
commits touching the pilot ledger found zero non-merge prefix violations
and zero lost lines, and both ledgers fold identically under random
permutation. Row 4's tripwire
**fired**: an independent scan found stale load-bearing script paths in this
paper's own Appendix B and the README — post-rename rot in
post-convention documents, invisible to the sweep *by design* (backtick
paths are unchecked). Repaired the same day; the hypothesis
stands only with that blind spot stated — the sweep guards links and
names, not backtick paths, and reproduction instructions are where the
exemption bites.

The first two rows share one dataset — 32 dispatches, 2 genuine
divergences, same author — two readings of one small sample, not two
confirmations. Their falsifiers are deliberately hair-trigger: one
fabricated claim would not mathematically overturn "not dominant," nor
one differently-caused divergence "dominant" out of three. Read both as
tripwires prompting re-examination, not negations.

**Deliberately absent**, by the table's own admission rule: *this
system generalizes beyond a solo-developer regime* (not a claim this
paper makes; §8 item 4 names it an open limit) and *recursive
self-catching is a repeating pattern* (two instances support no
falsifier — narrative only, §4).

The single largest claim this paper does *not* make: that the ledger
reduces false-VERIFIED rates in practice. Everything above concerns
mechanism — the machine detects what it is built to detect. Whether it
*helps*, net of the friction it adds, requires §10's control comparison,
not yet run.

---
## 8. Honest limits, ranked

Ranked by how much a skeptical reader should discount everything above:
item 1 conditions trust in every number in §2 and defect in §4, so it
leads even though item 2 names the largest single *unanswered
question*.

1. **Single-observer conflict of interest, in both halves.** The audit
   battery was assembled by one auditor; the pilot's operator is also
   the artifact's and this paper's sole author. Every number in §2 and
   defect in §4 is self-reported by the person who built the thing
   measured. Independent replication is the real check; it has not
   happened.
2. **Efficacy is unmeasured — and the cost side is now measured,
   unfavorably.** The largest open *question*, conditional on item 1.
   §2.2 quantifies the friction denominator any trial must divide by:
   ~1.5% verification hit rate, ~0.02-day half-life medians —
   re-verification churn, not filing, is the dominant cost.
   Since v0.9.12 the finding has a shipped countermeasure (`reaffirm`,
   §1), making the trial two-sided: does the ledger net-help, and does
   the countermeasure recover the churn without leaking bad
   auto-agrees. The first monthly hand-audit is due ~2026-08-08 — a
   future revision's number, not this one's.
3. **The field window is short.** §2.1 covers roughly 24–48 hours; §2.2
   adds twelve days, same operator. "Dominant failure mode" describes
   those windows, not a steady state — every §2 count is provisional
   until the deployments run for months.
4. **Single-regime evaluation.** One solo developer per repository, one
   machine. Multi-human, multi-machine concurrency is untested — the
   regime stressing confluence and `O_APPEND` hardest.
5. **Agent compliance is behavioral, not technical.** The layer is
   discovered through a few lines of instruction-file text; a runtime
   that never loads them bypasses everything. Held so far — but the
   operator is also the layer's author, so discovery by unbriefed agents
   is untested. The sharper edge is the *commit gate*: INV-A, INV-B,
   INV-G, INV-N, and the ADR-031 refusal are enforced by `check-truth`
   at commit, which runs only where a hook or CI is installed — where
   neither is, they are silently unenforced. This is the README's one MUST; `doctor` makes it decidable (ADR-025),
   and the residual — `doctor` opt-in, its CI arm self-certified — waits
   behind the growth gate with signed records (item 6).
6. **Timestamp forgery is accepted, not solved — but its worst
   composition is now refused.** An appender chooses its own `ts`; the prefix gate makes forged appends
   permanent and attributable but does not prevent backdating. The composition with duplicate-id dedup — a
   forged duplicate winning content under first-wins — is refused at
   commit in every `ts` shape (ADR-031, §1). The residual is forgery on
   a fresh id; cryptographic prevention stays behind a growth gate (§10)
   rather than half-built.
7. **Vocabulary debt — named since v0.6.** "Diverged" conflated "reality
   changed" with "the command's output format changed." ADR-012 names
   the second: `diverge --mechanical` records a recipe-change subtype;
   queue and `stats` report the rates separately. Open: whether the
   distinction is applied consistently — shipped, calibration
   unmeasured.
8. **Override decay's instrument is evadable, not just uncalibrated.**
   ADR-033's verbatim-repeat advisory — flagging a `--scope-ok`
   justification re-filed unchanged after a decay expiry — is defeated
   by a single synonym swap or appended token; the red team demonstrated
   this directly. The backstop is the raw counters
   (`scope_basis_filings`, `decay_expiries`), which increment regardless
   of text evasion; the advisory is a convenience pointer, not the
   measurement. Both ADR-032's decay and ADR-033's report are new as of
   v0.9.14 — outside every field window §2 covers, with their own
   adoption-gate calibration debt folded into the same R11 clock as
   item 2.

---

## 9. Adopting this

The friction budget is a design constraint, not a marketing claim: one
command to file a claim, four lines of instruction-file text for an
agent to discover the layer. Five field-earned conventions are worth
adopting alongside the code — three from the pilot, two from the second
deployment (§8 item 1 extends to them):

- **Never write a repo-wide clause backed by a package-scoped command.**
  Name the by-design survivors explicitly. (Intake refuses this shape
  unless `--scope-ok` justifies it — ADR-007.)
- **Commit the work, then file the completion claim** — a claim filed
  before its shipping commit can be staled by it within seconds.
- **Pin evidence output that embeds counts** (`"0 failures across 70
  docs"` diverges as the corpus grows though the fact holds); prefer a
  stable sentinel like `... && echo CLEAN`.
- **Scope `--paths` to the narrowest set that actually backs the claim**
  — for *blast radius* as much as correctness: a broad watch drags
  unrelated-but-true claims into the queue on every edit to a hot file
  (one commit re-staled 8 claims, 6 still true). §2.2's churn is what
  this convention exists to contain.
- **Reserve an ADR namespace before writing your own.** The template
  owns `docs/adr/NNN` and extends it on `copier update`; claims cite ADR
  numbers immutably, so a collision can only be namespaced, not
  renumbered away (the second deployment hit this).

Requirements: POSIX, git, Python 3; `jsonschema` if the schema-drift
detector should run armed rather than fail closed (block, the
default).

---

## 10. Future work

- **The efficacy trial** — §8 item 2's gap: longitudinal false-VERIFIED
  rate, with and without the ledger, across repositories and runtimes —
  plus a second arm, reaffirm's leak rate against the labor it
  recovers.
- **A scoping-fault countermeasure beyond discipline — shipped (v0.6,
  ADR-007), its ritual-rot risk now countered too (v0.9.14, ADR-032):**
  a `--scope-ok` justification filed without an explicit TTL decays on
  a 30-day default and re-fires the same gate on re-file, rather than
  sitting live forever. Measured by the override-velocity report
  (ADR-033). Remaining: both false-positive rates — decay-expiry-vs-
  genuine-diverge, and the verbatim-repeat advisory's own evadable FP
  class (§8 item 8) — unmeasured until two rot-free R11 hand-audit
  windows accumulate.
- **Integrity upgrade, behind the growth gate.** Earlier revisions
  proposed hash-linking each record to its predecessor (Haber &
  Stornetta, 1991) as the signature-free answer to §8 item 6. A red-team
  pass (2026-07-20) falsified the linear chain **for this regime**: two
  honest concurrent `O_APPEND` appenders extend the same predecessor and
  fork the chain, and a git union merge then breaks linear verification
  in both directions — a linear chain would refuse exactly the honest
  concurrency §1 provisions for. The
  named successor is the **fork-permanent hash TREE** design archived in
  `docs/growth-gate/` (TLR-002/013/014, with executable spec
  `test-tlr-fold.py`, 18/18 checks including negative controls): records
  link as a Merkle *tree*, forks are permanent and verified rather than
  refused, derive-time linearization replaces wall-clock order. One
  piece is already adopted (ADR-031, from TLR-013); the rest is built
  only when the growth gate trips — the first forged timestamp found in
  the wild. Until then, git's commit DAG over the INV-A-gated file binds
  sequence and content: every append is attributable, and a rewrite
  needs a visible force-push.
- **Claim half-life measurement — shipped mechanically (v0.6, FS-1;
  §6.2).** Still future: enough history for the suggestion to mean
  anything, and a calibration check against ground truth.
- **Generate the validate mirror from the schema — the corpus half
  shipped (v0.6, FS-2).** F1 and F8 are one defect class twice:
  hand-maintained contract copies drifting. FS-2's mutant generator
  holds mirror and schema in lockstep; the build step deriving one from
  the other is unbuilt, acceptable while the corpus holds.
- **Formal verification of the fold** — exhaustive model checking
  (TLA+/Alloy) of confluence and terminality, replacing sampling with
  proof.
- **Cross-language reimplementation as replication** — a port using the
  unchanged seeded-fault suite as its acceptance oracle: an unusually
  clean independent replication, and a direct answer to §8 item 1, which
  nothing else here resolves.
- **Attestation upgrade** — session-manifest attestation (everything a
  claiming session executed, not just its final command) if recheck-only
  verification proves too narrow.

---
## Appendix A. Invariant table (v0.4 core through v0.9.14)

Every shipped property a seeded fault gates belongs here — a row is
added when the property ships, not later. That rule has been violated
twice (INV-O/P/Q, then INV-R, backfilled after reviews found them
canary-gated but row-less — Appendix C): the lag between "fault lands"
and "row lands" is exactly the decay §5 predicts, observed on this table
itself.

| ID | Property | Falsified by | Gate |
|----|----------|--------------|------|
| INV-A | Ledger is append-only: staged file is a line-prefix extension of the committed file | One edit, deletion, or insertion committed | Prefix gate — **conditional on the commit gate actually running** (an installed hook or CI config; `doctor` decides, exits 1 without it, ADR-025; where neither exists the invariant is silently unenforced, §8 item 5); the same conditionality applies to every "refused at commit" row |
| INV-B | VERIFIED claims carry command, hash, anchor, paths-or-TTL | One bare VERIFIED accepted | Intake tests |
| INV-C | Evidence-path changes demote before re-trust | One stale claim rendered live | Seeded fault |
| INV-D | Recheck detects non-reproducing evidence | One hash mismatch scored agree | Seeded fault |
| INV-E | TTL'd claims expire: the scan writes an invalidation when `now - ts > ttl_days` (strict); only that record demotes — the fold never reads the clock (ADR-019) | One claim outliving its TTL; or one expired at fold time with no record | Seeded FAULT D; boundary + fold-purity tests |
| INV-F | History rewrites invalidate, with reason | One orphaned anchor still trusted | Seeded fault |
| INV-G | Retraction is terminal at both layers: the *status* stays `retracted` under any event; the readiness *block* is released only by matching human authority | One resurrected tombstone; or a HELD block released without the human gate | Seeded faults (verdict, append); content substitution under a retracted id refused at commit by ADR-031 (B1/B3–B5, K2; gate-conditional); supersede release human-gated unconditionally (ADR-017, R11). Residual: fresh-id forgery (§8 item 6) |
| INV-H | Broken premises hold work: a `stale`, `diverged`, `disputed`, `retracted`, or missing premise HOLDs its issue (the full ADR-001 blocking set) | One issue ready on such a premise | Seeded faults J, C1 (the matrix blocks all identically); the `cannot_verify` P0-only rule and `unverified` warn-pass are its non-blocking cells |
| INV-I | Fold is confluent: any event order, same state | Two orders, two statuses (or contents) | Permutation property test; the third order key is load-bearing (ADR-016; canary B6, core tests) |
| INV-J | Re-verification is durable across scans **for path-anchored claims**: `agree` advances the effective anchor. TTL'd claims exempt (ADR-019): re-filed, not re-verified | One re-verified path-anchored claim re-staled with no new changes | Seeded fault; ADR-019 amendment records the exemption |
| INV-K | Retraction requires `TRUTH_HUMAN=1` **plus** typed-id confirmation or `TRUTH_HUMAN_ACK=<exact-id>` (ADR-011) | One retraction accepted with the variable alone, headless | Seeded H-faults — still self-attested, but the one-export bypass is closed (F4) |
| INV-L | The drift detector is armed or the suite fails | One green run with the schema unchecked | Armed-detector test |
| INV-M | No `evidence_path` is *statically* dead at filing: every literal matches ≥1 tracked file, no whitespace-no-comma entries, no statically-unreachable globs (a static-deadness gate, **not** a liveness guarantee) | One accepted claim with a statically dead tripwire | Seeded `FAULT T` (ADR-023/024). A *reachable* glob is dormant — exempt. An *unreachable* glob (`.git/*`, absolute, trailing-slash, `.`/`..`/empty) can never match a normalized `git diff` path — refused, soundly but incompletely. The tracked-symlink literal is the undecidable residual — guidance, not a gate |
| INV-N | Issue-fold premise protection cannot be stripped by an appended duplicate `wk-` id | One HELD issue silently flipped to READY | Seeded FAULT R9 — duplicate issue ids first-wins, identical to INV-G (ADR-006); content-distinct duplicates refused by ADR-031 (every kind), with INV-G's residual and conditionality |
| INV-O | A verifier cannot `agree` with its own session's claim; same-session `diverge` IS allowed (self-incrimination) (ADR-010) | One same-session `agree` accepted, or `diverge` refused | Seeded faults V1–V3; session identity self-attested (F4 class) — the bypass is one visible env export |
| INV-P | A supersede redirect re-targets premise validity, never bypasses it: the replacement judged by the same matrix, refused while the old premise passes `ready`, human-gated for `retracted` (ADR-017) | One issue made READY by redirecting a live/unverified premise; a retracted premise redirected without human authority; non-deterministic resolution | Seeded faults R10/R11; cycle resolution pinned by tests |
| INV-Q | An acceptance oracle gates issue close: non-zero exit refuses `done`; an unscreened oracle is refused execution unless `--accept-unsafe-ok` stamps it visibly | One issue closed over a failing oracle, or an unscreened oracle executed silently | Seeded faults AC1–AC8 (ADR-014); `accept.executed=true` requires `returncode 0` |
| INV-R | Declared contradictions dispute both sides: while both endpoints would otherwise be `live`, both fold to `disputed` via a post-pass over the *underlying* statuses (order-independent, so INV-I survives); `disputed` blocks premises; a dormant edge changes nothing | One pair both `live`; one issue ready on a `disputed` premise; a dormant edge changing a status | Seeded faults C1–C5; TestDisputed core tests |
| INV-S | A reaffirm hash-mismatch is never auto-agreed: `reaffirm` auto-files `agree` only on an exact hash-and-exit match through the same screened recheck path; a mismatch files nothing; TTL-staled, unscreened, never-agreed, and same-session claims skip with reasons (ADR-030) | One mismatch auto-filed; or one skipped-arm claim executed or auto-agreed | Canary FAULT RA + core tests |
| INV-T | A `scope_basis` claim filed without an explicit `--ttl-days` is stamped a default `ttl_days=30` and `ttl_default: true`, and is never refused; an explicit `--ttl-days`, or no `scope_basis`, leaves the claim unchanged. Expiry rides the unchanged ADR-019 scan path (counted from the claim's own `ts`) — the fold reads no clock (ADR-032) | One default-stamped filing refused, or accepted without the flag; one explicit `--ttl-days` silently overridden by the default; one default-TTL claim demoted by any path other than the ADR-019 scan record | Seeded canary FAULT SD-decay (4 arms incl. negative control); core tests TestOverrideDecay + TestScopeDecayCLI |
| INV-U | `truth stats`'s `overrides` section counts scope-ok filings, ADR-032 decay expiries, overridden duplicates, and unscreened filings exactly, and flags as a repeat only a `scope_basis` claim whose `tokens()` set equals an earlier claim's that is now dead (stale/diverged/retracted) — a live/unverified prior is not flagged (ADR-033) | A verbatim re-justification after a decay expiry not flagged; or a genuinely narrowed re-file (token set differs in substance) flagged | Seeded canary FAULT OV (2 arms incl. negative control); core tests TestOverrideReport + TestOverrideReportCLI |

## Appendix B. Reproduction

All findings and repairs are demonstrated by scripts driving the real
CLI in fresh sandboxes. Relative to the repository root:
`template/scripts/truth` (CLI; root `scripts/truth` is a symlink),
`template/scripts/check-truth.sh` (commit gate),
`template/scripts/truth-canary.sh` (the seeded-fault suite — it prints
its own count; grown from 19 at v0.4), `template/scripts/test-truth-core.py`
(needs `jsonschema` importable or fails closed by design, F1),
`template/scripts/test-truth-v04.py`,
`template/.truth/schema/claims.schema.json`. §2.2 is reproducible from
`docs/paper-data/stats-snapshot-2026-07-20.json` and this repository's
own `.truth/claims.jsonl`. §2.1's numbers are read from the pilot
repository's ledger history — **not part of this artifact** — via §2.1's
counting rule. The append-only property does double duty as a research
instrument; the 2026-07-19 external audit (§7) exercised exactly that.

## Appendix C. Revision history

What v2 carried as dated in-place annotations, collapsed here (v3,
2026-07-20); one line per correction. The text above supersedes them —
this is the audit trail.

- 2026-07-12 — §6.3 added; second-deployment findings folded into §2/§9.
- 2026-07-13 — INV-M tracked-symlink residual recorded.
- 2026-07-18 — INV-O/P/Q rows backfilled; ADR-013 cycle amendment
  noted in INV-P.
- 2026-07-19 — §2 counting rule added (verdict rows underivable from
  the raw 42 agree / 5 diverge without the exclusions).
- 2026-07-19 — §2: "6 interleaved sessions" corrected to serialized
  appends, race never exercised; §7 row 3 narrowed.
- 2026-07-19 — §2 tripwire row: first refactor event (precision 1/3)
  added.
- 2026-07-19 — §2 attribution note: one of two catches
  instrument-attributable, the other rests on the trial log.
- 2026-07-19 — §2 confluence re-confirmed by shuffle-and-refold.
- 2026-07-19 — §4 F3 cell: "standard CRDT LWW move" corrected to three
  per-field disciplines, one LWW (§6.3, ADR-020).
- 2026-07-19 — §5 doc-health counting-set difference recorded (105 vs.
  99).
- 2026-07-19 — refusal-text-as-attack-surface corollary promoted from a
  code comment (§6.3).
- 2026-07-19 — nearest-kin block added from an external review (now
  §6.5), [unverified] until 2026-07-20.
- 2026-07-19 — §7 falsifier scoreboard added: row 3 survived attack, row
  4 fired (backtick-path rot, repaired same day).
- 2026-07-19 — INV-R (contradicts) row backfilled; INV-J TTL exemption
  recorded (ADR-019 amendment) after the re-stale loop was
  demonstrated.
- 2026-07-19 — Appendix B paths corrected to `template/…`.
- 2026-07-19 — references verified; Kung weakened, Claessen and Mokhov
  corrected, Barr title and Kleppmann URL fixed.
- 2026-07-20 — §6.4 standards-motivation section added.
- 2026-07-20 (v3) — annotations collapsed into this appendix; §2 made
  dual-window with a committed snapshot, churn promoted from §8 item 2;
  §4 gained ADR-028-seam and hollow-VERIFIED rows, §3 the v0.4-only
  audit-scope note; §1 and INV-G/N updated to ADR-031; reaffirm added
  (§1, INV-S — ADR-030); §10's linear hash-linking replaced by the
  growth-gate hash-tree pointer after a red-team falsified the chain;
  never-cited [proposed] references dropped, remainder renumbered, kin
  references verified; §6.5 added.

## References

*(Annotated; the → line states what each work is cited for. Entries 2–9
and 11–15 verified against publisher records 2026-07-19; 10 and 16–20
on 2026-07-20; re-verify before submission.)*

**1. Popper, K. (1959). *The Logic of Scientific Discovery.***
→ §7's framing: the paper states what would falsify its own claims.

**2. Lehman, M. M. (1980). Programs, Life Cycles, and Laws of Software
Evolution. *Proc. IEEE*, 68(9), 1060–1076.**
→ Analogy, not evidence: §5 transfers Laws II/VII to restated facts.
- DOI: https://doi.org/10.1109/PROC.1980.11805

**3. Kung, H. T., & Robinson, J. T. (1981). On Optimistic Methods for
Concurrency Control. *ACM TODS*, 6(2), 213–226.**
→ The never-block-append, validate-at-commit stance — not the
machinery: nothing aborts or retries.
- DOI: https://doi.org/10.1145/319566.319567

**4. Lamport, L., Shostak, R., & Pease, M. (1982). The Byzantine
Generals Problem. *ACM TOPLAS*, 4(3), 382–401.**
→ §6.1's design stance (the signed-messages result) and failure
model.
- DOI: https://doi.org/10.1145/357172.357176

**5. Mockapetris, P. (1987). Domain Names — Concepts and Facilities.
RFC 1034 (STD 13), IETF.**
→ `ttl_days`: decay for facts the source cannot push to you; a DNS
re-fetch restarts the TTL, re-verification here never does (ADR-019).
- DOI: https://doi.org/10.17487/RFC1034

**6. Hardy, N. (1988). The Confused Deputy. *ACM SIGOPS OSR*, 22(4),
36–38.**
→ ADR-011's designated-object authorization; an env var is designation
without unforgeability.
- DOI: https://doi.org/10.1145/54289.871709

**7. Haber, S., & Stornetta, W. S. (1991). How to Time-Stamp a Digital
Document. *Journal of Cryptology*, 3(2), 99–111.**
→ Historical anchor for §10's integrity upgrade: their *linear* linking
was this paper's earlier proposal, falsified for this regime by a
red-team — the growth-gate successor is a hash *tree*
(`docs/growth-gate/`), closest to their distributed-trust variant,
signature-free.
- DOI: https://doi.org/10.1007/BF00196791

**8. Castro, M., & Liskov, B. (1999). Practical Byzantine Fault
Tolerance. *Proc. OSDI '99*, 173–186.**
→ With #4: the practicality of tolerating arbitrary faults.

**9. Claessen, K., & Hughes, J. (2000). QuickCheck. *Proc. ICFP '00*,
268–279.**
→ §3 instrument 3: confluence as a universally quantified property —
the statement is QuickCheck's, the shipped search bounded-exhaustive.
- DOI: https://doi.org/10.1145/351240.351266

**10. DeMillo, R. A., Lipton, R. J., & Sayward, F. G. (1978). Hints on
Test Data Selection. *IEEE Computer*, 11(4), 34–41.**
→ Seeded-fault testing as mutation analysis / error seeding (back to
Mills), by hand at the defect-class level.
- DOI: https://doi.org/10.1109/C-M.1978.218136

**11. Fowler, M. (2005). Event Sourcing. martinfowler.com.**
→ §1's derive-don't-store fold; an unfinished draft by its own
caveat.

**12. Helland, P. (2015). Immutability Changes Everything. *CIDR 2015*;
*ACM Queue*, 13(9).**
→ Appendix B: the append-only file as research instrument.
- DOI: https://doi.org/10.1145/2857274.2884038

**13. Shapiro, M., Preguiça, N., Baquero, C., & Zawirski, M. (2011a).
Conflict-free Replicated Data Types. *SSS 2011*, LNCS 6976, 386–400.**
→ The convergence theory behind §6.3's merge disciplines; the FWW
register is this artifact's derived variant, in neither Shapiro paper.
- DOI: https://doi.org/10.1007/978-3-642-24550-3_29

**14. Shapiro, M., et al. (2011b). A Comprehensive Study of Convergent
and Commutative Replicated Data Types. INRIA RR-7506.**
→ The type catalog: LWW register, 2P-Set tombstone (§6.3).
- OA: https://inria.hal.science/inria-00555588

**15. Kleppmann, M., Wiggins, A., van Hardenberg, P., & McGranaghan, M.
(2019). Local-First Software. *Onward! 2019*, 154–178.**
→ The artifact's shape: user-owned files, git as sync layer, no
server.
- DOI: https://doi.org/10.1145/3359591.3359737

**16. Kelly, T. P., & McDermid, J. A. (2001). A Systematic Approach to
Safety Case Maintenance. *Reliability Engineering & System Safety*,
71(3), 271–284. (Earlier: SAFECOMP 1999.)**
→ Assurance evidence going stale under change; maintenance first-class
but manual.
- DOI: https://doi.org/10.1016/S0951-8320(00)00079-X

**17. Denney, E., Pai, G., & Habli, I. (2015). Dynamic Safety Cases for
Through-Life Safety Assurance. *Proc. ICSE 2015* (NIER), 587–590.**
→ Continuous automated invalidation of assurance evidence — proposed,
not shipped as developer tooling.
- DOI: https://doi.org/10.1109/ICSE.2015.199

**18. Samuel, J., Mathewson, N., Cappos, J., & Dingledine, R. (2010).
Survivable Key Compromise in Software Update Systems. *Proc. ACM CCS
2010*, 61–72.**
→ TUF's `expires`: TTL with signatures, no re-verification
lifecycle.
- DOI: https://doi.org/10.1145/1866307.1866315

**19. Torres-Arias, S., Afzali, H., Kuppusamy, T. K., Curtmola, R., &
Cappos, J. (2019). in-toto. *Proc. USENIX Security 2019*, 1393–1410.**
→ Signed evidence capsules, static — no invalidation, no staleness.

**20. Panthaplackel, S., Li, J. J., Gligoric, M., & Mooney, R. J.
(2021). Deep Just-In-Time Inconsistency Detection Between Comments and
Source Code. *Proc. AAAI 2021*, 35(1), 427–435.**
→ Learned commit-time comment invalidation — no ledger, no lifecycle.
- DOI: https://doi.org/10.1609/aaai.v35i1.16119

*Practice footnote (§6.5): Swimm, Dosu, Fiberplane — watched-path
staleness checks in CI; tools, not literature.*

### Standards

All catalog pages verified live, status **Published**; texts paywalled.
§6.4 reads this table as motivation: the obligation each standard names,
and the mechanism that mechanizes it.

| Standard | Used for | Catalog |
|---|---|---|
| ISO/IEC/IEEE 29148:2018 — Requirements engineering | Requirement characteristics; set completeness/consistency | https://www.iso.org/standard/72089.html |
| ISO/IEC/IEEE 24765:2017 — SE vocabulary | Forward/backward traceability | https://www.iso.org/standard/71952.html |
| ISO/IEC/IEEE 12207:2017 — Software life cycle processes | Verification vs. validation | https://www.iso.org/standard/63712.html |
| ISO 10007:2017 — Configuration management | Configuration status accounting | https://www.iso.org/standard/70400.html |
| ISO/IEC 25010:2023 / 25023:2016 — SQuaRE quality model & measures | Functional completeness | https://www.iso.org/standard/78176.html · https://www.iso.org/standard/35747.html |
| ISO/IEC/IEEE 29119 (-1:2022, -2/-3/-4:2021) — Software testing | Requirement-based coverage | https://www.iso.org/standard/81291.html (part 1) |
| ISO/IEC/IEEE 42010:2022 — **Software, systems and enterprise** — Architecture description | Correspondence rules | https://www.iso.org/standard/74393.html |
