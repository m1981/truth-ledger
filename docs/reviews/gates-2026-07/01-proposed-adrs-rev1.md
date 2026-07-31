# Proposed ADRs 034–037 — mechanizing the remaining brain-rules

> Reader: the truth-ledger operator, deciding what to adopt upstream |
> Enables: converting four filing-hygiene norms (prose in machinery.md
> and field notes) into intake refusals, forecasts, and defaults, per
> the house pattern (F4/ADR-010/ADR-011: norm → syntax) | Provenance:
> external review (Claude, 2026-07-30), grounded in the kuchnie ledger
> (1,522 records, 21 days) and the meta-repo snapshot 2026-07-20.
> Status of every ADR below: **Proposed** — numbers assume the template
> series continues from ADR-033; renumber freely, nothing cites them yet.

---

# ADR-034: Blast-radius forecast at intake

Status: Proposed (2026-07-30, external review, Claude)
Date: 2026-07-30
Supersedes: — (mechanizes the paper §9 blast-radius convention,
adopted 2026-07-13 from the second-deployment field note item 4;
extends ADR-032's pattern — an override judgment is stored and
mechanically revisited — from TTL to watch breadth)

## Context

Re-verification churn is the dominant operating cost of this regime
(paper §2.2: ~98.5% of verdict labor re-confirms what was already
believed; §8 item 2). The single largest controllable driver is watch
breadth, and today it is governed by prose alone — §9's "scope
evidence `--paths` to the narrowest set that actually backs the
claim", a rule a brain must remember at every filing.

The field cost is measured, twice:

- **kuchnie `tr-23661434`** watches four paths at once (a hot source
  file, its test file, and two documents). In 21 days it staled 15×
  and was re-agreed 15×; its median agree→stale life is **0.3 hours**
  (min ~0 h, max 263 h). The claim is usually still true — the labor
  is pure churn.
- **kuchnie `fsguard.go`** (field-notes-sdk-session item 4): one
  commit to a hot shared file re-staled **8 claims at once — 2
  genuinely affected, 6 still-true** — cascading verification debt
  across the file's whole claim neighborhood.

Meanwhile the system already *has* the data to predict this at filing
time: `stats` computes per-tier half-life from the ledger, and git
history holds per-path commit frequency. Nothing feeds either back
into intake. The judgment "is this watch too broad?" is exactly the
kind of judgment a machine makes better than a tired author: it is a
frequency estimate, not a semantic one.

## Decision

**Detection rule.** `truth claim` (and `done --claim`) gains one more
intake step, placed after the INV-M path checks and before the write.
The imperative shell gathers, once per HEAD and cached, a per-path
commit count over a trailing window (`git log --since=<window>
--name-only`, default window 30 days, constant beside
`DUPLICATE_THRESHOLD`). A pure function `blast_forecast(paths,
history)` — no I/O, no clock, no env; history is passed in, per the
ADR-019 log-purity discipline — returns the expected stalings per 30
days for the declared `evidence_paths`: the count of *distinct
commits* in the window touching any watched path (deduplicated by
commit — one commit touching three watched files stales the claim
once, so the union is counted, not the sum).

**Forecast, always.** Every filing prints the forecast beside the
half-life suggestion FS-1 already prints:
`blast: watch matched N commits in the last 30d → expect ~N
stalings/30d (~N verifications)`. Zero-history paths print
`blast: cold watch (no commits in window)` — visibility either way.

**Gate, above threshold.** If the forecast exceeds
`BLAST_THRESHOLD` (default **15 stalings/30d** — chosen so
`tr-23661434`-shaped claims are refused and single-hot-file claims
pass with a loud number; a constant beside the lexicons, changed only
together with the B-canary faults), intake **refuses** unless
`--blast-ok "<basis>"` states why the breadth is justified. The basis
is stored on the record like ADR-007's `scope_basis` — attackable at
review, visible to the verifier.

**The judgment is revisited, not trusted once (ADR-032's move).** The
record stores the forecast (`blast_forecast: N`) beside the basis.
`stats` gains a `blast` section (ADR-033's report pattern): for every
`--blast-ok` claim, observed stalings vs. forecast since filing,
sorted by observed. The report converts "was that override wise?"
from a memory into a queue — the operator reads a table, not the
ledger.

**Degradation is loud, never silent (the F1 lesson, adapted).** When
history is unavailable — shallow clone, no commits in window, git
absent — the gate degrades to a printed
`blast: history unavailable (<reason>); forecast skipped` and files
normally. Refusing legitimate claims because CI checked out at
depth 1 would convert a forecast into a false gate; the degradation
message is itself injection-asserted (fault B4), so silent skipping
is a canary failure.

## Explicit non-goals

- **No semantic narrowing.** The forecast counts commits, not
  meaning; a newly-hot file forecasts cold, and a burst-edited doc
  forecasts hot. Precision at the symbol level stays the growth-gate
  #3 successor (coarse-watch/fine-verify), for which this gate is the
  demand-signal generator: the `blast` report names exactly the
  claims whose watches deserve symbol pins first.
- **No TTL coverage.** TTL claims decay by clock, not commits; their
  breadth problem does not exist.
- **No auto-narrowing.** The gate refuses and reports; it never
  rewrites `evidence_paths` — a machine-chosen watch would be a
  machine-authored claim, which ADR-011's authority split forbids in
  spirit.

## Consequences

The §9 convention becomes syntax: broad watches on hot paths are
refused with a number attached, and every conscious exception is
stored, priced (the forecast), and revisited (the report). The
expected effect is directly measurable in the ledger this ADR's own
discipline produces — stalings/day and agree-verdicts/day should fall
in any repo that adopts it, and if they do not, the threshold or the
window is wrong and the B-canary numbers say so. Cost: one cached
`git log` per intake. Named residuals, accepted: history-based
forecasting is blind to *future* hotness; a claim filed the day a
refactor begins passes cold and stales daily — the `blast` report
catches it after the fact, which is the ADR-032 trade, not a gap.

**Canary faults.** B1: a claim watching a path with >threshold
commits in the window, no `--blast-ok`, is refused naming the
forecast. B2: every filing prints a forecast line
(injection-asserted). B3: a cold-path claim passes with the cold
notice and no refusal — the fatigue budget as a property (W2's
pattern). B4: a shallow-history repo degrades with the loud skip
notice, never silently. B5: `--blast-ok` stores both basis and
forecast on the record; `validate` refuses a `blast_ok` record
missing either.

---

# ADR-035: Volatile-recipe linter — evidence rot classes refused at intake

Status: Proposed (2026-07-30, external review, Claude)
Date: 2026-07-30
Supersedes: — (mechanizes three rot classes named in prose:
kuchnie multiagent field note item 3, batch-M field note item 2,
machinery.md filing-hygiene rules)

## Context

Three classes of evidence recipe are *known* — field-exercised, named
in prose, and left to memory — to rot independently of the fact they
back:

1. **Line-number output** — a `grep -n` recipe diverged mechanically
   in kuchnie when an additive edit shifted line numbers (multiagent
   note 3; ADR-012's exact class). The fact held; the recipe broke.
2. **Volatile literals** — `tr-22853f…` (meta-repo) hardcoded
   `"v0.9.8"`, which the v0.9.9 bump broke; batch-M's rule "grep
   INVARIANTS, never volatile strings" is a convention with no
   syntax. A version-shaped or date-shaped literal in an evidence
   command has a known expiry no one recorded.
3. **Line-spanning phrases** — `tr-3b69f8…` grepped a sentence the
   source wraps across two lines; `grep -q` never matched and the
   claim filed hollow (batch-M note 2).
4. **Generated artifacts as watch paths** — a kuchnie claim watching
   a generated file re-staled on every regeneration (multiagent
   note 3), which proposed a repo-declared generated list and never
   shipped it.

All four are lexically or structurally detectable at intake, before
anything is written. The moment a gate needs a model to fire it is a
review, not a refusal (the `contradicts` design stance) — none of
these do.

## Decision

`truth claim` gains a recipe linter, placed after the ADR-009 screen
(the command must already be safe to reason about) and before the
determinism double-run (no point double-running a recipe about to be
warned):

- **`-n` / `--line-number` in a grep/rg evidence command → warning**,
  never a refusal (a recipe may legitimately pin a line in a frozen
  fixture): `recipe: -n makes the output shift under unrelated
  edits — mechanical divergence guaranteed on the first insertion
  above the match (ADR-012). Drop -n unless the line number is the
  fact.`
- **Version-shaped (`vX[.Y[.Z]]`, `X.Y.Z`) and date-shaped
  (`YYYY-MM-DD`) literals in the command → warning naming the
  token**: `recipe: 'v0.9.19' is a volatile literal — this recipe has
  a release-shaped expiry. Anchor to an invariant (a def name, an
  ADR id, a FAULT tag) or file with --ttl-days instead.` Version-pin
  claims are legitimate (machinery.md: their divergences are genuine,
  successor-claim material) — hence warning, not refusal; the warning
  is the recorded acknowledgment that this claim is *expected* to
  diverge on release.
- **A quoted phrase of ≥ `PHRASE_WRAP_WORDS` words (default 5) in a
  grep-family command → warning**: `recipe: a 7-word quoted phrase
  breaks on any line wrap — the tr-3b69f8 hollow class. Grep the
  shortest invariant token instead.`
- **A watched path matching a committed `.truth/generated-paths`
  glob list → refusal**, `--generated-ok "<basis>"` to override
  (basis stored). The list ships EMPTY with a header explaining the
  policy, exactly the `.truth/accept-allow` pattern: which artifacts
  are generated is a per-repository fact the template cannot know.
  An empty or absent list disables only this check — visibly
  (`generated-paths: none declared`), never silently (F1).

Lexicons and the word threshold live as constants beside
`DUPLICATE_THRESHOLD` and change only together with the R-canary
faults.

## Explicit non-goals

No semantic judgment of recipe quality; no attempt to *rewrite*
recipes; no blocking of the three warning classes — each has a
legitimate shape, and a gate that refuses legitimate filings teaches
its own bypass (the ADR-011 lesson). The warnings exist to move the
four rules out of machinery.md prose and into the terminal at the
exact moment they apply, which is the only place a rule reliably
reaches a fresh session.

## Consequences

The filing-hygiene section stops being a memory test: three of its
rules fire themselves, and the fourth (generated paths) becomes a
policy file with a refusal behind it. Expected measurable effect:
ADR-012 mechanical-divergence rate and the hollow-VERIFIED intake
rate both fall; both are already counted, so the linter's value is a
`stats` diff, not an argument. Cost: string scans at intake, nothing
at fold. Named residual: the volatile-literal patterns are
shape-based — a codename-versioned string (`"quartz-release"`)
passes; extending the shapes is a constants-plus-faults change, the
ADR-007 amendment path.

**Canary faults.** R1: `-n` recipe warns (injection-asserted).
R2: version literal warns naming the token. R3: a 6-word quoted
phrase warns; a 3-word phrase does not (fatigue budget). R4: a claim
watching a `generated-paths` match is refused; `--generated-ok`
files with basis stored. R5: absent list prints the none-declared
notice and skips only the generated check — the other three classes
still fire (fail-open must be partial and loud).

---

# ADR-036: Positive-claim exit gate — hollow VERIFIED refused where decidable

Status: Proposed (2026-07-30, external review, Claude)
Date: 2026-07-30
Supersedes: — (hardens the v0.9.11 hollow-VERIFIED warning; composes
ADR-007's negation lexicon with the evidence exit code)

## Context

The Hollow-VERIFIED defect class (paper §4): the VERIFIED double-run
checks *stability*, not *success*, so a deterministically failing
command files VERIFIED and rechecks green forever. v0.9.11 shipped a
loud, non-blocking warning — queue, not gate — because a
legitimately-failing probe exists: `grep` proving *absence* exits 1,
and that exit code IS the demonstration.

The field has since produced the case the warning was too weak for:
kuchnie `tr-0e884e02`, a **positive** P1 claim ("kuchnie is synced to
template v0.9.19…") whose `&&`-chained evidence exited 1 at filing —
a stash-pop conflict had silently dropped the version pin, so the
evidence *contradicted the sentence at the moment of filing* — and it
filed VERIFIED anyway. The independent verifier caught it (banked as
QB-011, retracted, successor `tr-06522739`), which means the cheap
layer passed a defect to the expensive layer.

The blocking distinction — "is exit≠0 the proof or the refutation?" —
is decidable more often than the v0.9.11 decision assumed, because
the codebase already contains the decider: ADR-007's quantifier
lexicon includes the negation tokens (*no, none, never, nowhere,
zero*). A claim text with no negation signal is a positive assertion;
for a positive assertion, a failing evidence command demonstrates
nothing.

## Decision

At `truth claim --class VERIFIED` intake, after the determinism
double-run:

- **Text carries an ADR-007 negation token → unchanged**: the
  v0.9.11 warning path, exit code free (absence proofs are the
  legitimate non-zero class).
- **Text carries no negation token AND the evidence exit ≠ 0 →
  refusal**: `a positive claim's evidence exited N — the command
  demonstrates nothing it asserts (the tr-0e884e02 shape). Fix the
  recipe, or state why a failing command proves this sentence with
  --exit-ok "<basis>".` The basis is stored (`exit_ok_basis`),
  attackable at review; a bare flag is refused (ADR-007's
  `--scope-ok` discipline).
- `recheck` and `reaffirm` semantics are untouched: they compare
  stability against the *recorded* exit, exactly as today — this ADR
  gates filing, not re-verification (the ADR-029 gate-on-execution
  layering).

## Explicit non-goals

**Mixed claims stay warnings.** A sentence asserting a positive fact
AND an absence in one breath — kuchnie `tr-d59194ea`: "prices edge
banding as a hardcoded 0.80 line AND reads neither X nor Y" —
carries a negation token, so it takes the warning path even though
its positive half is undemonstrated on exit 1. Splitting compound
sentences is a semantic judgment this gate must not attempt; the
named residual is that hollow *halves* of mixed claims remain a
verifier's catch, and the filing-hygiene rule ("one fact per claim")
remains prose. Nor does this ADR touch INFERRED/UNVERIFIED classes:
they promise no demonstration, so a failing command contradicts
nothing they claim.

## Consequences

The exactly-decidable slice of the hollow class — positive sentence,
failing evidence — moves from the verifier's queue to an intake
refusal, which is where `tr-0e884e02` would have died at zero cost.
The undecidable slice (mixed sentences, absence proofs that fail for
the *wrong* reason) keeps the warning, honestly. Measurable:
QB-011-class verifier catches should approach zero for
single-fact positive claims; the `--exit-ok` count in `stats`
(ADR-033's velocity pattern) is the new place to watch for the gate
teaching a ritual.

**Canary faults.** X1: positive text + exit 1 refused naming the
shape. X2: negation-token text + exit 1 files with the v0.9.11
warning only. X3: `--exit-ok` without a basis refused; with a basis,
files and stores it. X4: positive text + exit 0 files silently
(fatigue budget). X5: `validate` refuses an `exit_ok_basis` record
whose recorded evidence exit is 0 (a basis with nothing to excuse is
schema noise).

---

# ADR-037: Tombstone citation gate — retraction refuses while cited

Status: Proposed (2026-07-30, external review, Claude)
Date: 2026-07-30
Supersedes: — (mechanizes machinery.md's "retraction citation sweep";
extends ADR-011's tombstone ceremony with a corpus check)

## Context

Machinery.md's filing-hygiene section carries a pure brain-rule:
*"before recommending or executing a retraction, grep the whole
corpus — specs, docs, use-cases — for the id. A retracted id cited by
any spec blocks every spec commit via the health gate; swap the
citations to the successor claim FIRST, then retract."* The rule
exists because the failure is real and ordered: retract first, and
the spec-health gate bricks unrelated spec commits until someone
hunts the citations — the cost lands later, on someone else, which is
the defining shape of a norm that wants to be syntax.

Every ingredient already exists: `fact-health.sh` knows how to find
ledger-id citations in tracked files; tombstones are already the most
ceremonial verb in the system (ADR-011: `TRUTH_HUMAN` plus a typed
exact id); and the citation convention (§5, "cite, don't restate")
guarantees citations are greppable by construction.

## Decision

`verdict <id> retracted` (and `done --cancel`, the issue tombstone),
after the ADR-011 human ceremony passes and before the append: the
shell greps tracked files (`git grep -l -F "<exact-id>"`, excluding
`.truth/claims.jsonl` itself and `docs/archive/` — frozen verbatim by
convention, its citations are historical record, not live
dependencies) for the id being killed.

- **Citations found → refusal**, printing the citing files and the
  ordered remedy: `retraction blocked: <id> is cited by 3 tracked
  files (listed). Swap each citation to the successor claim first,
  then retract. Deliberate orphaning: --orphan-ok "<basis>".` The
  basis is stored on the verdict record.
- **No citations → proceeds** exactly as today.
- **git unavailable → refusal with the reason** (`cannot verify
  citations: <reason>; retraction is rare and human-gated — run it
  where the corpus is greppable, or --orphan-ok`). Tombstones are
  the one verb where failing *closed* costs nearly nothing:
  retraction is deliberately rare (six in the pilot's whole window,
  all human), and a human who has already typed the exact id can
  type a basis.

The check compares the exact id token, `-F` fixed-string, so no
pattern ambiguity exists; the exclusion list is a constant beside
the lexicons, changed only with the T-canary faults.

## Explicit non-goals

No automatic citation rewriting — swapping a citation to a successor
is an editorial judgment about whether the successor *covers* the
citing sentence, exactly the judgment ADR-013's supersede gate
demands a human make for premises. No coverage of `cancelled`
premises-side cleanup beyond the issue tombstone itself; the ADR-001
HELD matrix already handles a retracted premise's downstream effect.
And no extension to `diverge`: a diverged claim is recoverable and
its citations may legitimately outlive the dispute — only the
*terminal* verb earns the terminal check.

## Consequences

The two-step ritual (sweep, then retract) collapses into one verb
that refuses in the wrong order, which is the whole cost of the rule
moved from a future spec-committer's afternoon to the retracting
human's present minute — the correct direction, since that human has
the context. The `--orphan-ok` count joins the ADR-033 override
report. Named residual: citations by claim *title* rather than id
(the two-commit dance's intermediate state) are invisible to the
`-F` id grep — the dance's second commit closes that window, and a
title-grep would false-positive on prose; accepted, documented here.

**Canary faults.** T1: retracting an id cited by a tracked doc is
refused listing the file. T2: after the citation is swapped to a
successor id, the same retraction proceeds. T3: `--orphan-ok`
without a basis refused; with one, files and stores it. T4: a
citation inside `docs/archive/` alone does not block (exclusion
honored). T5: git-unavailable refuses loudly with the reason, never
silently proceeds.

---

## Adoption order and the measurement each one owes

034 first — its effect is the largest measured cost (churn) and its
success metric already exists (`stats` half-life and stalings/day
must move). 035 and 036 second, together — both are intake-only,
both are measured by counters the ledger already keeps (mechanical
divergences, verifier hollow-catches). 037 last — smallest surface,
rarest verb, but the cheapest full norm→syntax conversion in the
backlog.

Every threshold above (BLAST_THRESHOLD 15, window 30d,
PHRASE_WRAP_WORDS 5) is a first guess wearing a constant's clothes:
the ADR-007 precedent applies — constants change only together with
their canary faults, and the first field week decides the numbers,
not this document.
