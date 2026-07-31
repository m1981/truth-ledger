# Proposed ADRs, revision 3 — six records, plan-of-record absorbed

> Reader: the truth-ledger operator | Supersedes: revision 2 in full
> | Provenance: external review (Claude) rev-2 + the rev-2 absorption
> audit + the architecture review + the 14-agent structured review
> (7 lenses, adversarially verified: 4 top findings confirmed,
> 3 refuted) — all consolidated in the plan of record
> (`06-plan-of-record.md`), which this revision implements as
> ADR text | Status of all six: **Proposed**. Numbers R0/034–038 are
> placeholders in adoption order; renumber to the series head at
> adoption.
>
> **Citation discipline, honored.** Load-bearing review facts are now
> ledger ids, filed 2026-07-31 by the verifier session
> (`verifier-adr-review-2026-07-31`, commit 0d35e3e):
> `tr-d0759df4` (meta retractions 49 at anchor, 27 through 07-28),
> `tr-efc43840` (pilot retractions 66, batch sweeps),
> `tr-f0c94c6c` (12/49 retracted ids cited outside archive, incl.
> rolled-over successors tr-bbdff732, tr-da868d5c),
> `tr-c3087292` (BLAST_THRESHOLD=15 replay: 82/96 above),
> `tr-166c4616` (exit-gate simulation: 5 refusals / 6 warnings over
> 244 real filings), `tr-5c2bd165` (birth-restale: 29/895 meta,
> 37/390 pilot), `tr-624d5916` (FAULT BL prefix taken),
> `tr-4387f0ea` (DW/TG/RC/BF prefixes free),
> `tr-f49a00ee` (accept-allow absent from copier ownership).
> Counts carry 30-day TTLs — they are facts about a moment, which
> the 27-vs-49 episode demonstrated.
>
> **Rev-2 errors, on the record** (each corrected at its site): BL
> canary-prefix collision (tr-624d5916) inside the very rule (CC-3)
> that prescribed the check; a dirty-watch mechanism that handed
> evidence globs to git as pathspecs (the two-grammars class, third
> instance); a vacuous-at-home default citation scope with an
> unspecified absent-file branch; a live successor cited after its
> own retraction (tr-bbdff732, see tr-f0c94c6c); a falsified number
> reused as a print floor; "none are declined" claimed while one
> finding was deferred with a reason.

---

## Cross-cutting: four structural invariants (bind every gate; shipped as R0 faults)

**SI-1 — One glob grammar.** No git verb ever receives a CLI-owned
glob (evidence paths, citation-scope, generated-paths) as a
pathspec. Git runs bare; the core filters through `match_paths()`.
Grounds: git `*` crosses `/`; a scope line in gitignore idiom
(`:!…`, `:(exclude)…`) inverts a sweep to everything-except, and a
typo'd scope exits rc=1 — byte-identical to "clean" (the confirmed
critical finding). Policy loaders refuse lines starting with
`:`, `-`, or `!`.

**SI-2 — Subprocess discipline.** Every gate subprocess runs with
`cwd=repo_root()` (a subtree `git grep` returns rc=1 = "clean" —
confirmed silent fail-open on the fail-closed verb). Name-emitting
verbs use NUL/unquoted forms: `git status --porcelain=v1 -z`,
`git log --name-only -z --no-renames` (or `-c core.quotepath=off`)
— default quotePath octal-quotes non-ASCII names, which
`match_paths` can never match (the pilot has 27 such tracked files
today). Exit codes are pinned per verb in ADR text; for `git grep`:
0 = hits, 1 = clean, ≥2 or spawn failure = unavailable.

**SI-3 — Advisories are a contract.** Under `--json`, stdout
carries `{"record": …, "advisories": […]}`; without it, every
advisory line begins `truth: advisory:` (stable, greppable — the
QB-011 swallow class must not recur across four new advisory
classes). Every claim-derived substring (paths, tokens, git-emitted
names) renders through the house `!r` escaping — INV-M refuses only
whitespace, so ESC bytes survive intake and raw interpolation
enables terminal-escape injection.

**SI-4 — Policy-file semantics.** Both new files are consumer
policy: listed in copier `_skip_if_exists` (and R0 fixes the
pre-existing gap: `.truth/accept-allow` is deployment-edited in the
pilot yet absent from copier ownership — tr-f49a00ee). States are
distinct: **committed-empty = consciously configured = silent;
absent = built-in default + one-line notice.** Loaders read
`utf-8-sig` (a BOM silently deadens the first glob). A non-empty
scope matching zero tracked files prints a loud dead-scope notice,
never a clean result.

**CC-1 (revised) — fatigue budget with a surface inventory.** One
advisory block per filing, rendered once, after a successful
append; silence on clean. The shipped stderr surfaces are decided,
not assumed: decay notice and hollow warning **fold in** (both
post-append today); the FS-1 half-life note moves post-append and
folds in; the commit-gate banner is **exempt with reason** (it must
fire at dispatch even on refused filings — fail-open-with-noise is
its documented property). Budget restated: one advisory block plus
the named exempt surface.

**CC-2 (revised) — overrides counted, single-homed.** Every
override flag lands in the ADR-033 `override_report` in the same
release; no second tally of the same event exists anywhere
(`stats` sections point at the override row, never recount it).
Every new stored basis carries an **explicit ADR-032 decay
decision** — include-with-decay or decline-with-reason — in its
ADR's text.

**CC-3 (revised) — canary prefix registry.** Check is
`grep 'FAULT <prefix>[0-9]'` (anchored, to avoid C/CC aliasing).
Taken: BL among others (tr-624d5916). Free and claimed here: DW,
X, TG, RC, **BF** (blast), CC, GS (gate system) — tr-4387f0ea.

**CC-4 (revised) — staged releases, schema honesty.** One ADR per
release. The schema `$id` bumps **only where the record shape
changes** (ADR-026): four of six releases; R0 and the dirty-watch
release ship no schema/mirror/FS-2 work — their sync surface is
code, stderr, and docs.

---

# ADR-R0: The gate system — staged table, assembler, invariants

Status: Proposed (2026-07-31, external review, Claude; new in rev-3
— five confirmed review findings are system properties no single
gate release can own)
Date: 2026-07-31

## Context

Rev-2 added four intake gates and one verdict gate by prose
placement ("after X, before Y"), each negotiating its slot
individually — while the properties the plan actually cares about
(one advisory block, silence on clean, every flag counted, nothing
executes before the screen) are properties of the *system of
gates*. Placement-by-prose is how those properties erode one gate
at a time. Meanwhile the structured review's confirmed findings
(SI-1/2/3/4 above) are cross-cutting: fixing them per-gate would
re-introduce them with the next gate.

## Decision

**Staged gate table.** Intake gates are rows of an ordered table
`(stage, name, gate_fn)`, stages `pre-execution | execution |
post-execution`. Gate functions are pure:
`gate_fn(ctx) → Refusal | Advisory | Silence`, with `ctx`
pre-gathered by the shell (status entries, log history, policy
globs, recorded rc, text tokens). **The ADR-009 evidence screen and
the determinism double-run are stage boundaries, not rows** — the
screen is a gate on execution, not a peer refusal (ADR-029,
Decision 1, cited here deliberately; rev-2's reviewers confirmed
the staged shape and the surviving requirement is this citation
plus fault preservation). The whole-sequence canary fault asserts
the staged order **and** preserves FAULT SD's non-flat contrast.

**CC-1 assembler.** The fold over the table's results: refusals
short-circuit at their gate; surviving advisories render as one
block, table order, post-append, through the SI-3 channel
contract (`--json` object + `truth: advisory:` prefix + `!r`
escaping). Override flags and their `override_report` rows are
generated from the table (CC-2 by construction).

**Invariants as faults.** SI-1/2/3/4 each get a canary arm in this
release: the subdir fixture (sweep from a subdirectory still
behaves), the unicode-filename fixture (quoted-by-default names
still match), the ESC-injection fixture (escaped rendering), the
policy-file state matrix (absent/committed-empty/dead-scope).

**Housekeeping shipped here because the table touches the same
code:** single fold in `cmd_stats` (consumers receive one shared
`(claims, ordered_events)` pair — today each re-folds and
re-sorts), `functools.lru_cache` on `_glob_rx` (pure; also speeds
the existing invalidation scan), and the copier `_skip_if_exists`
corrections (both new policy files, plus the accept-allow fix —
tr-f49a00ee).

## Explicit non-goals

No behavior change for users — R0 re-houses existing gates and
ships infrastructure; every subsequent ADR adds a row, not a
paragraph. No re-ordering of existing gates.

## Consequences

Ordering becomes data (testable), the fatigue budget becomes a fold
(enforceable), and the four invariants become properties of the
seam rather than disciplines of authors. Canary prefix: **GS**.
GS1: staged order asserted end-to-end; GS2: FAULT SD contrast
preserved under the table; GS3: subdir fixture; GS4: unicode
fixture; GS5: ESC-escaping fixture; GS6: `--json` advisories
object present; GS7: one-block fold on a double-advisory filing.

---

# ADR-034: Positive-claim exit gate (adopt first among gates)

Status: Proposed (rev-3; rev-2's ADR-035 with naming, decay, and
coverage completed)
Date: 2026-07-31

## Context

Unchanged from rev-2 (paper §4 hollow-VERIFIED; v0.9.11 warning;
the pilot QB-011 incident — evidence exited 1 at filing because a
stash-pop conflict resolution dropped the machinery.md
authoring-loop section; verifier caught it, retraction, successor).
The lexicon must be built: one undivided `QUANTIFIER_TOKENS`
exists, no negation constant. Empirical support, now on the
record: simulated over the 244 real VERIFIED filings in both
ledgers, the gate refuses 5 — the two motivating defects plus
three further exit-1 positive claims — and warns 6, each a genuine
absence proof; zero false refusals (`tr-166c4616`).

## Decision

`NEGATION_TOKENS` frozenset beside the lexicons: *not, neither,
nor, without, absent, lacks, lacking, missing, unused,
unreferenced* plus copies of the five negation-shaped quantifier
tokens (*no, none, never, nowhere, zero*) — copies, not a shared
reference (widening one must not silently widen ADR-007's gate);
fault X6 asserts the subset relation (one-directional tripwire:
catches removals, cannot catch new negation-shaped additions to
ADR-007's set — stated).

At VERIFIED intake — `truth claim` **and** `done --claim` (same
payload path; the paper's two real hollow instances were completion
claims) — after the double-run:

- text carries a `NEGATION_TOKENS` token → v0.9.11 warning path,
  exit-code free;
- text carries none AND recorded exit ≠ 0 → **refusal**: `a
  positive claim's evidence exited N — the command demonstrates
  nothing the sentence asserts (a hollow VERIFIED, this ADR). Fix
  the recipe, or state why a failing command proves this sentence:
  --evidence-exit-ok "<basis>".` Doctrine is cited, never a
  foreign ledger id (rev-2 named a pilot tr- unresolvable in any
  consumer repo).

**Flag and field:** `--evidence-exit-ok` / `evidence_exit_basis`
(house pattern names the overridden thing; `--exit-ok` is
ambiguous on `done`). **Decay decision (CC-2): declined, with
reason** — a legitimately-failing proof (differential `diff` exit
1) is a permanent property of the recipe, and re-verification
re-runs the command anyway; a decayed basis would re-ask a
question whose answer cannot change. `validate` refuses
`evidence_exit_basis` with recorded exit 0; tolerates legacy
records lacking `evidence.returncode`.

**Measurement:** `stats` gains warned/refused counters for exit≠0
VERIFIED filings; the overridden count is read from the
`override_report` row (single-homed, CC-2), not recounted.

## Explicit non-goals — residuals owned

Mixed sentences stay warnings (compound-sentence advisory named as
follow-on work — a deliberate deferral, not a silent drop). The
token test proxies the sentence's polarity, not the recipe's:
inverted recipes (`! grep`) exit 0 and pass silently; differential
proofs are falsely refused and pay one `--evidence-exit-ok` basis,
whose frequency the override row turns into a fact.
INFERRED/UNVERIFIED untouched.

## Consequences

The decidable slice of the hollow class dies at intake; the sim
says the price at current corpus scale is zero false refusals
(`tr-166c4616`). Canary: X1 positive+exit1 refused; X2
negation+exit1 warns only; X3 bare flag refused / basis stored;
X4 positive+exit0 silent; X5 validate cross-field; X6 subset
tripwire; X7 `done --claim` parity.

---

# ADR-035: Tombstone citation gate with preflight

Status: Proposed (rev-3; rev-2's ADR-036 with the I/O boundary
redesigned per the confirmed critical finding)
Date: 2026-07-31

## Context

The machinery.md retraction-sweep brain-rule, verbatim as in
rev-2. Volume: retraction is batch-shaped, not rare-as-six — the
pilot holds 66 retracted verdicts (`tr-efc43840`), the meta-repo
49 at anchor with 22 added in one day (`tr-d0759df4`), and 12 of
the meta's 49 are cited in tracked markdown outside archive
*right now*, including two rolled-over successors
(`tr-f0c94c6c`) — evidence both that historical citations are the
dominant false-refusal class and that stale successor pointers are
a real, current defect the gate would prevent.

The rev-2 mechanism (`git grep … -- <scope-globs>`) was falsified
by the structured review (confirmed critical): pathspec magic
inverts scope, dead globs read as clean (rc=1), git's glob grammar
diverges from the CLI's, and a subdirectory cwd silently truncates
the sweep.

## Decision

**Sweep (SI-1/SI-2 compliant).** After the ADR-011 ceremony, before
the append: shell runs `git grep -l -F <id>` **bare** — no
pathspecs, `cwd=repo_root()`, rc pinned (0 hits / 1 clean / ≥2 or
spawn failure = unavailable → **refuse with the reason**, the one
earned fail-closed). Core filters hits through
`match_paths(scope_globs)`; `.truth/claims.jsonl` is excluded
structurally in the core (retraction bases legitimately cite
successors — and this avoids the `:(exclude)` magic the pathspec
design would have forced).

**Scope policy.** `.truth/citation-scope` (consumer policy, SI-4:
`_skip_if_exists`, committed-empty = consciously-nothing = every
retraction sweeps clean silently; **absent = built-in default
`docs/specs/**` applies with a one-line notice**). The default is
calibrated by the pilot's own corpus: 28 distinct ids cited in its
six specs, intersection with its 66 retracted ids — empty; zero
day-one false refusals. At home the meta-repo has no `docs/specs/`
— acknowledged: the gate is vacuous there until the operator
declares a scope, and the notice says so.

**Refusal.** Citations found → refusal listing every citing file
with the ordered remedy (swap to the successor, then retract),
**with its own exit code** (next free small integer, the
impact/baseline precedent) so a sweep driver distinguishes it from
unknown-id, ack-mismatch, and unavailable, which all exit 1 today.
Deliberate orphaning: `--orphan-ok "<basis>"`, stored on the
verdict, counted (CC-2; decay: declined with reason — a tombstone
is terminal, there is no later re-ask). Per ADR-011's surface
rule, the refusal does **not** name the flag; the bypass lives in
`--help` and the README.

**Preflight verb.** `truth citations <id>…` — read-only, no
ceremony, exit 0 = clean / N = hits (listed, `--json`). A 25-id
sweep is one preflight pass, then ceremonial verdicts on the
already-clean set. A batch *ack* is refused on principle: ADR-011's
ack authorizes exactly one typed id ("a lingering environment
variable may not authorize arbitrary tombstones"). Noted cost:
each verdict invocation re-parses the ledger — O(ids ×
ledger-parse), the preflight amortizes the grep side only.

## Explicit non-goals — residuals owned

No automatic rewriting; no `diverge` coverage (only the terminal
verb earns the terminal check). Truncated-ellipsis citations stay
invisible to `-F` (companion hygiene rule: full ids in
scope-covered documents). TOCTOU between sweep and append accepted;
"retractions are all human" remains self-attested.

## Consequences

The two-step ritual becomes one verb that refuses in the wrong
order, batch-shaped, with a driver-usable exit-code contract.
Canary: TG1 in-scope citation refused listing files; TG2 swap →
proceeds; TG3 bare `--orphan-ok` refused / basis stored; TG4
out-of-scope citation does not block (pure-core property test);
TG5 grep-unavailable refuses loudly — written via the PATH-shim
pattern (a `git` wrapper passing everything except `grep` → 128);
TG6 preflight verb contract; TG7 subdir fixture (SI-2); TG8
dead-scope notice; TG9 id cited only in claims.jsonl proceeds.

---

# ADR-036: Volatile-recipe linter

Status: Proposed (rev-3; rev-2's ADR-037 with the tokenizer
replaced and policy semantics fixed)
Date: 2026-07-31

## Context

As rev-2 (three recipe rot classes + one watch rot class;
tr-22853f21, tr-3b69f8ff and their fates; phrase arm dropped —
subsumed by ADR-034's refusal). One correction from the review:
the proposed whitespace tokenizer would have been a *third* parser
of evidence commands, violating the recorded one-screen-parser
rule (the F1/F5 drift lesson) and gameable by quote-splitting
(`grep 'v0.9''.8'`).

## Decision

- **Tokens come from the screen.** `recipe_lints` consumes the
  shlex token stream `screen_evidence_command` already produces —
  exactly one screen-side tokenization exists. Path-context and
  carve-outs are defined per shlex token: a token is path-context
  iff it contains `/`; carve-outs are a named tuple of rules
  (path-context; schema-`$id` pattern; frozen-date context — a
  date immediately preceded by `Accepted (` inside the same
  token), extended only with RC faults. Measured residual after
  carve-outs: 13/98 meta commands warn, 9 correctly
  (release-expiring pins), 4 fixed by the frozen-date rule.
- **`-n`/`--line-number` in grep-family commands → warning**
  (zero occurrences in the meta corpus today — zero fatigue cost).
- **Generated-paths refusal at the INV-M position**, every
  evidence class (an INFERRED claim watching a generated file
  restales identically). `.truth/generated-paths`: consumer
  policy per SI-4 — committed-empty (as shipped) is **silent**;
  absent prints the one-line notice; `--generated-ok "<basis>"`
  stored and counted (CC-2; decay: **included** — ADR-032 default
  expiry applies, because "this path is generated" rots as build
  systems change, and the re-ask is exactly the scan-materialized
  loop ADR-032 built).

Warnings never refuse (ADR-014's confused-deputy lesson, correctly
attributed since rev-2).

## Consequences

Two field rules fire themselves; the generated list becomes policy
with a refusal at the position that covers all classes. Canary:
RC1 `-n` warns; RC2 version literal warns naming the token; RC3
carve-outs as properties (path segment, schema-`$id`, frozen date
do not warn); RC4 generated match refused for a non-VERIFIED
class too / `--generated-ok` stores basis; RC5 absent list →
notice, lints still fire; RC6 committed-empty list → silence
(SI-4 split); RC7 quote-split literal (`'v0.9''.8'`) still warns
(shlex-token property).

---

# ADR-037: Dirty-watch advisory

Status: Proposed (rev-3; rev-2's ADR-034 with the mechanism
corrected per SI-1/SI-2 and the conflict-state finding)
Date: 2026-07-31

## Context

As rev-2 (machinery.md's authoring loop: "commits the CONTENT
first … restales at birth"; INV-M refuses untracked watch paths
**for literals only** — explicit globs are exempt by design, so a
glob watching only untracked content is a live restale-at-birth
vector). The class is measured: 29/895 meta and 37/390 pilot
invalidations land within 30 minutes of their claim's own birth;
one pilot claim restaled 3× within 18 minutes (`tr-5c2bd165`).

## Decision

Shell: `git status --porcelain=v1 -z` at `cwd=repo_root()` (NUL
fields — no C-quoting, renames emit both paths as separate
fields). Core: an entry is dirty iff `XY ∉ {'  ', '!!'}` — the
structural definition, which covers the unmerged states (`UU` et
al.) a letter list misses; dirty *during conflict resolution* is
precisely the QB-011 scenario. `??` entries count when the watch
is a glob. Matching via `match_paths` (never git pathspecs —
SI-1; rev-2's `git status -- <paths>` reintroduced the v0.4
over-match). Advisory only, in the CC-1 block; no override flag
(nothing is refused). Measurement caveat owned: the birth-restale
metric cannot distinguish own-content landings from fast unrelated
commits — "approach zero" is an upper-bound target.

## Consequences

No schema, mirror, FS-2, or `$id` work (CC-4) — the sync surface
is code, stderr, and docs. Canary: DW1 modified watched path →
advisory; DW2 clean tree → silence; DW3 dirty unwatched file →
silence; DW4 untracked file under a glob watch → advisory; DW5
untracked outside the watch → silence; DW6 uncommitted `git mv`
→ advisory on either path; DW7 unicode-named watched file →
advisory fires (SI-2 end-to-end); DW8 `UU` conflict state →
advisory.

---

# ADR-038: Blast forecast and churn report — advisory only

Status: Proposed (rev-3; rev-2's ADR-038 with subprocess
discipline, unborn-HEAD handling, self-calibrating floor, and the
BF prefix)
Date: 2026-07-31

## Context

As rev-2 (churn cost; tr-23661434's recomputed profile; the
refusal gate severed — the threshold replay stands on the record:
82/96 meta path-claims exceed 15, `tr-c3087292`; the reaffirm
trial reads ~2026-08-08). The estimator remains an upper bound,
stated.

## Decision

- **Shell**: one `git log --since=<window> --name-only -z
  --no-renames` (or `-c core.quotepath=off`) at `cwd=repo_root()`;
  window applied at the shell edge (the codified house style — the
  purity objection was refuted; the boundary is nonetheless
  canary-pinned, below). rc ≠ 0 (unborn HEAD, any failure) → loud
  `blast: history unavailable` notice in the block;
  `blast_forecast` stored **absent**, never 0. Shallow repo
  (`git rev-parse --is-shallow-repository`) → floor-not-bound
  notice.
- **Core**: dedupe the emitted paths to a distinct set, match once
  through memoized `match_paths`, count commits whose set
  intersects. Optional saturation at 10× floor with `>=N`
  stored semantics (report survives saturation).
- **Floor, self-calibrating**: the advisory prints when the
  forecast ≥ floor, where floor = P90 of stored `blast_forecast`
  values over currently-live path-claims when ≥20 exist, else the
  constant 15. Rationale: a per-repo percentile stored as a
  universal constant is a category error — at home, 15 would print
  on ~85% of filings (`tr-c3087292`); in the pilot it is mostly
  silent on a one-commit margin. The effective floor is printed in
  the `stats blast` section so calibration is visible, and the
  constant fallback changes only with BF faults.
- **Report**: `stats blast` — observed invalidations vs
  forecast-at-filing per claim, per-path staler ranking (the
  invalidation records already store touched files; no git work),
  effective floor. ADR-033's move, named as such.
- **The refusal gate returns only as its own ADR** after ≥30 days
  of forecast-vs-observed data AND the reaffirm read, threshold
  derived from the measured distribution.

## Consequences

Authors see the price of a broad watch with honest semantics; the
operator gets the churn ledger; the gate question becomes a
measurement with a date. Canary (prefix **BF** — BL is taken,
tr-624d5916; DW/TG/RC/BF free, tr-4387f0ea): BF1 ≥floor →
advisory line; BF2 sub-floor → silence; BF3 shallow → notice; BF4
`blast_forecast` stored, validate tolerates absence; BF5 report
fixture with known counts; BF6 window boundary — a
`GIT_COMMITTER_DATE`-backdated out-of-window commit is not
counted, an in-window one is; BF7 unborn-HEAD → loud notice,
absent field.

---

## Adoption order and per-release checklist

**R0 (gate system) → 034 (exit gate) → 035 (tombstone+preflight) →
036 (linter) → 037 (dirty-watch) → 038 (blast).** R0 first because
five confirmed findings are system properties; the exit gate first
among gates (proven defect class, zero false refusals in
simulation, subsumes the phrase class); blast last (its report
decides whether a blast gate ever exists).

Every release: canary prefix check per CC-3; override flags land
in `override_report` in the same diff (CC-2) with their decay
decision stated; schema/`$id`/mirror/FS-2 only where the record
shape changes (CC-4: R0 and 037 ship none); docs sync (paper §1,
machinery.md, `.truth/README`) per release, never batched. Every
constant (window 30 d, fallback floor 15, lexicon contents,
carve-out rules) changes only with its faults; the field decides
the numbers.

## Considered and rejected (carried from the plan of record)

1. Gate table flattens the ADR-009 screen (refuted — staged by
   design; ADR-029 is cited in R0 and FAULT SD is preserved).
2. Python glob matching is the per-filing hotspot (refuted — the
   benchmark's "30-day window" was full history on a dormant repo;
   real 30-day volumes are 84–447 commits; `lru_cache` kept as
   polish).
3. The shell-edge `--since` window is impure (refuted — codified
   house style; the BF6 boundary arm is kept because BLAST_WINDOW
   is a constant paired with faults and no arm tested the boundary).
