# Spec-coverage manifests — validated design, pilot live

> Reader: anyone extending spec↔test traceability to another spec, or
> auditing why the pilot's sentinels look the way they do | Enables:
> wiring a new spec's assertions to its tests using recipes that already
> survived two falsification rounds, without re-deriving the amendments |
> Update-trigger: a falsified recipe, a second-wave adoption, or a CLI
> change to the evidence screen / recheck semantics

Status: **PILOT LIVE** (kuchnie, 2026-07-26) — first spec wired and
verified; wider adoption is demand-gated. Two adversarial rounds
(2026-07-26): a design round in which the designer falsified its own
first draft (the empty-manifest hole, B1) and a falsification round
that killed the unscoped extraction regex and measured the mechanism's
honest weakness on a live sandbox against CLI v0.9.15. Trigger for the
second wave: the operator wiring the next spec (builder-gui or
worktop-uu-seeding are the natural candidates — both already have
specs and tests).

Standards frame: requirements-based coverage / bidirectional
traceability (DO-178C §6.4.4.3 doctrine, 29148 verifiability, 24765
forward+backward tracing) at hobby weight: no tool qualification, no
coverage percentages, one grep-shaped sentinel per direction. The
missing middle 29119-4 never standardized.

## The design (five parts, post-falsification verdicts)

- **P1 — assertion id scheme** (BUILD, amended): testable assertions
  are named `SC-<slug>-NNN` — slug `[a-z0-9]{3,12}` derived from the
  spec filename (`configurator-api.md` → `cfgapi`), zero-padded 3-digit
  number, monotonic, never reused, renumbering forbidden (an id is a
  name, not an index). The id appears BOTH inline in the spec
  (`- [ ] [SC-cfgapi-001] POST /configurator/sessions returns 201 ...`)
  and as a line in the manifest — the spec copy is what humans review,
  the manifest copy is what machines diff; the sync sentinel makes
  lying between them loud. `SC-` ids are regex-distinct from tr-/wk-
  (spec-health's id tripwire ignores them) and must never be written as
  a valid-looking example elsewhere (a hex-8-shaped example id FAILs
  spec-health as missing-from-ledger; use `SC-<slug>-NNN` placeholders).
- **P2 — per-spec manifest** (BUILD): sibling file `<spec>.sc.txt` —
  ids only, one per line, pre-sorted (zero-padding makes lexical sort =
  numeric sort), NO header, NO comments, LF, trailing newline. A header
  line would diff as a phantom id. `.txt` is invisible to spec-health's
  `*docs/specs/*.md` find and to the consumer's new-doc governance
  gates — verified against both scripts' path filters.
- **P3 — test-side citation** (BUILD): the id verbatim as the FIRST
  line of the citing test's docstring (Python; `// SC-…` comment for js
  later). NOT the test name (identifiers can't carry hyphens; a lossy
  underscore translation would break the single grep alphabet). NOT a
  pytest marker (infrastructure for zero mechanical gain). Citations
  live in `test_*.py` files only — an id cited only in conftest.py or
  a README is invisible to the sentinel by design.
- **P4 — two sentinel claims per spec** (BUILD, amended): the
  spec↔manifest sentinel and the tests↔manifest sentinel (recipes
  below). ONE claim per direction per spec, never per assertion. The
  tests↔manifest diff answers both directions at once: `>` lines =
  manifest id no test cites (coverage gap), `<` lines = test id not in
  the manifest (orphan / typo).
- **P5 — dark-requirement grades** ("assertion-dark", distinct from
  file-dark):

  | grade | meaning | mechanically detectable? |
  |---|---|---|
  | r0 | assertion + citing test + test passing at last `done` | only via ADR-014 accept-cmd at `done`; NOT standing (the E-archetype gap) |
  | r1 | assertion in manifest + ≥1 test file cites it | YES — tests↔manifest pass state |
  | r2 | assertion in manifest, no test cites it | YES — the `>` lines, listed by name |
  | r3 | testable prose never minted into an SC id | **NO — honest limit.** Judged extraction is human/LLM-tribunal work (obligation-ledger design), growth-gated |

## Tested recipes (verbatim — as filed and live in kuchnie; screened
## through the deployed ADR-009 screen, run on macOS BSD grep)

```
# spec<->manifest sentinel (claim tr-fcca2d96 in kuchnie):
test -s catalog/docs/specs/configurator-api.sc.txt && grep -howE 'SC-cfgapi-[0-9]{3}' catalog/docs/specs/configurator-api.md | sort | diff - catalog/docs/specs/configurator-api.sc.txt
# NOTE: plain `sort`, NOT `sort -u`, on the spec side -- `-u` would
# collapse a duplicated marker and auto-agree it (red-team 5.1).

# tests<->manifest sentinel (claim tr-40a5beb5 in kuchnie):
test -s catalog/docs/specs/configurator-api.sc.txt && grep -rhowE 'SC-cfgapi-[0-9]{3}' --include='test_*.py' catalog/tests | sort -u | diff - catalog/docs/specs/configurator-api.sc.txt
# `-u` IS correct here: multiple tests citing one id is legitimate.
```

**Mandatory recipe rules** (each earned by a reproduced failure):
- `test -s MANIFEST &&` guard (B1): without it, deleting every marker,
  manifest line and citation produces empty output exit 0 —
  byte-identical to PASS; recheck silently auto-agrees the
  disappearance of the entire assertion set. (D3 in
  symbol-tracing-design.md has the same hole; inherit this amendment.)
- Slug-scoped regex `SC-<slug>-[0-9]{3}` (falsifier F2): the unscoped
  `SC-[a-z0-9-]+` extracts EVERY spec's ids — the moment a second spec
  is wired, the first spec's sentinels permanently diverge. Scoping
  also enforces the id grammar (unpadded `SC-cfgapi-7` passed silently
  before it).
- `-w` word-boundary + greedy alphabet inside the scope: malformed ids
  (`SC-cfgapi-0011`, typo'd `SC-cfgapi-01`) surface loud as orphans or
  missing ids instead of part-matching (reproduced four ways in the
  pilot's negative controls).
- `diff` is the comparator, never `wc -l` counts — macOS `wc -l` pads
  with spaces and a padded count comparison becomes a BLIND oracle
  (empty output both ways).
- Watch the test tree as a GLOB (`catalog/tests/**`), never a bare
  directory (INV-M refuses directories; the glob is live at scan time —
  a brand-new test file stales the sentinel, reproduced).

## Wording and intake discipline (falsifier F3/F4/F5, all reproduced)

- **ADR-018 near-duplicate**: parallel-template sentinel texts for a
  second spec hit the Jaccard 0.6 gate (measured 0.818 refused). Texts
  must carry slug + id-range tokens (`SC-cfgapi-001 through
  SC-cfgapi-006`); the pilot pair measured 0.273 spec↔tests. If a
  future pair still trips, `--duplicate-ok` is documented policy (the
  override is recorded and reviewable).
- **ADR-007 quantifier gate**: sentinel evidence always carries scope
  signals (`--include`, slash paths), so quantifier tokens in the text
  (only/no/none/never/each/all/every/any/entire/whole/zero/always)
  refuse the filing. The universal MEANING lives in the diff's algebra,
  not the claim's wording — same dodge D3 uses.
- **Ordering (anchor trap)**: commit spec+manifest+tests FIRST → file
  claims → commit ledger. A claim filed before the content commit
  re-stales immediately (anchor at pre-content HEAD, reproduced). Same
  rule on every repair cycle.
- **Bring-up**: reaffirm auto-clears only claims that have at least one
  verifier agree; dispatch-verify both sentinels from a NON-author
  session immediately after filing, or the first prose edit leaves them
  stuck stale — and a consumer whose governance runs spec-health
  corpus-wide then blocks unrelated spec commits.

## Named residuals (disclose wherever this ships)

- **r1 is a citation, not an execution** — the strongest reproduced
  attack: delete all citing test methods, paste all six ids into ONE
  comment line of one file → sentinel passes byte-identical to the
  honest state, forever, without even a dispatch. r1 = "string occurs
  somewhere in a test file". Only r0 (ADR-014 accept-cmd actually
  running the suite at `done`) proves execution; only a dispatched
  human/LLM judgment proves the test asserts what the id names. Same
  report-vs-judgment dichotomy as evidence-attached ≠
  evidence-confirmed, one layer up.
- **Drift commits land**: consumer governance (kuchnie 5c) guards the
  repair window, not the drift — a marker committed without its
  manifest twin passes pre-commit (sentinel still `live` at commit
  time) and surfaces at the next scan. Omission, never corruption.
- **One dead sentinel freezes the consumer's whole spec surface** where
  spec-health runs corpus-wide on staged specs (kuchnie: 17 specs).
  Escape sequence verified deadlock-free: fix working tree → commit
  watched files → fresh-session recheck+agree → commit ledger.
- **recheck runs in the caller's cwd** (no chdir to repo root) —
  relative-path evidence false-diverges when rechecked from a
  subdirectory. Ledger-wide property, not specific to this design.
- **Slug registry is convention, not mechanism**: `docs/specs/sc-slugs.txt`
  maps slug→spec; nothing consumes it yet. Slug uniqueness is enforced
  by eyeballs until a second-wave need justifies more.
- r3 (unminted prose) undetectable; retirement of an assertion is a
  three-file dance (marker + manifest line + citations in one commit).

## Pilot record (2026-07-26, kuchnie)

`catalog/docs/specs/configurator-api.md`: six assertions
SC-cfgapi-001..006 (201/session-token/current_step=front; persistence;
nonexistent-variant 400; wrong-step 400; carcass pairing + fallback;
BOM selections) — each verified against the actual router code before
commit. Manifest + slug registry + 8 docstring citations in
`catalog/tests/test_configurator.py` (005/006 cited twice by design).
Negative controls run four ways, all loud. 21 tests green, governance
clean, 0 stale. Content commit 505e02c, ledger commit 2738e0b; sentinels
tr-fcca2d96 / tr-40a5beb5 verified agree by independent session
verifier-r-0726. Cost: ~45 minutes end to end, +2 claims (+1.4% of the
kuchnie ledger).

## What not to build (refused, with reasons)

- No new CLI verb — two screened commands + existing claim/reaffirm
  mechanics cover the loop.
- No test-runner-as-evidence — the exact arbitrary-execution channel
  ADR-009 screens out; r0 stays in the ADR-014 lane.
- No coverage percentages — a ratio invites minting easy assertions;
  the r2 diff lists gaps BY NAME, strictly more actionable.
- No per-assertion claims — 20+ claims/spec recreates the +65%
  ledger-growth failure mode symbol-tracing's economics measured.
- No pytest markers/plugins, no r3 heuristic gate — judgment-laden,
  gameable, teaches marker-avoidant prose.
