# The Truth Ledger: A Claim-Invalidation Layer for Agentic Software Development

**Status:** v2. Merges the frozen v0.4 audit with pilot field evidence through
2026-07-09 into one living document, superseding the earlier split between
`truth-ledger-paper.md` (audit, frozen at v0.4) and
`truth-ledger-field-notes.md` (deployment, formerly living) — both now
retired to `docs/archive/`. Artifact version audited:
v0.4. Artifact version deployed in the pilot: v0.5.3 at day-0 (the
template has since moved well beyond that — it states its own version in
`scripts/truth`, and the ADRs below note where each mechanism landed. The
v0.6 solo-regime hardening batch (ADR-007 through ADR-012 plus FS-1/FS-2),
ADR-013's premise supersede, and the subsequent batch-2 spec-precision
ADRs (014 onward) convert several of this paper's "accepted" and "future
work" items below into shipped mechanisms, noted inline where they land;
the pilot first synced past day-0 to v0.6.4 on 2026-07-13, §2). Pilot: one multi-component
kitchen-manufacturing monorepo (domain core, catalog service, ERP, CAM, two
adapters), one solo developer, LLM agent sessions doing the implementation
work, day-0 2026-07-08. All quantitative claims in §2 are self-reported by
that same developer, who is also this paper's sole author and auditor —
see §8 item 1.

**How to read this paper.** Section headers are ordered by evidence class,
not narrative convention: mechanism and measurement first, interpretation
last. §6.2 and §6.3 are explicitly optional — skip them if you want the
artifact, not the theory. §6.1 isn't: it's the analysis §2 promises and §10 builds on.
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

**Derivation.** The fold below covers claim status; the work kernel adds a
fold for issue status (`fold_issues`; the state machine ADR-002 described in
prose is reproduced in ADR-028). That machine has two layers: **intake is
strict** — a fixed transition table (`open→claimed→closed`, `reopened` from
`closed`, `cancelled` from any non-terminal state) refuses nonsense
transitions loudly — while **the fold is permissive except that `cancelled`
is terminal**: later events on a cancelled issue are ignored, exactly as the
claim fold ignores events after `retracted`. Permissiveness is deliberate,
for confluence across merged branches; intake is the gate. An `issue_event`
must sort after its issue record, or the fold would drop it as a forward
reference — enforced at intake and by `order_check` (ADR-028). Status is never
stored; a pure function replays the log:

```
no events              → unverified
verdict agree          → live
verdict diverge        → diverged        (queued for attention)
verdict cannot_verify   → cannot_verify   (queued if P0)
verdict retracted       → retracted       (terminal — later events ignored)
invalidation            → stale           (queued if P0/P1)
```

`invalidation → stale` is the *only* path to `stale`, and it is complete:
even TTL expiry reaches `stale` only through an invalidation **record**.
TTL is not folded from the clock — the invalidation scan counts elapsed
time from the claim's own `ts` (not the anchor, not the verdict that made
it live) and, when *strictly more than* `ttl_days` have passed
(`now - ts > ttl_days`; at exactly the boundary it has not yet expired),
writes an invalidation naming the claim. A TTL'd claim the scan has not
yet visited is not stale, however old the fact. This keeps the fold a
pure, confluent function of the log while still letting time demote a
claim — the clock's effect is frozen into a record, never recomputed on
read (ADR-019).

A claim is born `unverified` regardless of its `evidence_class` — filing a
VERIFIED claim runs and hashes the evidence command at intake, but that
double-run is a gate, not a verdict; only an explicit `agree` event (via
`truth dispatch`, §1 Verification below) advances it to `live`. This is
deliberate: evidence attached at filing and evidence independently
confirmed are kept as two distinct events in the log, never conflated.

The negative states are the mirror image of that terminality: `diverged`,
`cannot_verify`, and `stale` are all **recoverable** — a later `agree`
(the higher-key event) returns the claim to `live`, and a `stale` claim
re-anchors as it does so. Status is one total function of the log
(§6.3, ADR-020): fold in `(ts, id, canon)` order and take the
last-writer-wins effect of each verdict/invalidation, with `retracted`
alone absorbing. Only a human retraction is a dead end; a machine's "I
could not check this" or "the evidence moved" is an invitation to check
again, not a verdict of falsehood.

Terminality of `retracted` is the strongest promise the system makes: a
human decision to kill a claim cannot be undone by any later event —
**on the paths this design defends against**, precisely stated below.
The promise has two layers, and both are now defended (ADR-017, after
an independent review found the second undefended — C3). At the *status*
layer, a retracted claim stays `retracted` in the fold under any event.
At the *readiness* layer, the block a retracted premise imposes (ADR-001:
HELD, unconditional) can be released only by the same human authority
that imposed the retraction: superseding a retracted premise (ADR-013)
requires the ADR-011 human gate, exactly as retraction does. The
mechanical dead states a premise may also be superseded out of —
`stale`, `diverged`, `cannot_verify`, `missing` — stay ungated, because
no human decided them; only `retracted` carries a human veto whose
release needs matching authority. Before ADR-017 the readiness layer was
open: any actor could redirect a retracted premise via a normal CLI verb
and release the blocked work, no forgery needed — the status promise
held while the operational one was silently spent.

**Fold semantics, precisely.** The fold replays every event — claim,
verdict, invalidation, premise — in the canonical total order
`(timestamp, id, canonical-serialization)`, ascending, regardless of
file position (this is what makes replay order-independent; §4, F3). The
third key matters and was added late (ADR-016, v0.9.1): `(timestamp, id)`
alone is **not** total — a duplicate id carrying a *copied*, byte-equal
`ts` ties both components, at which point a stable sort silently decides
the winner by file position, the one thing the fold must ignore. The
canonical record serialization is a deterministic function of content,
so distinct records never tie and every event order — including the two
a union merge can produce — folds identically. Within that order, the
*first* claim record to establish a given id fixes that claim's text and
evidence capsule; any later claim record bearing the same id is ignored
for content (§4, F6) — its append is permitted (the log is append-only,
not edit-only) but has no effect on derived state. Composing first-wins
with the accepted timestamp-forgery threat (§8 item 6) once yielded two
substitution gaps, both now closed by detection at commit: an appender
who **backdates** a duplicate-id record sorts it *before* the genuine one
(ADR-008, detected since v0.6 — within one repository's history file
order is append order, the INV-A guarantee, so `truth validate` fails any
duplicate id with a strictly earlier `ts`); and an appender who **copies
the ts byte-for-byte** ties the order and lets a union merge seat the
pair either way (ADR-016, detected since v0.9.1 — `validate` fails any
duplicate id with an *equal* `ts` and non-identical content). Identical
duplicated lines (git's union-merge shape — same id, same ts, same
content) still pass, the one legitimate equal-ts case. The residual that
remains accepted, not detected, is timestamp forgery on a *fresh*
(non-duplicate) id — §8 item 6.

**Intake gates.** `truth claim` refuses, before anything is written:
empty claim text (v0.5.5 — an assertion with no sentence cannot be
verified, diverged from, or cited); near-duplicates of active claims by
**Jaccard** token overlap ≥ 0.6 against claim text (ADR-018 pins the
conformance surface, v0.4: the metric is `|A∩B|/|A∪B|` — symmetric, so a
strict elaboration is *not* a duplicate — not the overlap coefficient a
vague "overlap" reading invites; tokens are the *set* of maximal
`[a-z0-9]+` runs of the lowercased text; "active" is exactly the
`{live, unverified}` statuses, so the other five are dead-for-intake)
(overridable, and always allowed for corrections of dead claims);
a universally quantified claim text over a scoped evidence command
(ADR-007, v0.6 — the §2 dominant-failure countermeasure §10 once listed
as unbuilt; refused unless `--scope-ok "<one sentence>"` states why the
scope covers the quantifier, stored as an attackable `scope_basis`);
*statically* dead-tripwire evidence paths (INV-M, v0.5.4 — a
whitespace-containing entry with no comma, or a **literal** path matching
zero tracked files, or a **glob** over a statically-unreachable namespace
(`.git/*`, an absolute or trailing-slash pattern, a `.`/`..`/empty
component — ADR-024); a glob over a *reachable* namespace is exempt because
it is a dormant watch, not dead — it fires when the namespace fills
(ADR-023); applies to *any* evidence class carrying paths, and has no
override); VERIFIED claims with no evidence command, with
neither paths nor TTL, or filed in a repository with no commits to anchor
to (these three checks are VERIFIED-only; UNVERIFIED and INFERRED claims
may omit evidence, paths, and TTL); evidence commands failing the
read-only safety screen against the committed `.truth/evidence-allow`
allowlist (ADR-009, v0.6 — the command re-executes later inside verifier
sessions; `--evidence-unsafe-ok` files with `screened=false` and recheck
then refuses to ever execute it. The screen tokenizes with `shlex` but
the command executes under `/bin/sh`; ADR-021 (v0.9.6, H4) closed a real
bypass where a newline — word-whitespace to `shlex`, a statement
separator to `/bin/sh` — smuggled a second command past the screen into a
verifier's recheck, by refusing control characters so the screen
tokenizes like its executor. The same ADR records that the per-program
argument blocklist is defense-in-depth, not the boundary: it cannot bound
a VCS or interpreter, so `git`/`sed`/`awk`/test-runners are excluded from
the allowlist by design, not merely flag-screened); evidence commands whose two intake
runs hash differently (nondeterministic, overridable); and INFERRED
claims with no `--basis`. The list is stated here in refusal
order, which is observable when one claim trips several gates — but the
safety screen is not a flat peer of the others: it is a **gate on
execution**. A command that fails the screen is not run at all, so it never
reaches the determinism double-run (it reports the screen refusal, never the
determinism one) — unless `--evidence-unsafe-ok` bypasses the whole screen,
which then runs the command twice, applies the determinism check, and stores
it `screened: false` for `recheck` to refuse (ADR-029).

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
filing friction, with a named fallback if warning fatigue appears. Since
v0.6.4 (ADR-013) a *genuinely dead* premise — the fact was wrong and its
correction lives under a new id — can be redirected by an auditable
supersede event; the redirect is refused while the old premise is live
or unverified (the states needing no rescue), and the replacement is
judged by this same matrix, so it
re-targets protection rather than removing it.

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
| Seeded faults, the pilot's downstream canary | grew 19 → 42 → 45 → 48 → 49 in step with the pre-v0.5.4 merges, matching the template through v0.5.3 (F7/ADR-006 synced 2026-07-09); diverged from the template until the pilot re-synced via `copier update` — to v0.6.2 (released tag) and then to v0.6.4 on 2026-07-13, zero-conflict, all suites green post-update (Appendix B) |

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

**A second deployment exists (2026-07-12).** A distinct agent in a
distinct repository (`temporal-go-agent-sdk`) reproduced the failure
taxonomy above: one genuine divergence — again the quantifier/scope
shape — one mechanical divergence (ADR-012's class), zero fabrications.
Same operator, so §8 item 1 extends to it unchanged: corroboration,
not independent replication. Its findings and their adopted remedies
are in `docs/field-notes-sdk-session.md` (one produced ADR-013).

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
| F3 | Fold not confluent under union merge — `{agree, diverge}` folds to `live` or `diverged` depending on merge direction | Medium | Exhaustive permutation check | No | Fold sorts events into total order `(timestamp, id, canon)` before replay (ADR-016 made the order total) — the standard CRDT total-order replay (Shapiro et al., 2011a). This cell previously labeled the move "last-writer-wins," which is imprecise: composed with F6's fix, the fold applies three per-field merge disciplines, only one of which is LWW — see §6.3 and ADR-020 for the single total status function. Confluence holds on the verdict path too (distinct verdict ids, total order), so backdating a verdict is not a C1 analogue — it only lowers the record's key and trips an ADR-008 warning (H3, ADR-020) |
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
the **log** and touches no I/O — even TTL expiry, the one demotion that
needs a wall-clock, enters only at the *scan* boundary, which reads the
clock and writes an invalidation record; the fold itself never reads a
clock (ADR-019). That log-purity is what made unit-level attacks on the
core cheap in the first place.

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
than the code. Four mechanisms fell out of this observation — the first
three grown in the pilot and shipped upstream in the project template,
the fourth grown in the template's own meta-repo (a third deployment
site, 2026-07-12):

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
- **doc-coverage claims** — a VERIFIED claim binding a document's
  load-bearing coverage to the code surface it describes, by watching
  *both* (the doc's path and the code's) with a sentinel evidence
  recipe. Code growth then mechanically stales the claim, converting
  "does the doc still cover this?" from a hoped-for review into a queue
  item. Installed in the meta-repo after a manual review found its
  instruction file documenting only half the CLI (the facts verbs, not
  the work kernel — the exact desync class spec-health cannot see,
  since it guards cited ids, not coverage). Across the four template
  releases that followed, the tripwires forced doc re-review each time;
  the residual, learned the same week: recipes narrower than their
  sentences survive intake (one was retracted for it), and a watch on a
  tracked symlink can never fire — git tracks the immutable link, not its
  target (Appendix A, INV-M). A later review (H5) tested the neighbouring
  worry — that an explicit glob matching nothing is a second dead tripwire.
  It split in two. A glob over a *reachable* namespace is *dormant*, not
  dead: it fires the moment its namespace is populated, because the
  invalidator re-evaluates the pattern against every scan's diff rather
  than freezing its matches at filing time (ADR-023). But an adversarial
  verifier then found the other half — a glob over an *unreachable*
  namespace (`.git/*`, an absolute or trailing-slash pattern, a
  `.`/`..`/empty component) is exempt yet can never fire; INV-M now refuses
  those at intake, a *statically decidable* class (ADR-024). What is left
  is the tracked symlink, the one residual whose deadness is *not*
  statically decidable — it needs link resolution — so it stays guidance.
  INV-M's gate decides *static* deadness, not liveness.

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
§6.3, added 2026-07-12, records the inverse of §6.1's direction:
vocabulary the design *converged on* without having been motivated by
it — which, for a single-author artifact (§8 item 1), is the more
evidentially valuable kind.

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

### 6.3 Architectural lineage, corrected — vocabulary the design converged on

Added 2026-07-12. The v0.4–v0.6 mechanisms were designed against local
evidence (§2, §4), not from the literature; this section names, after
the fact, the classical constructions several of them turn out to be
instances of — each with the correction stating where the artifact
deliberately stops short of its ancestor. The point is not pedigree.
Under this paper's own worst limit (§8 item 1, single-observer), a
design that independently converges on results derived decades earlier
by others has acquired the nearest available substitute for external
review: the original authors' analysis applies, and their known failure
modes become checkable predictions here. Nothing below changes how
anything operates.

**The fold, as CRDT constructions — the precision F3's row lacked.**
§4's F3 cell originally called the confluent fold "the standard CRDT
last-writer-wins move." Imprecise, corrected there and stated fully
here: the ledger is a grow-only set of events (a G-Set), and the fold
applies three *distinct* per-field merge disciplines over it — claim
**content** is first-writer-wins, a write-once register (F6's fix);
claim **status** is last-writer-wins in `(ts, id, canon)` order (F3's
fix, made a total order by ADR-016); and `retracted` is **terminal**, the
two-phase-set tombstone rule under which a removed element never re-enters
(Shapiro et al., 2011a; the 2P-Set construction itself is cataloged in the
companion report, Shapiro et al., 2011b). These compose into **one total
status function** (ADR-020), not three competing rules: fold every event
in `(ts, id, canon)` order; each verdict/invalidation sets the status
(`agree→live`, `diverge→diverged`, `cannot_verify→cannot_verify`,
`invalidation→stale`, `retracted→retracted`) last-writer-wins, EXCEPT that
once the folded status is `retracted` every later setter is ignored
(absorbing, tested on the folded status, not on `ts`). So `cannot_verify`,
`diverged`, and `stale` are **recoverable** — a later `agree` returns the
claim to `live` (a `stale` claim re-anchors) — while `retracted` is the
**sole terminal** verdict (intake also refuses any verdict on a retracted
claim). The worked worry "cannot_verify@ts=5 then a backdated agree@ts=3"
folds to `cannot_verify` by this function (5 is the higher key). Because
two verdicts carry distinct ids and the order is total, verdict ordering
is **confluent** — reordering ledger lines never changes a status, so
this is *not* a C1-style analogue: backdating only lowers a record's key
(strictly dominated by filing at `ts=now`) and merely trips the ADR-008
clock-regression warning; the sole residual is the accepted §8 item 6
forgery, needing no new gate (ADR-020). Each discipline is standard; what is local to
this design is only their per-field composition and the audited record
of why each was chosen (F3, F6, G12). Correction: CRDT theory buys
convergence across mutually unavailable *replicas*; this design spends
it on something narrower — branches of one repository, union-merged —
and §8 item 4's multi-machine caveat stands untouched.

**Local-first software.** No server, data in user-owned plain files,
CRDT-grade convergence, synchronization delegated to a transport the
user already trusts (git): the artifact is a near-textbook instance of
the local-first program (Kleppmann, Wiggins, van Hardenberg &
McGranaghan, 2019), applied to knowledge about code rather than to
documents. The framing also locates the honest boundary: local-first's
headline ideal is real-time multi-device *collaboration*, and this
design claims exactly none of it — §8 item 4 names multi-human,
multi-machine as untested, which in local-first vocabulary reads as
"the sync layer exists (git), the collaboration layer was never built."

**Optimistic concurrency control.** ADR-008's stance — never block an
append, validate coherence at commit, detect conflicts after the fact —
is the optimistic method (Kung & Robinson, 1981) transplanted from
transactions to an epistemic log: the commit gate is OCC's validation
phase with `(ts, id)` order in the role of serializability. Correction:
OCC's losing transaction is aborted and *retried by the system*; here
nothing retries — a validation failure feeds a human decision (the
refusal, the queue), because the conflicting party may be a
prompt-injected agent whose "retry" is exactly what must not happen
automatically.

**The confused deputy.** The v0.6 threat model's adversary (a) — the
compliant-but-confused agent that completes a bypass ritual an error
message taught it — is Hardy's confused deputy (1988), stated
twenty-five years before LLM agents gave it a new body. ADR-011's
remedy is the capability-theoretic one: `TRUTH_HUMAN_ACK=<exact-id>`
makes the authorization *designate* the specific object it authorizes,
so a lingering ambient variable (Hardy's ambient authority) can no
longer be spent on an arbitrary later target. Correction: there are no
actual capabilities here — identity remains self-attested (F4's class,
§8 item 5); what is closed is only the ambient-authority channel an
error message can teach.

**The borrowed event loop.** Stated nowhere above and worth one honest
paragraph: the system owns no process. All reactivity is borrowed from
host lifecycles — git's commit and merge hooks supply the transactional
moments, the agent harness's session-start and edit-intent hooks supply
the attention moments (ADR-005, FS-4). This buys event-driven behavior
with zero owned uptime, at the price that liveness is only as strong as
the host's hook wiring — which is precisely why `doctor` checks the
installation rather than the scripts (G4) and why §8 item 5 exists.
`doctor` makes that check decidable: it exits 1 unless, for each gate, an
active `check-truth`/`invalidate-scan` hook OR a CI config naming it
exists (ADR-025) — so a clean run is the proof the one MUST holds. No
canonical citation is claimed; the nearest kin (interception middleware,
aspect weaving) share the mechanism but not the motive, and this stays
a named observation rather than a borrowed authority.

**Older lineage, one breath each.** Derive-don't-store status (§1) is
event sourcing (Fowler, 2005) and the append-only half of the
immutability argument (Helland, 2015) — Appendix B's note that the
append-only file "does double duty as a research instrument" is
Helland's thesis in miniature. `ttl_days` is the DNS resolver's decay
model for facts the authoritative source cannot push to you
(Mockapetris, 1987). And the pipeline journal → derived ledger → trial
balance (`validate`) is double-entry bookkeeping's, five centuries on —
offered strictly as metaphor in §6.2's sense, since no double entry
exists here.

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
   unbriefed agents in unrelated repositories is untested. The same
   host-dependence has a sharper edge on the *commit gate*: INV-A
   (append-only), INV-B, INV-G and INV-N and the ADR-008/016 order
   detections are all enforced by `check-truth` running at commit, which
   runs only where a hook or CI is installed — where neither is, those
   invariants are silently unenforced (a rewrite of a committed line
   commits freely). This is the README's one MUST, and `doctor` is what
   makes it decidable: it exits 1 unless, for each gate, an active hook OR
   a CI config naming the gate script exists (ADR-025). The residual is
   that `doctor` is itself opt-in and its CI arm is self-certified — a
   commit-time refusal is deferred behind the same growth gate as signed
   records (item 6).
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
for an agent to discover the layer exists. In practice, five operating
conventions earned in the field are worth adopting alongside the code
itself — three from the pilot (the first mechanically enforced at
intake since v0.6, the next two discipline) and two from a second
deployment (2026-07-12, `docs/field-notes-sdk-session.md`; same
operator, so §8 item 1's caveat extends to them):

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
- **Scope `--paths` to the narrowest set that actually backs the claim**
  — not only for correctness but for *blast radius*: every claim
  anchored to a path re-stales when any commit touches it, so a broadly
  scoped watch drags unrelated-but-true claims into the verification
  queue on every edit to a hot file (second deployment, 2026-07-12: one
  commit to a shared file re-staled 8 claims, 6 of them still true).
- **Reserve an ADR namespace before writing your own ADRs.** The
  template owns `docs/adr/NNN` and extends that series on `copier
  update`; number your project's ADRs in a disjoint space (a separate
  directory, or a distinct prefix such as `P###`) from day one. Ledger
  claims cite ADR numbers immutably, so a collision discovered after
  the fact cannot be renumbered away — only namespaced going forward
  (second deployment hit exactly this).

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
  before. When that gate trips, the classical signature-free
  alternative should be evaluated first: hash-linking each record to
  its predecessor (Haber & Stornetta, 1991) binds order and content
  with no key management at all — a better fit for a regime that has
  no identity infrastructure by design (§6.3, confused deputy
  correction) — at the cost that it authenticates *sequence*, not
  *authorship*, which may be exactly enough here.
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

## Appendix A. Invariant table (v0.4 core through v0.9.1)

Every shipped property that a seeded fault gates belongs here — a row is
added when the property ships, not later. INV-O/P/Q were backfilled
2026-07-18 after an independent review found ADR-010/013/014 shipping
with canary faults but no table row; the table is itself an admitted
artifact class that needs its own freshness discipline (§5), and a lag
between "fault lands" and "row lands" is exactly the decay §5 predicts.

| ID | Property | Falsified by | Gate |
|----|----------|--------------|------|
| INV-A | Ledger is append-only: staged file is a line-prefix extension of committed file | One edit, deletion, or insertion committed | Prefix gate — **conditional on the commit gate actually running** (an installed `check-truth` hook or a CI config naming it). `doctor` decides this and exits 1 without it (ADR-025); where neither exists the gate never runs and this invariant is silently unenforced — a rewrite of a committed line commits freely (§8 item 5). This conditionality applies to every "commit gate" / "detected at commit" row below (INV-B, INV-G, INV-N, and the ADR-008/016 order detections) |
| INV-B | VERIFIED claims carry command, hash, anchor, paths-or-TTL | One bare VERIFIED accepted | Intake tests |
| INV-C | Evidence-path changes demote before re-trust | One stale claim rendered live | Seeded fault |
| INV-D | Recheck detects non-reproducing evidence | One hash mismatch scored agree | Seeded fault |
| INV-E | TTL'd claims expire: the scan writes an invalidation when `now - ts > ttl_days` (counted from the claim `ts`, strict boundary), and only that record demotes the claim — the fold never expires from the clock (ADR-019) | One claim outliving its TTL; or a claim expired at fold time with no invalidation record | Seeded fault (FAULT D, incl. the fold-clock-free arm); core boundary + fold-purity tests |
| INV-F | History rewrites invalidate, with reason | One orphaned anchor still trusted | Seeded fault |
| INV-G | Retraction is terminal at both layers: the claim's *status* stays `retracted` under any event, and the readiness *block* it imposes is released only by matching human authority | One resurrected tombstone; or a retracted premise's HELD block released without the human gate (C3) | Seeded fault (verdict path, append path); duplicate-id content substitution under a retracted id is detected at commit — backdated (strictly-earlier `ts`) since v0.6 (ADR-008), and copied-`ts` (equal, non-identical content) since v0.9.1 (ADR-016, canary B5); the readiness-layer supersede release is human-gated since v0.9.3 (ADR-017, canary R11) — residual: fresh-id timestamp forgery, accepted per §8 item 6; see §1 "Fold semantics, precisely". The commit-time detections here are **conditional on the commit gate running** (INV-A / ADR-025); the human-gated readiness release is not |
| INV-H | Broken premises hold work: a premise that is `stale`, `diverged`, `retracted`, or missing HOLDs its issue (the full ADR-001 blocking set, not just `stale`) | One issue ready on a premise in any of those four states | Seeded fault (FAULT J covers `stale`; the ADR-001 matrix — reused verbatim by the work kernel, ADR-002 — blocks all four identically). The `cannot_verify` P0-only rule and the `unverified` warn-pass are the matrix's two non-blocking cells |
| INV-I | Fold is confluent: any event order, same state | Two orders, two statuses (or two contents) | Permutation property test. The order key is `(ts, id, canonical-serialization)`: the third key is load-bearing (ADR-016, v0.9.1) — `(ts, id)` alone is not total, so a duplicate id with a copied equal `ts` folded to different *content* by file order until the content-derived tie-break closed it (canary B6; core `test_duplicate_id_equal_ts_folds_to_one_content`) |
| INV-J | Re-verification is durable across scans | One re-verified claim re-staled with no new changes | Seeded fault |
| INV-K | Retraction requires `TRUTH_HUMAN=1` **plus** an interactive typed-id confirmation or `TRUTH_HUMAN_ACK=<exact-id>` (ADR-011, v0.6) | One retraction accepted with the variable alone, headless | Seeded fault (H-faults) — still self-attested rather than identity-verified, but the one-export bypass is closed; see F4, §4 |
| INV-L | The drift detector is armed or the suite fails | One green run with the schema unchecked | Armed-detector test |
| INV-M | No `evidence_path` on an accepted claim is *statically* dead at filing time: every **literal** matches ≥1 tracked file, no entry is a whitespace-no-comma literal, and no **glob** is statically unreachable. (A static-dead-tripwire gate, **not** a liveness guarantee — one undecidable residual remains.) | One accepted claim carrying a *statically* dead tripwire (a comma-typo literal, a literal matching zero tracked files, or an unreachable glob) | Seeded fault (`FAULT T`), shipped v0.5.4; scope sharpened ADR-023 and the glob case closed ADR-024 (v0.9.8). **(1) A glob over a *reachable* namespace is dormant, not dead** — an explicit glob (`*`/`?`/`**`) matching nothing yet is exempt because it fires when the namespace fills: a claim on `src/ghost/*.py` goes stale the moment a tracked `src/ghost/*.py` file is touched (sandbox-verified). This refutes the universal reading that "an empty glob can never fire." **(2) A glob over an *unreachable* namespace is dead, and now refused (ADR-024)** — an adversarial verifier found that `.git/*`, `/etc/*.conf`, `zone/*/`, `../*.txt`, `dbl//*.txt` are exempt (they contain `*`) yet match no repo-relative, normalized `git diff` path, so they can never fire; INV-M now refuses a glob whose leading component is `.git` or that has an absolute/trailing-slash/`.`/`..`/empty component. This is *sound* (no false refusals: `.git*`, `.github/**` still pass) but *not complete*. **(3) The tracked symlink literal is the undecidable residual** (found by inspection, 2026-07-13): it passes the literal check but can never fire — git tracks the immutable link object (mode `120000`), not the target — and unlike the unreachable glob its deadness needs link resolution, so it stays guidance ("watch real, reachable paths"), not a gate |
| INV-N | Issue-fold premise protection (ADR-001) cannot be stripped by an appended duplicate `wk-` id | One HELD issue silently flipped to READY | Seeded fault (FAULT R9) — fixed at the fold level (ADR-006): duplicate issue ids are first-wins, identical to INV-G's claims-side mechanism; the backdated- and copied-`ts` duplicate compositions are detected at commit (ADR-008 v0.6, ADR-016 v0.9.1 — the equal-ts gate and total order apply to every kind, `wk-` included), with INV-G's same residual — fresh-id forgery while `ts`/`actor` remain unsigned (§8 item 6). Like INV-G, the commit-time detection is **conditional on the commit gate running** (INV-A / ADR-025) |
| INV-O | A verifier cannot `agree` with a claim from that claim's own authoring session; a `diverge` from the own session IS allowed (self-incrimination) (ADR-010, v0.6) | One same-session `agree` accepted, or one same-session `diverge` refused | Seeded fault (FAULTS V1/V2/V3). Self-attested session identity (`TRUTH_SESSION`), same class as F4/INV-K — the bypass is one visible env export, not an identity check |
| INV-P | A supersede redirect re-targets premise validity, never bypasses it: the replacement is judged by the same ADR-001 matrix, the redirect is refused while the old premise still passes `ready`, and superseding a `retracted` premise requires the ADR-011 human gate (ADR-017 — the mechanical dead states stay ungated) | One issue made READY by redirecting a live/unverified premise; a retracted premise redirected without human authority (C3); or a redirect resolving non-deterministically | Seeded fault (FAULT R10, R11); cycle resolution pinned by core tests (ADR-013 amended 2026-07-18, first-repeated-value rule) |
| INV-Q | An acceptance oracle gates issue close: a non-zero exit refuses `done`, and an unscreened oracle is refused execution unless `--accept-unsafe-ok` stamps it visibly | One issue closed over a failing oracle, or an unscreened oracle executed silently | Seeded fault (FAULTS AC1–AC8, ADR-014, v0.7); `accept.executed=true` requires `returncode 0` in schema and mirror |

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

*(Annotated. Entries 2–19 were verified against publisher records on
2026-07-19 — volume/issue/pages, DOIs, and open-access links checked at
that date; re-verify before any external submission. Entries marked
**[proposed]** are candidate citations not yet load-bearing in the body
text. The → line states what each work is cited for.)*

### Epistemic frame

**1. Popper, K. (1959). *The Logic of Scientific Discovery.***
→ §7's framing: the paper states its own claims and the observations
that would falsify them. *(Retained from the prior list; not part of
the 2026-07-19 verification batch.)*

### Derived belief status, justification tracking, and trust

**2. [proposed] Doyle, J. (1979). A Truth Maintenance System.
*Artificial Intelligence*, 12(3), 231–272.**
→ Status is subordinate to justifications and repaired whenever they
change. Note: Doyle's TMS *stores* in/out labels and incrementally
repairs them; the artifact is stricter — it re-derives status from the
log on every read. Cite for the principle, not the mechanism.
- DOI: https://doi.org/10.1016/0004-3702(79)90008-0
- OA: https://dspace.mit.edu/handle/1721.1/5733 — MIT AI Memo 521
  (June 1979) version; PDF is a scan with no text layer:
  https://dspace.mit.edu/bitstream/handle/1721.1/5733/AIM-521.pdf

**3. Lehman, M. M. (1980). Programs, Life Cycles, and Laws of Software
Evolution. *Proceedings of the IEEE*, 68(9), 1060–1076.**
→ Cited as **analogy, not evidence**: Laws II/VII concern E-type
*programs* (complexity grows, quality declines, unless explicit effort
is spent). §5 transfers the shape of that claim to restated facts; the
paper itself says nothing about recorded facts.
- DOI: https://doi.org/10.1109/PROC.1980.11805
- OA (course mirror, UT Austin; no author/institutional copy exists):
  https://users.ece.utexas.edu/~perry/education/SE-Intro/lehman.pdf

**4. Kung, H. T., & Robinson, J. T. (1981). On Optimistic Methods for
Concurrency Control. *ACM Transactions on Database Systems*, 6(2),
213–226.**
→ ADR-008's never-block-append, validate-at-commit stance. (Exact fit:
unrestricted work phase, validation at commit, abort on conflict.)
- DOI: https://doi.org/10.1145/319566.319567
- OA (Kung's Harvard page):
  https://www.eecs.harvard.edu/~htk/publication/1981-tods-kung-robinson.pdf

**5. Lamport, L., Shostak, R., & Pease, M. (1982). The Byzantine
Generals Problem. *ACM TOPLAS*, 4(3), 382–401.**
→ §6.1's design stance — specifically via the **signed-messages**
result: unforgeable messages turn trust from an assumption into a
checkable property. (The oral-messages 3m+1 bound is not the part §6.1
uses.) Also supplies the arbitrary-failure model for §6.1's taxonomy.
- DOI: https://doi.org/10.1145/357172.357176
- OA (Lamport's page): https://lamport.azurewebsites.net/pubs/byz.pdf

**6. [proposed] de Kleer, J. (1986). An Assumption-based TMS.
*Artificial Intelligence*, 28(2), 127–162.**
→ Companion to Doyle if the TMS lineage is taken seriously — with the
caveat that the ATMS is a different machine: it labels each datum with
minimal assumption sets and maintains all consistent contexts at once,
rather than one current belief state.
- DOI: https://doi.org/10.1016/0004-3702(86)90080-9
- OA (author's site):
  https://dekleer.org/Publications/An%20Assumption-Based%20TMS.pdf

**7. Mockapetris, P. (1987). Domain Names — Concepts and Facilities.
RFC 1034 (STD 13), IETF, November 1987.**
→ `ttl_days`: decay model for facts the source cannot push to you.
(Exact fit: DNS caching TTLs exist precisely because authoritative
servers cannot invalidate resolver caches.)
- DOI: https://doi.org/10.17487/RFC1034
- Canonical/OA: https://www.rfc-editor.org/rfc/rfc1034

**8. Hardy, N. (1988). The Confused Deputy (or why capabilities might
have been invented). *ACM SIGOPS Operating Systems Review*, 22(4),
36–38.**
→ ADR-011's designated-object authorization
(`TRUTH_HUMAN_ACK=<exact-id>`): binding the ack to a specific id
removes ambient authority. Residual: an env var is designation without
unforgeability — it prevents confusion, not forgery.
- DOI: https://doi.org/10.1145/54289.871709
- OA (author's site; **HTTP only** — the HTTPS vhost 404s on this
  path): http://cap-lore.com/CapTheory/ConfusedDeputy.html

**9. Haber, S., & Stornetta, W. S. (1991). How to Time-Stamp a Digital
Document. *Journal of Cryptology*, 3(2), 99–111.**
→ §10's hash-linking alternative for the timestamp-forgery residual.
Note: their linking scheme still has a signing timestamp service — the
hash chain *reduces trust in* the signer rather than eliminating
signatures; the fully signature-free reading is this artifact's design
choice, closest to their distributed-trust variant.
- DOI: https://doi.org/10.1007/BF00196791 (journal version; distinct
  from the CRYPTO '90 proceedings version, 10.1007/3-540-38424-3_32)
- OA (publisher-served, free):
  https://link.springer.com/content/pdf/10.1007/bf00196791.pdf

**10. Castro, M., & Liskov, B. (1999). Practical Byzantine Fault
Tolerance. *Proc. 3rd USENIX Symp. on Operating Systems Design and
Implementation (OSDI '99)*, 173–186.**
→ *Moved here from "Verification, testing, and oracles" (it is a
replication protocol, not a testing method).* Cited alongside #5 for
the **practicality** of tolerating arbitrary faults (3f+1 replicas,
asynchronous networks, low overhead) — not for a failure taxonomy,
which #5 already carries.
- No DOI (USENIX proceedings). Landing:
  https://www.usenix.org/conference/osdi-99/practical-byzantine-fault-tolerance
- OA (publisher full text):
  https://www.usenix.org/publications/library/proceedings/osdi99/full_papers/castro/castro_html/castro.html
- Canonical PDF (MIT PMG; host blocks some networks — verify
  reachability before relying on it):
  https://pmg.csail.mit.edu/papers/osdi99.pdf

### Verification, testing, and oracles

**11. Claessen, K., & Hughes, J. (2000). QuickCheck: A Lightweight
Tool for Random Testing of Haskell Programs. *Proc. ICFP '00*,
268–279.**
→ §3 instrument 3: confluence as a universally quantified property.
(Exact fit: algebraic laws under random generation with shrinking.)
- DOI: https://doi.org/10.1145/351240.351266
- OA (stable course-archive mirror, Tufts):
  https://www.cs.tufts.edu/~nr/cs257/archive/john-hughes/quick.pdf

**12. [proposed] Barr, E. T., Harman, M., McMinn, P., Shahbaz, M., &
Yoo, S. (2015). The Oracle Problem in Software Testing: A Survey.
*IEEE Transactions on Software Engineering*, 41(5), 507–525.**
→ §6.1's scope-overreach analysis: the evidence command as a weaker
(partial) oracle than the claim text. *(Title corrected: includes
": A Survey".)*
- DOI: https://doi.org/10.1109/TSE.2014.2372785
- OA (UCL Discovery institutional repository):
  https://discovery.ucl.ac.uk/id/eprint/1471263/1/06963470.pdf

### Event logs, immutability, and append-only structure

**13. Fowler, M. (2005). Event Sourcing. martinfowler.com, 12 December
2005.**
→ §1's derive-don't-store status fold: state = fold(log), rebuildable
at will. Cite as what it is — an unfinished development draft (Fowler's
own caveat on the page), not maintained guidance.
- URL: https://martinfowler.com/eaaDev/EventSourcing.html

**14. [proposed] Laurie, B., Langley, A., & Kasper, E. (2013).
Certificate Transparency. RFC 6962 (Experimental), IETF, June 2013.
Obsoleted by RFC 9162 (CT v2.0, December 2021).**
→ INV-A's append-only gate: CT's consistency proof establishes exactly
"old log is a prefix of new log." INV-A checks the same *invariant* by
direct prefix comparison rather than Merkle proof — same property,
weaker (first-party) trust model. Also the middle option for §10's
signing item.
- DOI: https://doi.org/10.17487/RFC6962
- Canonical/OA: https://www.rfc-editor.org/rfc/rfc6962 (successor:
  https://www.rfc-editor.org/rfc/rfc9162)

**15. Helland, P. (2015). Immutability Changes Everything. *CIDR
2015*; reprinted in *ACM Queue*, 13(9), November/December 2015.**
→ Appendix B: the append-only file as research instrument ("accountants
don't use erasers"; the log is truth, everything else a derived cache).
- OA (CIDR proceedings PDF):
  https://www.cidrdb.org/cidr2015/Papers/CIDR15_Paper16.pdf
- Queue version DOI: https://doi.org/10.1145/2857274.2884038

### Convergence and staleness under replication

**16. Shapiro, M., Preguiça, N., Baquero, C., & Zawirski, M. (2011a).
Conflict-free Replicated Data Types. *SSS 2011*, LNCS 6976, 386–400.**
→ Cited for the **theory**: strong eventual consistency via semilattice
join / commuting operations — why F3/F6's per-field merge disciplines
converge at all. The type catalog is #17's, not this paper's. The FWW
register is **not** in either paper: it is this artifact's derived
write-once (min-timestamp) variant, built on the same convergence
argument.
- DOI: https://doi.org/10.1007/978-3-642-24550-3_29
- OA (HAL; the RR-7687 technical-report version of the same paper):
  https://inria.hal.science/inria-00609399/document

**17. Shapiro, M., Preguiça, N., Baquero, C., & Zawirski, M. (2011b).
A Comprehensive Study of Convergent and Commutative Replicated Data
Types. INRIA Research Report RR-7506, 50 pp.**
→ The catalog reference for F3/F6's named types: LWW register (status)
and 2P-Set tombstone (§6.3). No DOI; HAL is the publisher of record.
- OA: https://inria.hal.science/inria-00555588/document (landing:
  https://inria.hal.science/inria-00555588)

**18. [proposed] Mokhov, A., Mitchell, N., & Peyton Jones, S. (2018).
Build Systems à la Carte. *Proc. ACM Program. Lang.*, 2(ICFP),
Article 79.**
→ `evidence_paths` as tracked dependencies; the invalidation scan as a
**verifying-traces rebuilder** *(corrected — the paper's whole point is
that rebuilders and schedulers are orthogonal; "verifying traces" is a
rebuilder; the scan's in-order walk is the trivial topological
scheduler)*.
- DOI: https://doi.org/10.1145/3236774 (CC BY — the ACM DL copy is
  open access)
- OA (Microsoft Research):
  https://www.microsoft.com/en-us/research/wp-content/uploads/2018/03/build-systems.pdf

**19. Kleppmann, M., Wiggins, A., van Hardenberg, P., & McGranaghan,
M. (2019). Local-First Software: You Own Your Data, in spite of the
Cloud. *Onward! 2019*, 154–178.**
→ The artifact's overall shape: plain user-owned files, git as sync
layer, no server. (The paper's own evaluation rates Git among the
closest existing approximations of local-first.)
- DOI: https://doi.org/10.1145/3359591.3359737
- OA (author's page): https://martin.kleppmann.com/papers/local-first.pdf
- Essay version: https://www.inkandswitch.com/essay/local-first/
  *(URL corrected — the old `/local-first/` path is dead)*

### Standards

All catalog pages verified live with status **Published**; texts are
paywalled.

| Standard | Used for | Catalog |
|---|---|---|
| ISO/IEC/IEEE 29148:2018 — Requirements engineering (Ed. 2) | Individual requirement characteristics; set completeness; set consistency | https://www.iso.org/standard/72089.html |
| ISO/IEC/IEEE 24765:2017 — Systems and software engineering vocabulary (Ed. 2) | Forward / backward traceability definitions | https://www.iso.org/standard/71952.html |
| ISO/IEC/IEEE 12207:2017 — Software life cycle processes (Ed. 1) | Verification vs. validation; requirements analysis process | https://www.iso.org/standard/63712.html |
| ISO 10007:2017 — Guidelines for configuration management (Ed. 3) | Configuration status accounting | https://www.iso.org/standard/70400.html |
| ISO/IEC 25010:2023 — SQuaRE product quality model (Ed. 2) | Functional completeness (sub-characteristic) | https://www.iso.org/standard/78176.html |
| ISO/IEC 25023:2016 — Measurement of product quality (Ed. 1) | Functional completeness (the measure) | https://www.iso.org/standard/35747.html |
| ISO/IEC/IEEE 29119-1:2022 / -2:2021 / -3:2021 / -4:2021 — Software testing (Ed. 2) | Requirement-based coverage | Part 1: https://www.iso.org/standard/81291.html · Part 2: https://www.iso.org/standard/79428.html · Part 3: https://www.iso.org/standard/79429.html · Part 4: https://www.iso.org/standard/79430.html |
| ISO/IEC/IEEE 42010:2022 — **Software, systems and enterprise** — Architecture description (Ed. 2) | Correspondence rules | https://www.iso.org/standard/74393.html |

Note on 42010: the 2022 edition changed the title from "Systems and
software engineering" to "Software, systems and enterprise" — use the
new title when citing the current edition.
