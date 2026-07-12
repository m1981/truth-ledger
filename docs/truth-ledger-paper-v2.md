# The Truth Ledger: A Claim-Invalidation Layer for Agentic Software Development

**Status:** v2. Merges the frozen v0.4 audit with pilot field evidence through
2026-07-09 into one living document, superseding the earlier split between
`truth-ledger-paper.md` (audit, frozen at v0.4) and
`truth-ledger-field-notes.md` (deployment, formerly living) — both now
retired to `docs/archive/`. Artifact version audited:
v0.4. Artifact version deployed in the pilot: v0.5.3 (the template has
since moved to v0.6.2, including the v0.6 solo-regime hardening batch —
ADR-007 through ADR-012 plus FS-1/FS-2, which converts several of this
paper's "accepted" and "future work" items below into shipped
mechanisms, noted inline where they land; pilot sync pending, §2). Pilot: one multi-component
kitchen-manufacturing monorepo (domain core, catalog service, ERP, CAM, two
adapters), one solo developer, LLM agent sessions doing the implementation
work, day-0 2026-07-08. All quantitative claims in §2 are self-reported by
that same developer, who is also this paper's sole author and auditor —
see §8 item 1.

**How to read this paper.** Section headers are ordered by evidence class,
not narrative convention: mechanism and measurement first, interpretation
last. §6.2 is explicitly optional — skip it if you want the artifact, not
the theory. §6.1 isn't: it's the analysis §2 promises and §10 builds on.
§7 applies the artifact's own discipline to this document: a table of what
would falsify this paper's own claims.

---

## 0. What this is, in one paragraph

Language-model agents assert facts about codebases — "this module owns all
currency conversion," "no call sites remain for this API" — with no record
of how the fact was established and no mechanism for a later code change to
invalidate it. The truth ledger is a cache-invalidation system for those
sentences: every trusted claim carries a command whose output was hashed at
a known commit, and any subsequent git event or elapsed TTL that could
undermine the claim mechanically demotes it. That's the whole idea. Sections
1–5 are that idea, its measured behavior in one real deployment, and the
defects an adversarial audit found in it. Section 6 is the theoretical
vocabulary (Byzantine fault tolerance, entropy) that motivated the design —
presented after the mechanism, and after the field correction to what that
vocabulary got wrong.

---

## 1. The mechanism

**Storage.** A single append-only JSONL file, `.truth/claims.jsonl`, beside
a work tracker it never writes to. A dependency-free Python CLI
(`scripts/truth` — roughly 750 lines at the v0.4 audit scope §3–§4 cover,
and grown severalfold since as the work kernel, the §5 satellites, and
the v0.6 hardening landed; the file states its own current size and
version), two shell gates (`check-truth.sh`, a commit-time prefix check, and
a post-merge invalidation-scan hook), a fixed verifier prompt, a JSON
Schema. Concurrent writers are assumed, not incidental: multiple appends
racing to the same file rely on POSIX `O_APPEND` atomicity for
single-write-call, single-filesystem safety — stated here as a load-bearing
assumption, not only as the caveat it also appears as in §8.

**Six record kinds**, sharing an envelope (`id`, `kind`, `actor`,
`session`, `ts`):

- **claim** — an assertion with an `evidence_class` (VERIFIED / INFERRED /
  UNVERIFIED), a `cost_tier` (P0/P1/P2, the cost of acting on it if false),
  and — for VERIFIED — an evidence capsule: the command run, a SHA-256 of
  its output, exit code, the anchor commit, and either watched
  `evidence_paths` (facts git can see) or `ttl_days` (facts about the
  world outside the repository).
- **verdict** — a judgment (`agree` / `diverge` / `cannot_verify` /
  `retracted`), always with a `basis` sentence.
- **invalidation** — a mechanical demotion: evidence paths touched, TTL
  elapsed, or anchor commit unreachable after history rewriting.
- **premise** — a work item's declared dependency on a claim.
- **issue** / **issue_event** — added by the work kernel (§5, its design
  record ADR-002, not reproduced in this paper):
  work items are folded the same way claims are, so premise-at-birth and
  claim-at-death are more events in the same log rather than a second
  system.

**Derivation.** The fold below covers claim status; the work kernel adds
an analogous fold for issue status, described in §5. Status is never
stored; a pure function replays the log:

```
no events              → unverified
verdict agree          → live
verdict diverge        → diverged        (queued for attention)
verdict cannot_verify   → cannot_verify   (queued if P0)
verdict retracted       → retracted       (terminal — later events ignored)
invalidation            → stale           (queued if P0/P1)
```

A claim is born `unverified` regardless of its `evidence_class` — filing a
VERIFIED claim runs and hashes the evidence command at intake, but that
double-run is a gate, not a verdict; only an explicit `agree` event (via
`truth dispatch`, §1 Verification below) advances it to `live`. This is
deliberate: evidence attached at filing and evidence independently
confirmed are kept as two distinct events in the log, never conflated.

Terminality of `retracted` is the strongest promise the system makes: a
human decision to kill a claim cannot be undone by any later event —
**on the paths this design defends against**, precisely stated below.

**Fold semantics, precisely.** The fold replays every event — claim,
verdict, invalidation, premise — in the canonical total order
`(timestamp, id)`, ascending, regardless of file position (this is what
makes replay order-independent; §4, F3). Within that order, the *first*
claim record to establish a given id fixes that claim's text and evidence
capsule; any later claim record bearing the same id is ignored for content
(§4, F6) — its append is permitted (the log is append-only, not
edit-only) but has no effect on derived state. Composing this with the
accepted timestamp-forgery threat (§8 item 6) yields one composition
gap, stated plainly rather than left implicit: an appender who backdates a
duplicate-id claim record to sort *before* the genuine one in canonical
order becomes "first," silently substituting its text and evidence
capsule under an id that may already carry a live verdict. Verdicts and
invalidations still apply correctly to whichever content wins — no
verdict is lost or misattributed — but the claim's *substance* was not
protected against this specific composition of two individually-documented
behaviors. As of v0.6 this composition is **detected at commit**
(ADR-008): within one repository's history, file order is append order —
a guarantee the INV-A prefix gate already provides — so `truth validate`
(and therefore the commit gate) fails any record whose envelope id
duplicates an earlier line's with a strictly earlier `ts`. Identical
duplicated lines (git's union-merge shape) still pass. The residual that
remains accepted, not detected, is timestamp forgery on a *fresh*
(non-duplicate) id — §8 item 6.

**Intake gates.** `truth claim` refuses, before anything is written:
empty claim text (v0.5.5 — an assertion with no sentence cannot be
verified, diverged from, or cited); near-duplicates of active claims by
word-level, case-folded token overlap ≥ 0.6 against claim text
(overridable, and always allowed for corrections of dead claims);
a universally quantified claim text over a scoped evidence command
(ADR-007, v0.6 — the §2 dominant-failure countermeasure §10 once listed
as unbuilt; refused unless `--scope-ok "<one sentence>"` states why the
scope covers the quantifier, stored as an attackable `scope_basis`);
dead-tripwire evidence paths (INV-M, v0.5.4 — a whitespace-containing
entry with no comma, or a literal path matching zero tracked files;
explicit globs exempt; applies to *any* evidence class carrying paths,
and has no override); VERIFIED claims with no evidence command, with
neither paths nor TTL, or filed in a repository with no commits to anchor
to (these three checks are VERIFIED-only; UNVERIFIED and INFERRED claims
may omit evidence, paths, and TTL); evidence commands failing the
read-only safety screen against the committed `.truth/evidence-allow`
allowlist (ADR-009, v0.6 — the command re-executes later inside verifier
sessions; `--evidence-unsafe-ok` files with `screened=false` and recheck
then refuses to ever execute it); evidence commands whose two intake
runs hash differently (nondeterministic, overridable); and INFERRED
claims with no `--basis`. The list is stated here in refusal
order, which is observable when one claim trips several gates.

**Invalidation.** A scan, wired to post-merge hooks or CI, demotes claims
whose premises git can check. Anchor-loss after rebase/squash/gc demotes
with reason "anchor unreachable" — failing toward distrust rather than
assuming innocence.

**Verification.** `truth dispatch <id>` emits a fixed prompt plus the claim
record — never the authoring session's transcript or reasoning. The
verifier first runs a deterministic recheck (hash mismatch → diverge;
command not found → cannot_verify), then independently judges whether the
evidence supports the claim's *text* — the gap between "does this command
still produce this output" and "does this output support this sentence."
Verifiers cannot retract.

**Policy.** `truth ready` intersects the work tracker's unblocked issues
with premise validity, tier-sensitive: `live` passes; `unverified` passes
with a warning; `cannot_verify` blocks only P0 premises; `stale`,
`diverged`, `retracted`, and missing claims always block. Work may proceed
on an unverified premise that later proves false — a stated trade for low
filing friction, with a named fallback if warning fatigue appears.

That is the entire mechanism: an event log, a derivation function, entry
gates, exit triggers, an independent recheck, and a policy join. Nothing
above this line requires the word "Byzantine."

---

## 2. What it actually catches, with numbers

One pilot repository, one solo developer, LLM agent sessions doing the
implementation work — the regime the design targets. Day-0: 2026-07-08.
Measured as of 2026-07-09:

| Measure | Value |
|---|---|
| Verifier dispatches | 32 |
| — agree | 29 |
| — diverge, genuine (claim actually wrong) | 2 |
| — diverge, mechanical (evidence recipe changed, fact still true) | 1 |
| — cannot_verify | 0 |
| Claims in ledger | 21 (15 live, 6 retracted) |
| Human retractions (`TRUTH_HUMAN=1`) | 6 — all by the human, none by an agent |
| Concurrent agent sessions writing one ledger | 6 interleaved, zero corruption |
| Tripwire recall & false-alarm rate (post-commit scan, one real refactor) | 1/1 staled when it should have (recall), 0 false alarms that round (precision signal; both n=1) |
| Seeded faults, this repo's template canary | the suite prints its own count — no number restated here, since the suite has grown with every mechanism since v0.4's 19 (work kernel, spec-health/doc-health satellites, F7/ADR-006, INV-M, S4, the impact verb's W-faults, and the v0.6 hardening batch's Q/B/E/V/H/M faults) and is no longer frozen; Appendix B |
| Seeded faults, the pilot's downstream canary | grew 19 → 42 → 45 → 48 → 49 in step with the pre-v0.5.4 merges, matching the template through v0.5.3 (F7/ADR-006 synced 2026-07-09); the template has grown well past that since — pilot sync is pending, so the two suites diverge until the next `copier update` (Appendix B) |

**The dominant real failure mode is scope overreach, not hallucination.**
Both genuine divergences shared one shape: a *correct* evidence command
backing an *overreaching* claim text — a repo-wide clause ("the only
occurrences in the repo are…") backed by a package-scoped grep whose
`--include` filter was doing invisible work. Same author, same defect
pattern, caught twice by independent verifiers (n=2, same author, same
defect shape — a signal, not yet a distribution). Zero fabricated or
hallucinated claims were observed in this window. This matters beyond the
pilot's small N: it is evidence about what kind of failure this tool is
actually built to catch, addressed directly in §6.1.

**Scripted independence held, and exceeded its brief.** Verifiers
receiving dispatch-only context (no authoring session's reasoning) caught
the author both times a divergence occurred. Twice, independently, a
verifier went further than asked — tracing a claim about commit-time
enforcement to the actually-active hook manager rather than trusting a
vestigial config path, unprompted skepticism about a norm dressed as an
enforced property — the same pattern F4 names in §4.

**The repairs held under real concurrency.** Re-verified claims stayed
live across subsequent scans (no re-staling loop); human-gated retraction
was exercised six times, always correctly; near-duplicate intake fired
correctly once and was consciously overridden; six concurrent sessions
interleaved appends with zero corruption and an order-independent fold.
Small-scale evidence only — six sessions on one machine is not two humans
on two machines, and the paper's single-regime caveat (§8) stands.

---

## 3. The audit method

Seven instruments, each targeting a defect class the others miss:

1. **Consistency audit of the specification** — diff every contract
   representation (README, schema, code, diagrams) against the others;
   two copies of one contract will drift.
2. **Seeded-fault acceptance testing** — run the shipped fault suite to
   establish a baseline, then audit its *coverage*: which stated
   properties does no seeded fault exercise?
3. **Property-based and permutation testing** — state invariants as
   universally quantified properties and search for counterexamples (the
   QuickCheck lineage; Claessen & Hughes, 2000); for an event-sourced log
   merged by union, the decisive property is confluence (every event
   order folds to the same state).
4. **Adversarial capability enumeration** — list every actor (agent
   session, human, verifier, CI) and, for each capability that actor
   *actually has*, attempt to violate an invariant using only that
   capability. Every property lands in exactly one bucket: prevented,
   detected, or accepted-and-documented. Anything in no bucket is a
   finding.
5. **Boundary and degenerate-case analysis** — empty logs, duplicate ids,
   same-timestamp events, glob edge cases, rewritten history.
6. **Fail-open analysis of the detection machinery** — does a detector run
   when its optional dependency is absent, and if not, does the suite fail
   or silently pass?
7. **Independent reproduction and recursion** — every finding demonstrated
   by a runnable script against the real artifact in a fresh sandbox, and
   the method turned on its own output: every repair must pass the
   *original* acceptance suite, unchanged.

The organizing rule across all seven: evidence is survival of a genuine
attempt at refutation, not accumulation of green runs. A hundred passing
fault-suite runs are worth less than one well-aimed attack that fails to
land.

---

## 4. Findings and repairs

Nine defects, six from the original audit (v0.2/v0.3 → v0.4) and three
found later by inspection — one during pilot deployment (v0.5.x), one
during a documentation-accuracy pass that re-derived an ADR's rationale
against the shipped CLI rather than trusting the ADR's prose (v0.5.3),
and one during a four-agent cross-corpus audit that probed the stdlib
validate mirror against the JSON Schema live rather than trusting the
conformance suite's green run (v0.5.5). Each row: what broke, how it was demonstrated, whether the
shipped test suite would have caught it, and the fix.

Severity scale: Low (cosmetic/documented risk) < Medium (wrong status
under a specific, narrow condition) < High (wrong status under normal
operation) < Critical (a headline invariant falsified by an attack no
gate covered).

| # | Finding | Severity | Demonstration | Caught by shipped tests? | Fix |
|---|---|---|---|---|---|
| F1 | Schema stale against code on two features (`retracted` verdicts, TTL-only claims); drift detector fails open (silently skips) without an optional dependency | High | Real CLI produced a ledger the schema rejected; suite reported `OK (skipped=2)` without `jsonschema` | Only if the optional dependency was installed | Schema updated; missing dependency is now a **test failure** unless explicitly waived — the detector fails closed (blocks) instead of open (skips) |
| F2 | Re-verified claims re-stale every scan — anchor frozen at filing, never advanced | High | stale → agree → live → next scan, zero new edits → stale again | No | `agree` verdicts on path-anchored claims advance an **effective anchor**; scan diffs from it |
| F3 | Fold not confluent under union merge — `{agree, diverge}` folds to `live` or `diverged` depending on merge direction | Medium | Exhaustive permutation check | No | Fold sorts events into total order `(timestamp, id)` before replay — the standard CRDT last-writer-wins move (Shapiro et al., 2011) |
| F4 | "Retraction is humans-only" enforced nowhere — CLI checked only that a basis was present, never the actor | Medium | Verifier-actor retraction accepted | No | v0.4: retraction requires setting `TRUTH_HUMAN=1` — a self-attested convention with a syntax, not an identity-checked property; any actor able to set an environment variable could still retract. Hardened in v0.6 (ADR-011): the variable alone is refused — a tombstone additionally needs an interactive typed-id confirmation at a real terminal, or `TRUTH_HUMAN_ACK=<exact-id>` for headless human use, closing the one-export bypass the refusal message itself used to teach (§8 item 5) |
| F5 | Evidence-path globs cross directory separators (`src/*.py` matches `src/sub/deep.py`) | Low | Direct check | Partially | Custom glob translation: `*`/`?` stop at `/`, `**` spans |
| F6 | **Tombstone resurrection by pure append** — a duplicate claim record bearing a retracted id resets status to `unverified`; both shipped gates (diff-deletion heuristic, well-formedness check) pass it | Critical | A retracted P0 claim — text: *"the database is safe to drop"* — resurrected through both gates and `validate` | No — the canary seeded this fault only on the verdict path | Fold ignores duplicate claim ids (first wins); commit gate replaced with a line-prefix check: the staged file must literally extend the committed one — see §1's "Fold semantics, precisely" for a related composition gap this fix did not close, since detected at commit by ADR-008 (v0.6) |
| INV-M | **Dead tripwire** — space-separated `--paths` ("a.sh b.sh") silently stores as one literal path matching nothing; the claim is true, the hash matches, the verifier agrees, and the invalidation trigger can never fire | High | Found by inspection in the pilot ledger, not by any gate | No — nothing checks a claim's protection metadata for validity | Shipped (v0.5.4): intake refuses (a) whitespace-containing path entries with no comma and (b) any literal (non-glob) path matching zero tracked files at filing time; explicit globs (`*`/`?`) are exempt — watching a pattern that's empty for now is legitimate intent, unlike a typo'd literal. Applies to any evidence_class carrying paths, not only VERIFIED, since invalidation itself doesn't discriminate by class. `FAULT T`, self-defense verified; also caught a live fixture bug (an existing canary claim filed on an untracked path) in the process |
| F7 | **Issue-fold premise-stripping by pure append** — ADR-002's issue fold was last-wins on duplicate `wk-` ids ("update-by-refile"); a raw appended duplicate with `premises: []` silently disarmed an issue's ADR-001 protection. Unlike F6, no backdated timestamp was needed (last-wins means any later real timestamp wins) and no terminal-state coincidence was needed (works on any open issue, not only a retracted one) | High\* | A HELD issue (broken premise, `tr-... (stale)`) flipped to READY after one raw JSONL append, no CLI involved; `truth validate` still passed | No — no canary fault or unit test exercised a duplicate `wk-` append; the one existing unit test on this path (`test_last_issue_payload_wins`) asserted the vulnerable behavior as a feature | `fold_issues` is now first-wins on duplicate ids, identical to `fold()` (ADR-006). The "update-by-refile" rationale it replaced described a verb the shipped CLI never implemented — `truth issue` always mints a fresh id from `hash(payload, ts, actor)`, so no command could legitimately re-file an existing `wk-` id; last-wins was pure attack surface |
| F8 | **Schema-mirror drift, recurrence of F1's class** — `validate`'s stdlib mirror accepted a claim record with no `text`, which `claims.schema.json` requires at minLength 1; `truth claim ""` filed a record the schema rejects and the INV-B commit gate would then block — a CLI contradicting its own gate | Low | Live probe: a payload of only `evidence_class`/`cost_tier` returned `validate: 1 record(s) OK` | No — the shared conformance corpus (F1's own fix) carried no missing-text fixture | Shipped (v0.5.5): mirror rejects missing/empty claim text; intake refuses empty text; two corpus fixtures added. The second recurrence of this class upgrades "keep the corpus exhaustive" from advice to structural future work (§10) |

\* By this table's own definition of Critical ("a headline invariant
falsified by an attack no gate covered"), F7 reads Critical: the ADR-001
gate `truth ready` exists to enforce was falsified, and nothing caught
it. Rated High instead because the enabling *capability* — an
attributable forged append with a chosen `ts` — is the same
already-accepted class named in §8 item 6, not a newly discovered one;
F7 is a previously unexamined application of that capability, not a new
capability. Recorded as a judgment call against the scale, not a
mechanical reading of it — a second auditor may reasonably disagree.

**Verification effort at repair time (v0.4):** 41 unit and conformance
tests green with the schema detector armed; 12 new regression tests added,
unevenly across findings — three each for F2/F3/F5/F6, with F1 and F4
covered instead via the conformance corpus and canary; 19/19 seeded faults
caught, up from an original 14 — the original 14 unchanged and still
green, which is what demonstrates behavior preservation rather than merely
new coverage.

**What survived attack** (the negative results, reported because a method
that only reports hits is not measuring anything): retraction terminality
held on the verdict path under reordering and resurrection attempts before
the fix; all intake gates fired as documented; the invalidation scan is
idempotent; degenerate ledgers fold cleanly; the readiness matrix matches
its design record (ADR-001, not reproduced here) cell-for-cell;
anchor-loss demotion fails toward distrust; the
dispatch seam leaks no author reasoning; the core is a pure function of
time and touches no I/O, which is what made unit-level attacks on it cheap
in the first place.

**A prediction the evidence refuted:** F1's root cause was predicted to be
fixture-corpus omission. Wrong — the corpus contained both cases, and the
suite failed correctly when armed. The real cause, a detector failing open
on an absent optional dependency, was worse for process and better for
design than the prediction. Recorded because a method that cannot be
surprised isn't testing anything.

**The recursive episode, twice.** The first attempt to fix F3 used
second-granularity timestamps; same-second events tied and fell to a
random id tie-break, making the fold confluent but wrong under ties — the
original, unchanged acceptance suite caught its own auditor's bug
nondeterministically, fixed by moving to microsecond timestamps. Months
later, in the pilot, a dead-name pre-commit check fired on the very commit
introducing the naming convention it enforces, and again on its own
author's later edit. Two instances, in different codebases and different
timeframes, are a pattern worth watching rather than an established
operating mode — deliberately kept out of §7's falsifiability table,
since two data points support no real falsifier; a third instance, or a
long dry spell, would be the honest way to revisit this claim later.

---

## 5. What generalizes: citation over restatement

One pattern recurred across every new mechanism the pilot grew: **facts
restated in prose rot; facts cited by id stay checkable** — the same
structural growth Lehman documented for code itself, absent explicit
counter-effort (Lehman, 1980), applied here to knowledge about code rather
than the code. Three mechanisms fell out of this observation, all now
upstream in the project template:

- **Work kernel** — work items are ledger records with a premise declared
  at birth and a completion claim filed at death; readiness requires open
  status, closed dependencies, *and* valid premises.
- **spec-health** — feature specs may state facts only by citing ledger
  ids; a sweep judges every spec by the readiness status of the ids it
  cites. A cold review of the pilot's first spec immediately found the
  convention's own blind spot: a fact that is premise of no cited work
  item is invisible to the readiness check — now a warning.
- **doc-health** — the same discipline applied to prose generally:
  forbidden post-rename names, broken relative links. A sweep of the
  pilot's 105 live markdown files found decay **concentrated entirely in
  pre-ledger prose** — every document written under the citation
  convention came back clean but one routing gap.

That last result is evidence for a claim the original design never
explicitly made: this isn't only a detector of decayed facts after the
fact — citing a fact by id, rather than restating it, may prevent the
decay at the point of authorship. One repository, 105 files, one sweep, is
not a controlled trial and does not establish causation; the distribution
(100% clean post-convention, all rot pre-convention) is a plausible signal
worth a real test — a second repository, or a before/after within this
one as more documents accrue — not yet a demonstrated effect.

The transferable idea, held to that same caution, is the pattern rather
than any one satellite: an artifact class admitted into a repository
plausibly needs its own health tripwire at the moment it's admitted, or it
risks becoming archive material — a hypothesis this pilot is consistent
with, not one it proves.

---

## 6. Interpretive framings

This section names the theoretical vocabulary that motivated the design,
each corrected against what the field evidence supplied. None of it is
required to operate the artifact — but §6.1 isn't decoration: it's the
analysis §2 promises and §10's proposed countermeasure builds on.

### 6.1 Byzantine fault tolerance — as analogy, corrected

Byzantine fault tolerance (Lamport, Shostak & Pease, 1982; Castro &
Liskov, 1999) formalizes agreement when components fail arbitrarily —
crashing, lying, colluding — and its transferable idea is structural:
trust need not be a judgment about a component, it can be a checkable
property of a protocol's redundancy. This system borrows that *move* —
replace "do I trust this claim" with "does the structure guarantee a
false claim is detected" — and explicitly does not borrow BFT's
machinery: there is no quorum, no `3f+1` replica bound, no vote. It is not
a consensus protocol and was never meant to be one: it targets one
operator's sessions, not open, mutually distrusting replicas.

The original design motivation mapped failure classes directly: crash
faults to unverified claims, omission faults to silently outdated facts,
Byzantine faults to hallucinated or forged claims, correlated faults to a
verifier sharing the author's priors. Field measurement (§2) found none
of the pilot's real defects in the Byzantine or correlated-fault rows —
zero hallucinations across 32 dispatches. The dominant real fault, scope
overreach by an honest actor with honest evidence, has no row in the
table at all: it isn't a crash, an omission, a lie, or a shared bias. It's
a mismatch between a quantifier in natural language and the domain of the
command that was supposed to support it — a fault category native to
*this* domain (claims stated in prose) with no analogue in a domain about
computational agreement. The honest conclusion is that BFT contributed a
useful design stance and an overclaimed failure taxonomy; the taxonomy
should be read as a starting enumeration, not a closed one.

### 6.2 Entropy — as unformalized metaphor

At verification, uncertainty about a claim is reduced to near zero and
the anchor commit timestamps that moment; every subsequent event that
*could* invalidate the claim reinjects uncertainty whether or not it
actually changed the truth value, because the observer cannot know
without re-checking. Under this reading, `evidence_paths` and `ttl_days`
are an explicit model of a fact's decay channels, and `stale` is the
mechanical admission that accumulated uncertainty crossed a threshold.
This is a framing, not a formalism: no entropy is computed anywhere in
the system or in this paper. The field data in §2 (dispatch counts,
divergence rates) is exactly the raw material a real calculation would
need — an estimated claim half-life per cost tier, from which intake
could suggest TTLs instead of relying on author guesses. As of v0.6
that calculation exists mechanically (FS-1): `truth stats` reports
per-tier live→stale half-life from the ledger's own history, and once a
tier has ≥5 observations, filing a TTL'd claim prints the observed
median beside the author's choice — a suggestion, never a substitute.
Whether the suggestion is *calibrated* remains unmeasured; this section
still should not be read as a formalized result.

---

## 7. This paper's own claims, and what would falsify them

Applied to this document the discipline it applies to the artifact —
Popper's demarcation, that a claim is scientific only insofar as it
specifies what would refute it, used here as an acceptance criterion
rather than a philosophical commitment (the invariant table of Appendix A
is one row per property, naming its falsifier and its gate; §3's method
attacks the falsifiers themselves, since a weak one passing proves
nothing): each claim below is falsifiable by a specific, nameable
observation.

| Claim | Falsified by |
|---|---|
| Hallucination is not the dominant failure mode in this deployment regime | One confirmed fabricated claim (fact asserted with no basis in reality, not merely scope overreach) appearing anywhere in the pilot ledger's history |
| Scope overreach, not fabrication, is the pilot's dominant real failure | A third genuine divergence whose cause is not a quantifier/evidence-domain mismatch |
| The v0.4 repairs hold under real concurrent use | Any corruption, lost update, or non-confluent fold observed in the pilot's git history of `.truth/claims.jsonl` |
| Citation discipline is *hypothesized* to prevent documentation decay, not only detect it (§5 states this as a hypothesis, not a result) | A post-ledger-convention document found to contain undetected rot, discovered by any means other than the doc-health sweep itself |

The first two rows share one underlying dataset — 32 dispatches, 2 genuine
divergences, same author — so they are two readings of one small sample,
not two independent confirmations, and should be weighted accordingly.
Their falsifiers are also deliberately hair-trigger relative to the
claims' actual logical form: one fabricated claim would not mathematically
overturn "not dominant," and one differently-caused divergence would not
overturn "dominant" out of three. Read both falsifiers as tripwires that
should prompt re-examination, not as strict logical negations — precision
this table cannot fully deliver from n=32.

**Deliberately absent from this table:** two claims that don't belong in
a falsifiability table by its own admission rule. First, *this system
generalizes beyond a solo-developer regime* — not a claim this paper makes
anywhere; §8 item 4 names single-regime evaluation as an open limit, not a
result. Second, *recursive self-catching (§4) is a repeating pattern, not
a single episode* — discussed in §4 as two observed instances, but a claim
this table cannot state a real falsifier for (no fixed observation window
would cleanly refute "pattern" from two data points), so it stays a
narrative observation in §4 rather than a row here. A falsifiability table
should not include claims the paper itself disclaims, or claims it cannot
actually falsify.

The single largest claim this paper does *not* make, and should not be
read as making: that the ledger reduces false-VERIFIED rates in practice.
Everything above concerns mechanism — the machine detects what it is
built to detect. Whether it *helps*, net of the friction it adds, requires
the control comparison described in §10 and has not yet been run.

---

## 8. Honest limits, ranked

Ranked by how much a skeptical reader should discount everything above
this list before weighing it, not by raw "size" alone: item 1 conditions
trust in every number in §2 and every defect in §4, so it leads even
though item 2 names the largest single *unanswered question*.

1. **Single-observer conflict of interest, in both halves.** The audit
   battery was assembled by one auditor; the pilot's operator is also the
   artifact's sole author and this paper's sole author. Every number in
   §2 and every defect in §4 is self-reported by the same person who
   built the thing being measured. Independent replication — a second
   team auditing the artifact, or a second deployment measuring the
   pilot's numbers — is the real check and has not happened.
2. **Efficacy is unmeasured.** The largest open *question*, conditional
   on item 1's caveat being accepted. A monthly hand-audit against the
   day-0 baseline is the system's own prescribed check; the first is due
   ~2026-08-08 and will be recorded in a future revision of this
   document, not asserted here.
3. **The field window is short.** Every §2 number comes from roughly a
   24–48 hour window (day-0 2026-07-08, measured 2026-07-09). Language
   like "dominant failure mode" or "repeating pattern" describes what has
   been seen in that window, not a steady-state rate — treat every count
   in §2 as provisional until the pilot has run for months, not days.
4. **Single-regime evaluation.** One solo developer, one repository, six
   concurrent agent sessions on one machine. Multi-human, multi-machine
   concurrency is untested and is exactly the regime that would stress
   the confluence and `O_APPEND` assumptions hardest.
5. **Agent compliance is behavioral, not technical.** The entire layer is
   discovered through a few lines of instruction-file text; a runtime
   that never loads them bypasses everything. Held so far in the pilot —
   but the pilot's operator is also the layer's author, so discovery by
   unbriefed agents in unrelated repositories is untested.
6. **Timestamp forgery is accepted, not solved — but its worst
   composition is now detected.** An appender chooses its own `ts`; the
   line-prefix gate makes forged appends permanent and attributable in
   git history but does not prevent backdating. The composition with
   duplicate-id dedup — a backdated duplicate winning claim content
   under first-wins — is detected at commit since v0.6 (ADR-008; §1,
   "Fold semantics, precisely"): file order is append order, so a
   backdated duplicate id fails `validate`. The residual accepted risk
   is timestamp forgery on a fresh, non-duplicate id. Cryptographic
   prevention stays deferred behind a growth gate (signed records)
   rather than half-built.
7. **Vocabulary debt — named since v0.6.** "Diverged" conflated
   "reality changed" with "the measuring command's output format
   changed." ADR-012 names the second: `verdict <id> diverge
   --mechanical` records a recipe-change divergence as a subtype
   (status unchanged; queue and `truth stats` report the two rates
   separately). What remains open is whether authors and verifiers
   apply the distinction consistently — vocabulary shipped, calibration
   unmeasured.

---

## 9. Adopting this

The friction budget is stated as a design constraint, not a marketing
claim: one command to file a claim, four lines of instruction-file text
for an agent to discover the layer exists. In practice, three operating
conventions earned in the pilot are worth adopting alongside the code
itself — the first is mechanically enforced at intake since v0.6, the
other two remain discipline:

- **Never write a repo-wide clause backed by a package-scoped command.**
  Name the by-design survivors explicitly instead of relying on a
  quantifier the evidence command doesn't actually check. (Since v0.6
  intake refuses this shape outright unless `--scope-ok` states the
  justification on the record — ADR-007, §1 Intake gates.)
- **Commit the work, then file the completion claim** — not the reverse;
  a claim filed before its own shipping commit can be staled by that
  commit within seconds.
- **Pin evidence-command output that embeds counts** (`"0 failures across
  70 docs"` will mechanically diverge as the corpus grows even though the
  claimed fact stays true); prefer a stable sentinel like `... && echo
  CLEAN`.

Requirements: POSIX, git, Python 3; the `jsonschema` package if the
schema-drift detector should run armed rather than fail closed (block,
the safe default) instead of running unarmed and silently skipping.

---

## 10. Future work

- **The efficacy trial** — see §8 item 2 for the gap; the concrete design
  is: longitudinal false-VERIFIED rate, with and without the ledger,
  across repositories and agent runtimes.
- **A scoping-fault countermeasure beyond discipline — shipped (v0.6,
  ADR-007).** §2's dominant finding had only an operating convention
  (§9) as a defense; the intake heuristic this item proposed — flag
  universal quantifiers ("only", "no ... anywhere", "the repo") in
  claim text when the evidence command carries path or `--include`
  filters — is now the quantifier–scope gate (§1 Intake gates). What
  remains future work is measuring its false-positive rate and whether
  `--scope-ok` justifications rot into ritual.
- **Signed records** (§8 item 6, Appendix A INV-G) — binding `actor` and
  `ts` cryptographically would close what ADR-008's commit-time
  detection (v0.6) cannot: backdating on a fresh id, and any forgery in
  a history the local prefix gate never saw. The duplicate-id
  substitution gap itself is no longer undefended — it is detected at
  commit (§1 "Fold semantics, precisely"). Signing stays deferred
  behind a growth gate, per the original v0.4 audit's own trigger:
  build it when the first forged timestamp is found in the wild, not
  before.
- **Claim half-life measurement — shipped mechanically (v0.6, FS-1;
  §6.2).** `truth stats` computes per-tier half-life from
  invalidation-log data and intake suggests the observed median beside
  the author's TTL once ≥5 observations exist. Still future: enough
  field history for the suggestion to mean anything, and a calibration
  check against ground truth.
- **Generate the validate mirror from the schema — the corpus half
  shipped (v0.6, FS-2).** F1 and F8 are one defect class occurring
  twice: two hand-maintained copies of the record contract (stdlib
  mirror, JSON Schema) drifting apart. The conformance corpus was a
  sample, and samples miss; the second recurrence was the trigger, and
  FS-2 answered it with a constraint-enumerated mutant generator in
  `test-truth-core.py` — hundreds of generated near-valid records on
  which mirror and schema must agree, with a meta-canary count floor.
  The other half — a build step deriving the mirror from the schema —
  remains unbuilt, acceptable while the generated corpus holds the two
  in lockstep.
- **Formal verification of the fold.** The core is a pure function over a
  small event alphabet — a natural target for exhaustive model checking
  (TLA+/Alloy) of confluence and terminality, replacing the permutation
  sampling of §3 instrument 3 with proof.
- **Cross-language reimplementation as replication.** A port (e.g., Go)
  using the unchanged seeded-fault suite as its acceptance oracle would be
  an unusually clean independent replication of the behavioral contract —
  a direct answer to §8 item 1, which nothing else on this list actually
  resolves.
- **Attestation upgrade.** Session-manifest attestation — recording
  everything a claiming session executed, not just its final command — if
  recheck-only verification proves too narrow in practice.

---

## Appendix A. Invariant table (merged, v0.4 + proposed)

| ID | Property | Falsified by | Gate |
|----|----------|--------------|------|
| INV-A | Ledger is append-only: staged file is a line-prefix extension of committed file | One edit, deletion, or insertion committed | Prefix gate |
| INV-B | VERIFIED claims carry command, hash, anchor, paths-or-TTL | One bare VERIFIED accepted | Intake tests |
| INV-C | Evidence-path changes demote before re-trust | One stale claim rendered live | Seeded fault |
| INV-D | Recheck detects non-reproducing evidence | One hash mismatch scored agree | Seeded fault |
| INV-E | TTL'd claims expire | One claim outliving its TTL | Seeded fault |
| INV-F | History rewrites invalidate, with reason | One orphaned anchor still trusted | Seeded fault |
| INV-G | Retraction is terminal, on every path *tested* | One resurrected tombstone | Seeded fault (verdict path, append path); the backdated duplicate-id append that could substitute claim content under a retracted id is detected at commit since v0.6 (ADR-008, canary B-faults) — residual: fresh-id timestamp forgery, accepted per §8 item 6; see §1 "Fold semantics, precisely" |
| INV-H | Broken premises hold work | One issue ready on a stale premise | Seeded fault |
| INV-I | Fold is confluent: any event order, same state | Two orders, two statuses | Permutation property test |
| INV-J | Re-verification is durable across scans | One re-verified claim re-staled with no new changes | Seeded fault |
| INV-K | Retraction requires `TRUTH_HUMAN=1` **plus** an interactive typed-id confirmation or `TRUTH_HUMAN_ACK=<exact-id>` (ADR-011, v0.6) | One retraction accepted with the variable alone, headless | Seeded fault (H-faults) — still self-attested rather than identity-verified, but the one-export bypass is closed; see F4, §4 |
| INV-L | The drift detector is armed or the suite fails | One green run with the schema unchecked | Armed-detector test |
| INV-M | Every `evidence_path` on an accepted claim matches ≥1 tracked file at filing time, or is an explicit glob | One accepted claim whose tripwire can never fire | Seeded fault (`FAULT T`), shipped v0.5.4 |
| INV-N | Issue-fold premise protection (ADR-001) cannot be stripped by an appended duplicate `wk-` id | One HELD issue silently flipped to READY | Seeded fault (FAULT R9) — fixed at the fold level (ADR-006): duplicate issue ids are first-wins, identical to INV-G's claims-side mechanism; the backdated-duplicate composition is detected at commit since v0.6 (ADR-008), with INV-G's same residual — fresh-id forgery while `ts`/`actor` remain unsigned (§8 item 6) |

## Appendix B. Reproduction

All findings and repairs are demonstrated by scripts driving the actual
CLI in fresh sandbox repositories: `scripts/truth` (CLI, pure core over
imperative shell), `scripts/check-truth.sh` (prefix-based commit gate),
`scripts/truth-canary.sh` (the seeded-fault suite — it prints its own
count rather than having it restated here; grown from 19 at v0.4 as the
pilot's satellites, the work kernel, the impact verb, and the v0.6
hardening batch merged upstream into this same template — see §2),
`scripts/test-truth-core.py`, `scripts/test-truth-v04.py`, and
`.truth/schema/claims.schema.json`. Field numbers in §2 are read
directly from `git log -p .truth/claims.jsonl` in the pilot repository —
the append-only property doing double duty as a research instrument.

## References

*(Indicative; verify before any external submission.)*

- Lamport, L., Shostak, R., & Pease, M. (1982). The Byzantine Generals
  Problem. *ACM TOPLAS*, 4(3).
- Castro, M., & Liskov, B. (1999). Practical Byzantine Fault Tolerance.
  *OSDI '99*.
- Popper, K. (1959). *The Logic of Scientific Discovery.*
- Lehman, M. M. (1980). Programs, Life Cycles, and Laws of Software
  Evolution. *Proceedings of the IEEE*, 68(9).
- Claessen, K., & Hughes, J. (2000). QuickCheck: A Lightweight Tool for
  Random Testing of Haskell Programs. *ICFP '00*.
- Shapiro, M., Preguiça, N., Baquero, C., & Zawirski, M. (2011).
  Conflict-free Replicated Data Types. *SSS 2011*.
