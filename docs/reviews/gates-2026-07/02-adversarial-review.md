# Review of proposed ADRs 034–037

> Reader: the truth-ledger operator | Method: five independent Fable
> agents — four adversarial fact-checkers (one per ADR, every citation
> re-verified against the meta-repo, the kuchnie ledger, and git
> history; all numbers recomputed from raw JSONL) and one design
> reviewer (fit with ADR corpus 001–033, implementability in
> `template/scripts/truth`, threshold sanity, canary testability).
> Date: 2026-07-30. All checks read-only.

## Headline

The proposal's field grounding is excellent — nearly every number
recomputes exactly from the raw ledgers (tr-23661434's 15×/15×,
median 0.31 h, max 263.4 h; the 1,522-record count; the QB-011
incident shape; the verbatim machinery.md retraction-sweep quote).
But **each ADR carries at least one error that must be fixed before
adoption**, two of them load-bearing:

1. **ADR-036 contradicts its own example** — the "negation lexicon"
   it claims to reuse does not exist as an artifact, and its flagship
   mixed-claim exemplar (`tr-d59194ea`, "reads **neither** X **nor**
   Y") carries *no* token from the real `QUANTIFIER_TOKENS` set —
   under the ADR's own rule it would be refused, not warned. Found
   independently by two agents.
2. **ADR-034's default threshold is falsified by the meta-repo's own
   history** — 82 of 96 path-carrying meta-repo claims would exceed
   BLAST_THRESHOLD=15; a claim watching `template/scripts/truth`
   alone forecasts 50–76 commits/30d. `--blast-ok` would be the
   per-filing ritual on day one.

**Recommended adoption order — inverted vs. the proposal:**
036 (after lexicon fix) → 037 (with widened exclusions) → 035 (with
relocated generated-paths check) → 034-lite (forecast + stats report
only; the refusal gate returns as its own ADR after one field window
of forecast-vs-observed data — which is what the house's own
ADR-032/033 calibration discipline demands, and what the proposal's
closing paragraph concedes without acting on).

---

## ADR-034 (blast-radius forecast) — REDESIGN: ship report + advisory, defer the refusal gate

Fact-check: mostly solid. Confirmed by recomputation: paper §2.2
~98.5% and §8 item 2; §9 convention + 2026-07-13 adoption;
tr-23661434 stalings 15×, agrees 15×, intervals median 0.310 h /
min 0.0045 h / max 263.35 h; fsguard.go 8-staled/2-genuine/6-true;
DUPLICATE_THRESHOLD; INV-M intake checks; F1/W2; growth-gate #3;
ADR-032/033/007/019 characterizations. BLAST_THRESHOLD=15 survives
replay on kuchnie history (union 20 > 15 refuses; hottest single file
14 < 15 passes — margin of exactly one commit).

Errors to fix:
- **Provenance**: "kuchnie `fsguard.go`" — the file belongs to
  `temporal-go-agent-sdk` (second deployment); the ADR's own
  Supersedes line says so, contradicting its Context bullet.
- **Window**: "In 21 days it staled 15×" — tr-23661434 lived
  15.3 days; ~22 days is the whole-ledger span.
- **FS-1 adjacency is false**: the half-life suggestion prints only
  on `--ttl-days` filings (truth:2066–2074), which this ADR's own
  non-goals exclude — for every claim the gate covers there is no
  FS-1 line to sit "beside".
- **"ADR-011's authority split" is an invented citation** — the term
  appears nowhere in the corpus and no ADR forbids machine-authored
  claims (agents file claims constantly). The no-auto-narrowing
  decision is fine on its own; it needs no false precedent.
- **Estimator arithmetic**: "distinct commits = expected stalings =
  verifications" is an upper bound, not an expectation — a claim
  stales only from live; N commits between re-verifications produce
  one staling (observed in tr-23661434 itself: 15 invalidations,
  14 re-agrees). Fine as a hotness forecast; wrong as stated.
- **Characterization**: the dominant staler among the four watched
  paths is a *document* (`docs/specs/use-cases.md`, 11/15 stalings),
  not the "hot source file".

Design findings:
- **Threshold falsified at home** (see headline). A default that
  refuses the median filing in the template's own repo is not a sane
  default; kuchnie may be cooler, but the template ships to unknown
  consumers.
- **Timing inverts the house discipline**: reaffirm (ADR-030) already
  automated the hash-match arm of exactly this churn; paper §8
  item 2 names "does reaffirm recover it?" as the open question of
  the running trial (~2026-08-08 read). Gating filings on a cost the
  shipped countermeasure may have absorbed, before the first data
  read, contradicts ADR-032/033's own "no threshold until the FP
  rate is known" precedent.
- **"ADR-032's move" is overclaimed**: ADR-032 revisits
  *mechanically* (decay → scan → re-file → gate re-fires); ADR-034's
  revisit is a stats table a human may read — that is ADR-033's
  move. If ADR-032's move is wanted, `--blast-ok` should carry the
  default decay.
- **B4 has a silent hole**: a shallow clone does not error `git
  log` — it silently truncates and the forecast quietly reads cold
  (the exact silent skip B4 forbids). Needs
  `git rev-parse --is-shallow-repository`. "git absent" is an
  unreachable arm (intake already ran git). "No commits in window"
  is claimed both as the cold-pass notice and a degradation reason.
- **B2 violates the fatigue budget**: a forecast line on *every*
  filing, where the house prints zero lines on a clean filing (W2
  silence-on-clean). Print only above a floor.
- The per-HEAD cache implies an unspecified machine-local state
  file; one `git log --name-only` per intake is cheaper than the
  double-run already is — drop the cache.

What survives fully: the `stats` blast/churn section, the advisory
forecast, and the demand-signal argument for growth-gate #3.

## ADR-035 (volatile-recipe linter) — ADOPT WITH AMENDMENTS

Fact-check: field grounding excellent. Confirmed: multiagent note 3
(both the `grep -n` divergence and the generated-file restaler, plus
the never-shipped generated-list proposal); batch-M note 2 and
**tr-3b69f8ff** (filed VERIFIED with rc=1 and the empty-output hash;
diverged `--mechanical`, successor tr-bbdff732); **tr-22853f21**
(hardcoded `v0.9.8` grep, broke at v0.9.9, diverged then retracted);
ADR-012 subtype; the ADR-009→double-run seam exists exactly where
claimed; accept-allow ships empty with the policy header; the
`contradicts` maxim is verbatim in the paper; ADR-007's
constants-with-faults precedent is real.

Errors to fix:
- **Wrong prose home**: none of the four rules is in machinery.md's
  filing-hygiene section (it has seven different rules). They live in
  the two field notes and `template/.truth/README.md:429–435`. Three
  sentences in the ADR (Supersedes, non-goals, Consequences) depend
  on the false placement.
- **"Three" vs four** — twice (Context opener, Supersedes line); the
  ADR defines four classes.
- **"ADR-011 lesson" misattributed**: refuses-legitimate-filings-
  teaches-bypass is ADR-014's confused-deputy lesson (and the
  accept-allow header); ADR-011's lesson is about refusal *messages*
  naming the bypass.
- **"Both are already counted" is half false**: stats counts
  mechanical divergences, but there is no hollow-VERIFIED counter
  anywhere (the v0.9.11 warning is per-filing stderr, never tallied).

Design amendments:
- **Move the generated-paths refusal to the INV-M position** (it is a
  path check, not a recipe check; INV-M applies to all classes with
  `evidence_paths` — a generated-file watch on an INFERRED claim
  re-stales identically; the proposed placement inside the VERIFIED
  arm misses that case).
- **Version/date shapes over-fire**: 25 of 98 meta-repo VERIFIED
  commands contain version-shaped tokens; many are legitimate
  invariants — including the schema `$id` `truth-ledger-record.v0.9`,
  the very anchor that FIXED the tr-22853f21 defect, and filename
  dates. Needs path/filename and schema-id carve-outs.
- **Phrase arm: raise to 8+ words or drop.** The motivating defect is
  subsumed by ADR-036 (tr-3b69f8ff filed with exit 1 on a positive
  sentence → refused there); ~13% of real recipes carry a ≥5-word
  quoted phrase, mostly legitimate single-line greps and regex
  alternations the naive word count mis-tokenizes. Also: the field
  case is exactly 5 words and the proposed R3 tests 6 and 3 — the
  boundary is canary-unpinned; an off-by-one would miss the
  motivating defect.
- **`--generated-ok` must join `override_report`** — 034/036/037 all
  route their overrides there; 035 forgets.
- Minor: the "no point double-running a recipe about to be warned"
  rationale is muddled (warnings don't block; only the refusal class
  benefits from pre-execution placement); the paper's F1 collides
  with an unrelated canary F1 label.

## ADR-036 (positive-claim exit gate) — ADOPT WITH AMENDMENTS (strongest core; lexicon must be fixed first)

Fact-check: infrastructure confirmed precisely — paper §4
hollow-VERIFIED row, v0.9.11 non-blocking warning + absence-proof
rationale, `evidence.returncode` recorded (truth:2036–2039), recheck
compares against the *recorded* exit (truth:1111–1118), `--scope-ok`
basis discipline, ADR-033 stats home, INFERRED/UNVERIFIED carry no
evidence command. The tr-0e884e02/QB-011 incident is as told: 4-leg
`&&`-chain, rc=1, empty-output hash, verifier diverge tr-ca69eadb,
retraction tr-11f8bffc, successor tr-06522739 (rc=0, agreed).

Errors to fix:
- **The negation lexicon does not exist.** There is one undivided
  `QUANTIFIER_TOKENS` constant (15 tokens incl. positive universals);
  no `NEGATION` constant anywhere. The ADR treats new machinery as
  already-shipped, with no N-faults locking the subset.
- **The flagship example breaks the gate**: tr-d59194ea's negators
  are "neither"/"nor"/"not"/digit "0" — none in the lexicon
  (`tokens()` splits on `[a-z0-9]+`; "no" ≠ "not"). Under the rule as
  written it is refused; the Non-goals section promises the warning
  path. Fix: a dedicated `NEGATION_TOKENS` superset (not, n't,
  neither, nor, without, absent, lacks, missing…), **decoupled** from
  ADR-007's constant — sharing it would silently widen the ADR-007
  gate.
- **Mechanism misattribution**: the stash-pop dropped the
  machinery.md authoring-loop section, not "the version pin" — the
  verifier verdict on record says the pin passed. (The successor
  claim's own ambiguous text likely misled the author.)
- **Name `done --claim` explicitly**: it files VERIFIED through the
  same `build_claim_payload` path — covered by a natural
  implementation, but the ADR text says only "`truth claim`
  intake", and the paper's two real hollow instances were completion
  claims. Sibling 034 names both verbs; 036 should too.
- Broader false-refusal classes than acknowledged: diff-based proofs
  ("a and b differ" — exit 1), "absent"/"missing"/"lacks"/"0
  matches" phrasings; and inverted recipes (`! grep`) exit 0, so the
  token test is a proxy for the *sentence's* polarity, not the
  recipe's. Acceptable with the wider lexicon + `--exit-ok`, but the
  ADR should own the residual honestly.
- Cosmetic: "ADR-029 layering" is loose decoration (ADR-029 is about
  the screen gating execution); X5's validate check must tolerate
  legacy records lacking `evidence.returncode` (recheck already
  does, via `.get`).

Why it goes first anyway: smallest diff; the returncode is already
in the payload at the exact seam; the defect actually shipped past
the cheap layer once (QB-011); and it subsumes the worst of 035's
phrase class.

## ADR-037 (tombstone citation gate) — ADOPT WITH AMENDMENTS (mechanism right, grep scope wrong)

Fact-check: the machinery.md quote is **verbatim**; ADR-011 ceremony
and `done --cancel` exact; ADR-001 HELD matrix and ADR-020
"retracted is the only non-recoverable verdict" exact; two-commit
dance residual matches machinery.md:124–128; excluding claims.jsonl
is provably necessary (retraction bases cite successor ids
throughout).

Errors to fix:
- **"Six retractions in the pilot's whole window" is wrong by 11×**:
  the pilot has **66** retracted claims over the window (paper's "6"
  is the two-day Window 1 figure); the meta-repo has 49. Retractions
  arrive in human batch sweeps of 21–28 (e.g. commit 217306c: 21 at
  once). The fail-closed argument survives, but must be argued from
  66/49-in-batches, not 6.
- **Exclusion list too narrow — measured**: 12 of the meta-repo's 49
  already-retracted ids are cited right now in tracked markdown
  outside `docs/archive/` (CHANGELOG, ADRs 023/024, field notes,
  roadmap, operations guide, loophole map) — historical record, not
  live dependencies. Under the gate as written those retractions
  would have refused → `--orphan-ok` ritualization on day one.
  Kuchnie's own historical-exemption convention is far broader
  (archive|attic|docs/adr|freeze|CHANGELOG). Fix: match the corpus
  the health gates actually judge — best, make the inclusion scope a
  consumer-declared policy file (the 035 generated-paths move),
  defaulting to the template gate's scope (`docs/specs/`).
- **Wrong ingredient named**: `fact-health.sh` is META-REPO ONLY by
  its own header (tr- ids only, README+docs only, manual, currently
  red with 46 failures and blocking nothing); the template-shipped
  analogue is `spec-health.sh` (tr+wk, `docs/specs/`), and even that
  blocks commits only where a consumer wired it (kuchnie's
  `.beads/hooks/pre-commit` → check-governance 5c). "Every
  ingredient already exists" holds only with that correction.
- **Truncated citations are invisible**: tracked docs cite
  `tr-3b69f8…` / `tr-22853f…` with ellipses (batch-M does; this
  proposal document itself does) — a `-F` full-id grep never matches
  them. Named residual to add, or normalize the citation style.
- Minor: ADR-013's gate demands ceremony, not a judged coverage
  answer (paraphrase stretch); TOCTOU window for citations added
  after the sweep (or untracked files) — accept and name it.
- "All human" is self-attested (actor field + prose bases), not
  record-visible; phrase accordingly.

What is genuinely good: fail-closed on git-unavailable is the one
earned exception to the F1 fail-open-loud default (rare verb, human
already in ceremony); "only the terminal verb earns the terminal
check" (no `diverge` coverage) is the right boundary.

## Cross-cutting

- **Canary namespace collisions**: proposed B1–B5 collide exactly
  with existing FAULT B1–B6 (ADR-008/031 arms), T1–T5 with FAULT T
  (INV-M), R1–R5 with the R10/R11 roadmap-finding namespace. Only X
  is free. Rename (e.g. BL/RC/TG).
- **Stacked fatigue never totaled**: worst-case single filing under
  all four = up to five override flags with bases (`--duplicate-ok
  --scope-ok --blast-ok --generated-ok --exit-ok`) and up to seven
  stderr lines, where today a clean filing prints zero. Needs one
  combined rule: silence on clean, at most one advisory block per
  filing, and every new override flag lands in `override_report` in
  the same change.
- **Doc-sync surface**: five new payload fields ⇒ schema + validate
  mirror + FS-2 fixtures + `$id` bump + paper §1 + machinery.md +
  README per ADR — the largest sync surface since v0.6, in a repo
  whose memory flags doc-sync silent drops as standing residue.
  Stage the adoptions; don't mega-release.

## What the proposal missed

1. **Dirty-watch warning** (arguably the highest-yield unclaimed
   norm): warn at intake when a watched path has uncommitted
   modifications — mechanizes §9's "commit the work, then file the
   claim" and the restale-at-birth class; one `git status
   --porcelain`; cheaper than 034.
2. **"One fact per claim"** compound-sentence advisory (" AND ", "; "
   in claim text) — 036's own Non-goals names this residual as what
   keeps hollow halves alive, then leaves it prose.
3. **A stats-side churn report alone captures most of 034's value**
   — the blast *gate* is the only expensive-and-premature piece in
   the whole proposal.

## Suggested next steps

1. Hand this review back to the external reviewer for a revision
   pass (all errors are fixable; no ADR needs rejection outright —
   034's refusal arm needs severing, not deletion).
2. If adopting: 036 → 037 → 035 → 034-lite, one release each, canary
   prefixes renamed, override_report extended in the same change as
   each new flag.
3. The verified facts above (retraction counts, threshold replay,
   citation-scope measurement) are filing material for the meta
   ledger if the operator wants them on record — verifier-session
   discipline applies (TRUTH_SESSION, author≠verifier).
