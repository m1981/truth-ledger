# Proposed ADRs, revision 2 — five records, review findings absorbed

> Reader: the truth-ledger operator | Supersedes: revision 1
> (`proposed-adrs-034-037.md`, 2026-07-30) in full | Provenance:
> external review (Claude) revised against the five-agent adversarial
> review of 2026-07-30; every review finding is either absorbed into
> the text below or explicitly declined with a reason (none are
> declined) | Status of every ADR: **Proposed**. Numbers 034–038 are
> placeholders assigned in the review's adoption order; renumber to
> the series head at adoption, nothing cites them yet.
>
> **Citation discipline.** Ledger facts are cited by id
> (`tr-…`/`wk-…`). Facts established by the 2026-07-30 review
> (retraction counts, threshold replay, citation-scope measurement,
> lexicon inspection) are cited as *[review]* — if the operator files
> them to the meta ledger (review next-step 3), swap each *[review]*
> for its id before adoption; a restated number is the rot this
> repository exists to prevent.
>
> **Revision-1 errors, on the record.** R1 contained: a windowed
> figure universalized ("six retractions" vs. the pilot's 66
> *[review]*); an invented citation ("ADR-011's authority split");
> two misattributed lessons (ADR-011 for ADR-014's confused-deputy;
> machinery.md as the prose home of rules living in the field notes
> and `template/.truth/README.md:429–435`); one wrong deployment
> (`fsguard.go` is `temporal-go-agent-sdk`, not kuchnie); one
> non-existent artifact treated as shipped (a negation lexicon); a
> flagship example (`tr-d59194ea`) that R1's own rule would refuse
> while its Non-goals promised a warning; an uncalibrated default
> threshold falsified on the meta-repo (82/96 path-carrying claims
> above it *[review]*); and canary prefixes colliding with three
> existing fault namespaces. Each is corrected below at its site.

---

## Cross-cutting rules (bind every ADR in this file)

**CC-1 — Fatigue budget, totaled.** A clean filing prints zero new
lines (the W2 silence-on-clean property). Across all gates in this
file plus the shipped ones, a single filing emits **at most one
advisory block**; when several advisories fire, they render as one
block, most severe first. Refusals are exempt (a refusal ends the
filing). Canary fault CC1: a filing tripping two advisory classes
prints one block; CC2: a clean filing prints nothing new
(injection-asserted absence).

**CC-2 — Overrides are reported, always, in the same change.** Every
override flag introduced below (`--exit-ok`, `--orphan-ok`,
`--generated-ok`) lands in the ADR-033 `override_report` in the same
release as the flag. A flag whose use is not counted is a ritual
waiting to form.

**CC-3 — Canary namespace check is an adoption step.** Proposed
prefixes: DW, X (free per review), TG, RC, BL, CC. Before each
adoption, grep the canary for the prefix; B, T, R are known-taken
*[review]* and are not used here.

**CC-4 — Staged releases.** One ADR per release. The five ADRs
below add payload fields and stderr surfaces; the sync surface
(schema + validate mirror + FS-2 fixtures + `$id` bump + paper §1 +
machinery.md + README) is per-ADR work, and a mega-release is how
doc-sync silently drops.

---

# ADR-034: Dirty-watch advisory at intake

Status: Proposed (2026-07-30, external review, Claude; the gap was
named by the 2026-07-30 adversarial review, missed-items item 1)
Date: 2026-07-30
Supersedes: — (mechanizes the orchestrator rule in machinery.md's
authoring loop — "commits the CONTENT first (…) a claim filed before
its watched content lands restales at birth" — and the two-commit
dance's motivating hazard)

## Context

INV-M refuses a watch on an *untracked* path. A watch on a
**tracked-but-dirty** path passes every gate — and the claim then
stales on the very commit that lands the content it describes:
restale-at-birth, the class the two-commit dance
(machinery.md:124–128) exists to choreograph around. The
choreography is prose; the hazard is mechanically visible at filing
time in one `git status --porcelain -- <paths>` call. Of everything
in this file, this is the cheapest norm→syntax conversion: no new
payload field, no override flag, no threshold.

## Decision

At claim intake (`truth claim` and `done --claim`), after the INV-M
path checks: the shell runs `git status --porcelain -- <evidence
paths>`. Any watched path reporting modified or staged-uncommitted
state produces an advisory (never a refusal), rendered inside the
CC-1 block:

`dirty watch: <path> has uncommitted changes — this claim stales on
the commit that lands them (restale-at-birth). Commit the content
first, then file (the two-commit dance, machinery.md).`

TTL claims (no paths) are out of scope by construction. No override
flag exists because nothing is refused; a deliberate mid-flight
filing simply proceeds past the advisory.

## Explicit non-goals

No refusal: filing ahead of the content commit is legitimate when
the author intends an immediate re-verify (the dance's step 2), and
a gate here would teach `git stash` as its bypass. No attempt to
detect a dirty *repository* — only the claim's own watched paths
are the claim's business.

## Consequences

The restale-at-birth class becomes visible at the only moment it is
cheap — before the append — and the authoring-loop rule stops
depending on a fresh session having read machinery.md. Measurable:
invalidations dated within minutes of their claim's own `ts` (the
birth-restale signature) should approach zero; that query is
computable from the ledger today, so the ADR's effect has a
denominator before it ships.

**Canary faults.** DW1: a claim watching a modified tracked path
prints the advisory (injection-asserted). DW2: a clean-tree filing
prints nothing (CC-1 absence assertion). DW3: a dirty file *not*
watched by the claim produces no advisory (the fatigue budget as a
property).

---

# ADR-035: Negation lexicon and the positive-claim exit gate

Status: Proposed (2026-07-30, external review, Claude; revision 2 —
the review falsified R1's lexicon premise and its flagship example)
Date: 2026-07-30
Supersedes: — (hardens the v0.9.11 hollow-VERIFIED warning; builds
the negation constant R1 wrongly assumed shipped)

## Context

The Hollow-VERIFIED class (paper §4): the VERIFIED double-run checks
*stability*, not *success*; a deterministically failing command
files VERIFIED and rechecks green forever. v0.9.11 made this a loud
non-blocking warning, because a legitimately-failing probe exists —
`grep` proving absence exits 1, and that exit IS the demonstration.

The field then produced the case the warning under-serves: kuchnie
`tr-0e884e02`, a **positive** P1 claim ("kuchnie is synced to
template v0.9.19…") whose four-leg `&&`-chained evidence exited 1 at
filing — a stash-pop conflict resolution had dropped the
machinery.md authoring-loop section, so one chain leg failed and the
sentinel echo never ran. It filed VERIFIED; the independent verifier
caught it (`tr-ca69eadb` diverge; retraction `tr-11f8bffc`;
successor `tr-06522739`; banked as QB-011). The cheap layer passed a
decidable defect to the expensive layer.

Decidable — but not with shipped machinery. The CLI has one
undivided `QUANTIFIER_TOKENS` frozenset (15 tokens, positive
universals included) and **no negation constant** *[review; confirmed
by re-inspection]*; `tokens()` splits on `[a-z0-9]+`, so
"neither/nor/not" match nothing in it. R1's rule, run against R1's
own mixed-claim exemplar `tr-d59194ea` ("reads **neither** X **nor**
Y…"), would have *refused* the claim its Non-goals promised to
warn — the lexicon must exist before the gate can.

## Decision

**A dedicated constant.** `NEGATION_TOKENS`, a frozenset beside the
lexicons: *not, neither, nor, without, absent, lacks, lacking,
missing, unused, unreferenced*, **plus copies** of the five
negation-shaped quantifier tokens (*no, none, never, nowhere,
zero*). Copies, not a shared reference: sharing would couple this
gate to ADR-007's, and widening one would silently widen the other.
A canary fault (X6) asserts the five-token subset relation, so drift
between the constants is caught, not trusted.

**The gate.** At VERIFIED intake — both verbs, `truth claim --class
VERIFIED` **and** `done --claim`, which files through the same
payload path and supplied both of the paper's real hollow instances —
after the determinism double-run:

- text carries a `NEGATION_TOKENS` token → the v0.9.11 warning path,
  exit-code free (absence proofs keep their legitimate non-zero);
- text carries none AND recorded evidence exit ≠ 0 → **refusal**:
  `a positive claim's evidence exited N — the command demonstrates
  nothing the sentence asserts (the tr-0e884e02 shape). Fix the
  recipe, or state why a failing command proves this sentence:
  --exit-ok "<basis>".` The basis is stored (`exit_ok_basis`),
  attackable at review; a bare flag is refused (the `--scope-ok`
  discipline). Per CC-2, `--exit-ok` joins `override_report` in the
  same release.

`recheck` and `reaffirm` are untouched — they compare stability
against the *recorded* exit exactly as today; this gates filing, not
re-verification. `validate` tolerates legacy records lacking
`evidence.returncode` (as recheck already does via `.get`); an
`exit_ok_basis` on a record whose recorded exit is 0 is refused as
schema noise (X5).

**Measurement, added here because it is absent today** *[review]*:
`stats` gains counters for exit≠0 VERIFIED filings — warned
(negation path), refused, and `--exit-ok`-overridden — so this ADR's
effect and 037's have a denominator; the v0.9.11 warning is
currently per-filing stderr that no number remembers.

## Explicit non-goals — and the residuals, owned

- **Mixed sentences stay warnings.** `tr-d59194ea` ("prices as a
  hardcoded 0.80 line AND reads neither X nor Y") carries negation
  tokens, so its undemonstrated *positive* half rides the warning
  path — splitting compound sentences is semantic work this gate
  must not attempt. The standing hygiene rule is "one fact per
  claim"; a compound-sentence advisory (" and ", "; " in claim text)
  is named here as follow-on work, not smuggled in.
- **The token test reads the sentence's polarity, not the
  recipe's.** An inverted recipe (`! grep …`) exits 0 and the gate
  stays silent regardless of text; a differential proof ("A and B
  differ", `diff` exiting 1) has no negation token and is *falsely
  refused* — `--exit-ok` with a basis is the designed path for that
  class, and the override counter is where its frequency becomes a
  fact instead of an anecdote.
- INFERRED/UNVERIFIED are untouched: they promise no demonstration.

## Consequences

The exactly-decidable slice of the hollow class — positive sentence,
failing evidence — dies at intake, where `tr-0e884e02` would have
cost zero instead of a verifier dispatch, a retraction ceremony, and
a successor. The undecidable slices keep the warning, and their
sizes are now counted. Adoption-order note: this ADR goes **first**
among the gates (review verdict): smallest diff, the returncode
already sits in the payload at the exact seam, and it subsumes the
worst of the recipe linter's phrase class.

**Canary faults.** X1: positive text + exit 1 refused naming the
shape. X2: negation-token text + exit 1 files with only the v0.9.11
warning. X3: bare `--exit-ok` refused; with basis, files and stores
it. X4: positive text + exit 0 files silently (CC-1). X5: validate
refuses `exit_ok_basis` with recorded exit 0; tolerates absent
returncode. X6: `NEGATION_TOKENS ⊇` the five negative quantifier
tokens (constant-drift tripwire). X7: `done --claim` with failing
positive evidence is refused identically to `truth claim`.

---

# ADR-036: Tombstone citation gate

Status: Proposed (2026-07-30, external review, Claude; revision 2 —
scope and volume re-based on the review's measurements)
Date: 2026-07-30
Supersedes: — (mechanizes the machinery.md retraction-citation
sweep; extends ADR-011's ceremony with a corpus check)

## Context

Machinery.md, verbatim: *"before recommending or executing a
retraction, grep the whole corpus — specs, docs, use-cases — for the
id. A retracted id cited by any spec blocks every spec commit via
the health gate; swap the citations to the successor claim FIRST,
then retract."* Retract first and the cost lands later, on someone
else's spec commit — the defining shape of a norm that wants to be
syntax.

Volume, corrected from R1: retraction is not rare-as-six. The pilot
holds **66** retracted verdicts over its window and the meta-repo
dozens more, arriving in **human batch sweeps of 21–28** (e.g.
meta commit 217306c, 21 at once) *[review; 66 confirmed by
recount]*. The gate must therefore be batch-shaped: refusals list
*all* citing files per id in one pass, so a 25-id sweep meets 25
verdicts, not 25 interactive hunts.

Scope, measured and corrected from R1: a blanket "all tracked files
minus `docs/archive/`" grep is falsified at home — 12 of the
meta-repo's already-retracted ids are cited *right now* in tracked
markdown outside archive (CHANGELOG, ADR bodies, field notes, the
roadmap, the operations guide, the loophole map) as **historical
record, not live dependencies** *[review]*; kuchnie's own
historical-exemption convention is broader still
(archive|attic|docs/adr|freeze|CHANGELOG). A gate that refuses on
historical mentions ritualizes its own override on day one.

Ingredient, corrected from R1: the template-shipped citation checker
is `spec-health.sh` (tr+wk ids, `docs/specs/`, blocking only where a
consumer wired it); `fact-health.sh` is meta-repo-only by its own
header.

## Decision

`verdict <id> retracted` and `done --cancel`, after the ADR-011
human ceremony passes and before the append: the shell greps for the
exact id (`git grep -l -F`) **within a consumer-declared inclusion
scope** — a committed policy file `.truth/citation-scope` (glob per
line, the `.truth/accept-allow` pattern), shipped defaulting to
`docs/specs/**`: the one corpus whose health gate the template
actually ships teeth for. `.truth/claims.jsonl` is excluded
unconditionally (retraction bases legitimately cite successors
throughout — provably necessary *[review]*).

- **Citations found → refusal**, listing every citing file, with the
  ordered remedy: swap each citation to the successor claim, then
  retract. Deliberate orphaning: `--orphan-ok "<basis>"`, basis
  stored on the verdict, counted per CC-2.
- **No citations → proceeds** as today.
- **git grep unavailable → refusal with the reason.** The one earned
  exception to fail-open-loud (review concurrence): the verb is
  terminal, the human is already mid-ceremony with a typed id, and
  typing a basis costs a sentence.

The scope file is policy, not mechanism: a consumer who wants
kuchnie's broad historical exemptions writes them; the template does
not guess a consumer's documentary conventions.

## Explicit non-goals — and residuals, owned

No automatic citation rewriting (whether a successor *covers* a
citing sentence is editorial judgment). No `diverge` coverage — a
diverged claim is recoverable and its citations may legitimately
outlive the dispute; only the terminal verb earns the terminal
check. Named residuals: **truncated citations** (`tr-3b69f8…`-style
ellipses, used by the field notes and by this document) are
invisible to a full-id `-F` grep — the companion hygiene rule is
"cite full ids in scope-covered documents", and the residual stands
where the rule isn't followed; a TOCTOU window exists for citations
added between sweep and append (accepted; the spec-health gate
remains the backstop); "retractions are all human" is self-attested
via actor fields and bases, not record-proven.

## Consequences

The two-step ritual collapses into one verb that refuses in the
wrong order, moving the cost from a future spec-committer's
afternoon to the retracting human's present minute — the correct
direction, since that human holds the context and is already in
ceremony. Batch sweeps stay batch-shaped. `--orphan-ok` frequency in
`override_report` is the gate's own health metric: a rising count
means the scope file is wrong, not the users.

**Canary faults.** TG1: retracting an id cited inside the scope is
refused listing the file(s). TG2: after the citation swaps to a
successor, the same retraction proceeds. TG3: bare `--orphan-ok`
refused; with basis, files and stores it. TG4: a citation outside
the scope file's globs does not block. TG5: git-grep failure refuses
loudly with the reason, never proceeds silently. TG6: a batch of
three retractions with mixed citation states yields per-id verdicts
in one pass.

---

# ADR-037: Volatile-recipe linter

Status: Proposed (2026-07-30, external review, Claude; revision 2 —
prose homes, class placement, and carve-outs corrected per review)
Date: 2026-07-30
Supersedes: — (mechanizes rot classes named in the kuchnie
multiagent field note item 3, the batch-M field note item 2, and
`template/.truth/README.md:429–435` — not machinery.md, R1's error)

## Context

Three recipe rot classes and one watch rot class are
field-exercised, named in prose, and left to memory:

1. **Line-number output**: a `grep -n` recipe diverged mechanically
   in the pilot when an additive edit shifted numbers (multiagent
   note 3; ADR-012's class). The fact held; the recipe broke.
2. **Volatile literals**: `tr-22853f21` hardcoded `v0.9.8`, broken
   by the v0.9.9 bump, diverged then retracted. The repair that
   fixed it anchored to the schema `$id` — itself version-shaped —
   which is why this class needs carve-outs, not a blanket rule.
3. **Line-spanning phrases**: `tr-3b69f8ff` grepped a sentence the
   source wraps; `grep -q` never matched; filed hollow with rc=1,
   diverged `--mechanical`, successor `tr-bbdff732`.
4. **Generated artifacts as watches**: a pilot claim watching a
   generated file restaled on every regeneration (multiagent
   note 3), which proposed a repo-declared generated list that never
   shipped.

Class 3's *defect* is subsumed by ADR-035: `tr-3b69f8ff` filed with
exit 1 on a positive sentence, which the exit gate now refuses
outright. The review measured the phrase heuristic's residual value
against its noise (~13% of real recipes carry a ≥5-word quoted
phrase, mostly legitimate; the naive word count mis-tokenizes regex
alternations) and this revision **drops the phrase arm** — the class
is covered where it is decidable (exit≠0) and not worth a
mis-tokenizing lexical guess where it is not.

## Decision

**Placement first (review amendment): the generated-paths check is a
watch check, not a recipe check.** It moves to the INV-M position,
applying to every claim with `evidence_paths` regardless of
evidence class — an INFERRED claim watching a generated file
restales identically. A committed `.truth/generated-paths` (glob per
line, `accept-allow` pattern, ships EMPTY with a policy header):
a watched path matching it is **refused**, `--generated-ok
"<basis>"` to override, basis stored, counted per CC-2. An absent
or empty list disables only this check, with a one-line notice
inside the CC-1 block — partial fail-open, loud.

**The recipe warnings**, at VERIFIED intake after the ADR-009
screen, rendered inside the CC-1 block:

- `-n`/`--line-number` in a grep-family evidence command → warning:
  line numbers shift under unrelated edits; mechanical divergence
  guaranteed on the first insertion above the match (ADR-012). Drop
  `-n` unless the line number is the fact.
- Version-shaped (`vX[.Y[.Z]]`, `X.Y.Z`) or date-shaped
  (`YYYY-MM-DD`) literals in the command → warning naming the token
  and its release-shaped expiry, **except** when the token sits
  inside a path/filename segment or matches the schema-`$id` pattern
  — the two measured legitimate-invariant classes (25/98 meta-repo
  commands carry version shapes; many are the fix, not the defect
  *[review]*). Version-pin claims stay legitimate and
  divergence-expected (their divergences are genuine, successor
  material); the warning is the recorded acknowledgment of that
  expiry, not a prohibition.

Warnings never refuse: each class has a legitimate shape, and a gate
refusing legitimate filings teaches its own bypass — **ADR-014's
confused-deputy lesson** (R1 misattributed it to ADR-011, whose
lesson is about refusal *messages*). Constants live beside the
lexicons and change only with the RC faults.

## Explicit non-goals

No semantic recipe quality judgment; no rewriting; no phrase
heuristic (dropped above, revivable as its own ADR with a
canary-pinned boundary if the exit gate's coverage proves
insufficient — the boundary R1 left unpinned between its 5-word
field case and its 6/3-word test values).

## Consequences

Two field rules fire themselves at the moment they apply — the only
place a rule reliably reaches a fresh session — and the generated
list becomes policy with a refusal behind it, at the gate position
where it covers all evidence classes. Measurable: ADR-012 mechanical
divergence rate (already counted) and the ADR-035 hollow counters
(added there) are the before/after; the `--generated-ok` count in
`override_report` is the policy file's health metric.

**Canary faults.** RC1: `-n` recipe warns (injection-asserted).
RC2: version literal in a command warns naming the token. RC3: the
same shape inside a filename segment does not warn; the schema-`$id`
pattern does not warn (carve-outs as properties). RC4: a claim of
*any* evidence class watching a `generated-paths` match is refused;
`--generated-ok` files with basis stored. RC5: absent list prints
the one-line notice and skips only the generated check — the recipe
warnings still fire. RC6: a clean recipe on a clean watch prints
nothing (CC-1).

---

# ADR-038: Blast forecast and the churn report — advisory only

Status: Proposed (2026-07-30, external review, Claude; revision 2 —
the R1 refusal gate is severed, per the review's threshold replay
and the house calibration discipline)
Date: 2026-07-30
Supersedes: — (gives the paper §9 blast-radius convention — adopted
2026-07-13 from the temporal-go-agent-sdk field note item 4, R1's
provenance error corrected — its instrument; the refusal gate
returns as its own ADR only after a field window of data)

## Context

Re-verification churn is the regime's dominant operating cost
(paper §2.2, §8 item 2), and watch breadth is its largest
controllable driver, governed today by prose. The field cost is
measured: kuchnie `tr-23661434` — four watched paths — staled 15×
and re-agreed 15× over its **15.3-day** life (median agree→stale
0.31 h, min 0.0045 h, max 263.4 h), and its dominant staler is a
*document*, `docs/specs/use-cases.md`, 11 of 15 stalings *[review]* —
the blast hazard is docs-in-watch as much as hot source. In the
second deployment, one commit to `fsguard.go` restaled 8 claims —
2 genuinely affected, 6 still-true.

R1 proposed a refusal above BLAST_THRESHOLD=15. The review replayed
that default against the meta-repo's own history: **82 of 96
path-carrying claims would refuse**, a claim watching
`template/scripts/truth` alone forecasting 50–76 commits/30d
*[review]* — `--blast-ok` as the per-filing ritual on day one, in
the template's home repository. Meanwhile the shipped countermeasure
for exactly this churn — reaffirm's hash-match arm (ADR-030) — is
mid-trial, its first data read due ~2026-08-08 (paper §8 item 2).
Gating filings on a cost the running countermeasure may have
absorbed, before its first read, with a threshold falsified at home,
inverts the ADR-032/033 discipline: **no threshold until the
false-positive rate is known.** This revision ships the instrument
and defers the gate.

## Decision

**The forecast, honest about what it is.** A pure function
`blast_forecast(paths, history)` — history gathered at the shell
edge (`git log --since=<window> --name-only`, window 30 d, constant
beside the lexicons; no cache — one traversal per filing is cheaper
than the double-run already paid) — returns the count of *distinct
commits* in the window touching any watched path (union, deduped by
commit). This is an **upper bound on stalings, not an expectation**:
a claim stales only from live, so N commits between re-verifications
produce one staling — `tr-23661434` itself shows 15 invalidations
against 14 re-agrees. The number is a hotness signal; the ADR says
so and no more.

**Advisory above a floor, silence below (CC-1).** Filings print
nothing when the forecast is under `BLAST_ADVISORY_FLOOR` (default
15/30d — the same value R1 misused as a refusal, correctly employed
here as a print threshold); at or above it, one line inside the CC-1
block: `blast: watch matched N commits in the last 30d — an upper
bound on stalings; narrower --paths cut re-verification load (§9)`.

**Shallow history detected, not trusted** (R1's B4 hole): shallow
clones truncate `git log` silently; the shell checks `git rev-parse
--is-shallow-repository` and a shallow repo prints
`blast: shallow history — forecast is a floor, not a bound` instead
of a quietly-cold number. ("git absent" is unreachable — intake
already ran git; R1's degradation list conflated it with the
legitimate no-commits-in-window case, which is simply a sub-floor
silence.)

**The churn report — most of the value, none of the gate.** `stats`
gains a `blast` section: per path-watched claim, observed
invalidations since filing vs. forecast-at-filing (stored on the
record as `blast_forecast: N`), top-N by observed, plus the
per-path staler ranking (which file causes the most invalidations —
the `use-cases.md` 11/15 shape, surfaced instead of excavated). This
is ADR-033's move — a report a human reads — named as such; R1
overclaimed it as ADR-032's mechanical revisit.

**The gate, deferred with a named trigger.** A refusal arm ships
only as its own future ADR, after one field window (≥30 d) of
forecast-vs-observed data from this report AND the ~2026-08-08
reaffirm read — with the threshold derived from the measured
distribution, not guessed. This paragraph is the demand signal the
growth-gate pattern requires; the report above is its instrument.

## Explicit non-goals

No refusal (severed, above). No semantic narrowing — commits are
counted, not meanings; a newly-hot file forecasts cold, and the
report catches it after the fact, which is the accepted trade. No
TTL coverage (clock decay, not commit decay). No auto-narrowing of
`evidence_paths` — the forecast informs the author; it does not
author. Symbol-level precision remains growth-gate #3, for which the
per-path staler ranking is now the demand-signal generator: it
names exactly the paths whose claims deserve symbol pins first.

## Consequences

Authors see the price of a broad watch at the moment they choose it,
in a number with honest semantics; the operator gets the churn
ledger the gate decision has always lacked; and the refusal
question is converted from an argument into a measurement with a
date. Cost: one `git log` traversal and one `rev-parse` per filing.

**Canary faults.** BL1: a filing whose watch matched ≥floor commits
prints the advisory line (injection-asserted). BL2: a sub-floor
filing prints nothing (CC-1 absence). BL3: a shallow repo prints the
floor-not-bound notice, never a bare cold number. BL4: the record
stores `blast_forecast`; `validate` tolerates its absence on legacy
records. BL5: `stats blast` renders observed-vs-forecast and the
per-path staler ranking from a fixture ledger with known counts.

---

## Adoption order and what each release must carry

Per the review's inverted order, one release each: **035** (exit
gate + negation lexicon + hollow counters) → **036** (tombstone
citation gate + citation-scope policy file) → **037** (recipe
linter + generated-paths at INV-M) → **034** (dirty-watch —
slotted here rather than first only because 035's incident class
has already cost a QB entry; the operator may equally run it first,
it conflicts with nothing) → **038** (forecast + churn report),
whose report then decides whether a blast *gate* ADR ever exists.

Every release: schema + mirror + FS-2 fixtures + `$id` bump + paper
§1 + machinery.md + `.truth/README` sync (CC-4), canary prefix
check (CC-3), and the new flag's `override_report` row (CC-2) in
the same diff. Every constant above (window 30 d, floor 15,
lexicon contents) is a first guess wearing a constant's clothes —
the ADR-007 precedent applies: constants change only together with
their faults, and the field decides the numbers, not this document.
