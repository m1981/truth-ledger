# Gate-metric registry — Tier B gates and counted overrides

> Reader: the R11 monthly hand-audit, first item on its agenda |
> Enables: answering "does this gate pay?" from data, and retiring the
> ones that don't | Update-trigger: a gate ships or retires (ADR-047:
> a new gate enters PROPOSED with a metric or not at all), or a monthly
> review lands new minutes.

**Placement note (meta-repo side, deliberately).** This file holds
OPERATIONAL REVIEW STATE — current instrument readings and review
minutes for *this repository's* ledger — not shipped machinery. The
rule it implements is template policy
(`template/docs/adr/truth/047-gate-adoption-metrics.md`); the numbers
and judgments below are ours alone and are never templated (the
ADR-003 placement test). Reviews ride the existing R11 monthly
hand-audit slot — zero ceremony beyond the audit already due.

## The registry

Current values pulled 2026-08-02 from the Tier C instruments
(`python3 instruments/override-velocity.py --json`,
`instruments/separation-report.py --json`,
`instruments/blast-report.py --json`) and `scripts/truth stats --json`
(198 claim filings; folded: 67 live · 15 unverified · 40 stale ·
27 diverged · 49 retracted).

| Gate / override | Adoption metric | Source | Current (2026-08-02) | Next review | Standing |
|---|---|---|---|---|---|
| `text-nonempty` (G0, no override) | refusal count — the gate has NO override flag, so there is no override to count; and a refusal appends nothing to fold (the ADR-035 note, INV-M precedent), so the count is **unmeasurable from the ledger by construction**. Named honestly rather than proxied | none possible from the ledger; standing evidence that it fires = the gate-table order pin (`test_gate_table_pre_execution_order_is_pinned`, core suite) + schema `text` `minLength: 1` mirrored by the FS-2 mutant conformance corpus | no counter, by construction · hand-exercised at this review in a scratch repo: empty and whitespace-only text both refuse and **no ledger line is written** (the append-nothing property, observed) · end-to-end arms **GS7/GS7b** (v0.9.33) assert the refusal and the ledger-unchanged property, red-proven by gutting the gate body | 2026-09-08 | armed, uncounted by construction |
| `class-precheck` (G4/G1/G10/INV-B intake, no override) | refusal count — same shape: no override flag, and a refusal appends nothing, so **unmeasurable from the ledger by construction** | none possible from the ledger; standing evidence that it fires = canary **FAULT F (G1)** (a VERIFIED claim in a zero-commit repo is refused, end-to-end) + core-suite unit tests of `verified_intake_error` / `inferred_intake_error` (the INV-B, G10, G1 and INFERRED-without-basis branches) | no counter, by construction · FAULT F green in the suite run at close of the migration | 2026-09-08 | armed, uncounted by construction |
| G8 near-duplicate (+ `--duplicate-ok`) | override rate: duplicate-ok filings / all claim filings (ADR-007's ~50% recalibration line, applied per ADR-018) | override-velocity `overridden_duplicates` ÷ ledger claim count | 11 / 198 = **5.6%** | 2026-09-08 | armed |
| ADR-007 quantifier-scope (+ `--scope-ok`, ADR-032 decay) | `--scope-ok` volume; largest granted TTL; decay expiries vs genuine diverges | override-velocity `scope_basis_filings`, `max_scope_ttl_days`, `decay_expiries` | 8 filings · max TTL **3650 d** (historical — minutes item 3) · 0 expiries | 2026-08-08 | armed |
| INV-M dead-tripwire family (ADR-024) | dead watches reaching the fold (target 0) — refusals are deliberately uncounted (a refusal appends nothing, ADR-035 note) | hand check at audit + canary FAULT T arms | 0 observed | 2026-08-08 | armed |
| ADR-009/021/022 evidence screen (+ `--evidence-unsafe-ok`) | unscreened-filing volume | override-velocity `screened_false_filings` | **0** | 2026-08-08 | armed |
| G6 determinism double-run (+ `--single-run`) | **no stored counter — the one uncounted override (registry gap, finding of this review)**; loose proxy: mechanical diverges | none mechanized; `stats --json` `verdicts.diverge_mechanical` as proxy | proxy: 5 mechanical diverges (all ADR-012-annotated, none attributed to `--single-run`) | 2026-09-08 | armed, gap flagged |
| ADR-035 positive-claim exit gate (+ `--evidence-exit-ok`) | exit-ok override volume; hollow-warned population | override-velocity `evidence_exit_filings`, `hollow_warned` | 0 overrides · 6 hollow-warned | 2026-08-08 | armed |
| ADR-036 tombstone citation gate (+ `--orphan-ok`) | deliberate-orphaning volume | override-velocity `orphan_filings` | **0** | 2026-08-08 | armed |
| ADR-037 generated-paths (+ `--generated-ok`, ADR-032 decay) | generated-ok override volume | override-velocity `generated_ok_filings` | **0** | 2026-08-08 | armed |
| ADR-038 dirty-watch advisory | restale-at-birth incidence — advisory-only, no counter; hand-read of filing transcripts at audit | none mechanized (advisory prints, stores nothing) | no counter | 2026-09-08 | armed (advisory) |
| ADR-039 blast advisory | calibrated floor vs fallback; forecast-vs-observed spread; history health | blast-report `effective_floor`, `floor_source`, `rows`, `history_state` | floor **64** (calibrated) · history ok · top staler `template/scripts/truth` (988 invalidations) | 2026-09-08 | armed (advisory) |
| ADR-033 verbatim-repeat detector | repeats caught once decay-expiry→re-file cycles exist | override-velocity `repeats` (+ `decay_expiries` as the opportunity clock) | repeats **[]** · 0 expiries (no firing opportunity yet) | **2026-10-08** | **dated probation** (minutes item 1) |
| `label-coupling` (battery arm 8b, no override flag) | unrecorded-coupling count: module pairs sharing ADRs above the 0.25 Jaccard threshold with no import between them and no line in `.truth/label-coupling-opt-out`. The gate's whole job is to refuse the NEXT one, so a healthy reading is 0 and the interesting series is the opt-out file's growth rate — each new line is a decomposition that forced an architectural ruling | `instruments/label-coupling.py` summary line (`N unrecorded coupling(s)`) + `wc -l .truth/label-coupling-opt-out` | 0 unrecorded · opt-out holds 5 pairs (4 baseline 2026-08-18 **unadjudicated**, 1 adjudicated 2026-08-18 as ADR-041/056 forced split) · fired once in its first 2 days, catching `evidence~shellio` | 2026-09-20 | armed, **on probation**: filed 2026-08-20, retroactively — the gate shipped 2026-08-18 without this row, which ADR-047 makes part of a gate's definition of done. Review must ask whether one catch in two days is signal or a threshold set too low |

Supporting Tier C context read alongside (not gates, no rows): the
separation report (172 author→verifier pairs, 0 same-session, median
gap 210.8 s, 14 unevidenced verdicts of which 1 on a live claim,
tr-ad7bba71) feeds the ADR-010 half of the audit.

## First review — minutes, 2026-08-02 (applying migration decision D5)

Present: operator. Scope: every row above, plus the two named
first-review actions from the migration plan (P6 item 3). Retirement
judgments use the ADR-047 three-question test: (1) real opportunity to
fire? (2) when it fired, was it acted on? (3) does the guarded failure
exist in the declared regime?

### 1. ADR-033 verbatim-repeat detector → dated probation (D5: retire nothing at first review)

The detector flags a `--scope-ok` basis re-filed verbatim after its
decay expiry — the shape of an override that was never real judgment.
It has fired zero times (`repeats: []`), but question 1 answers "no
opportunity yet", not "never": it can only fire after a
decay-expiry→re-file cycle, and `decay_expiries` is 0 because no
30-day TTL has lapsed yet. Three `ttl_default` filings now feed the
pipeline: one from 2026-07-31 (since diverged) and the batch's two
fresh `--scope-ok` filings from the 2026-08-02 re-anchoring session —
tr-d6ce1dd9 and tr-ce35e9fe, both live, both on the ADR-032 30-day
default — so the earliest possible expiries are 2026-08-30 and
2026-09-01 (the plan's "~2026-08-19" estimate predated the actual
filing dates; these are the real clocks). **Probation terms:
reviewable once ≥5 decay-expiry→re-file cycles exist; realistic review
2026-10-08.** Retirement condition, per the test: retire then only if
question 1 has matured (≥5 completed cycles), the detector caught
nothing across them, AND a hand-read of the re-files confirms nothing
was there to catch; keep on any caught repeat that was acted on.

### 2. G8 calibration — keep 0.6, re-review with 30 more days of data

The review question: is `DUPLICATE_THRESHOLD = 0.6` Jaccard too
aggressive? The data: 11 `--duplicate-ok` filings across 198 claim
filings ever — a **5.6% override rate**, far under the ~50% line
ADR-007's adoption gate sets for narrowing. All 11 landed in one batch
(2026-07-29, the v0.9.18 ADR-path re-anchoring session), where
successor re-filings are near-duplicates *by construction* — the gate
firing on them and being deliberately overridden is correct operation,
not friction. The recent migration batch adds a second signal: G8
refused templated boilerplate sentences outright, which is the failure
it exists to guard actually occurring and being stopped. Questions 1–3
all answer yes. **Decision: keep 0.6 unchanged; re-review 2026-09-08
with the next 30 days of filings** (conservative — one legitimate
override batch and one correct refusal is signal, not yet a calibration
dataset).

### 3. The 3650-day scope-TTL — traced; human re-justification queued

`max_scope_ttl_days: 3650` in the override report is carried by exactly
one claim, found by scanning the ledger for `scope_basis` +
`ttl_days: 3650`:

```
tr-ebac6513  (filed 2026-07-21, session coverage-policy-0721; RETRACTED 2026-07-29)
text:  "the ADR series is a dense record set: 33 decision records
        numbered 001 through 033 ... this claim is set-level RECORD
        integrity and will stale whenever an ADR is added or a Status
        header removed"
scope_basis: "the evidence globs template/docs/adr/[0-9]*.md, which is
        exactly the whole numbered ADR series (not a package-scoped
        sample), so the count check and grep -L Status reach every ADR
        the sentence quantifies; the scope is the complete set by
        construction"
retraction basis (2026-07-29): "superseded by the v0.9.18
        docs/adr/truth path re-anchor successor"
```

Finding: the outlier is **historical** — the carrying claim was
retracted 2026-07-29 in the ADR-namespace re-anchor, and no live claim
carries an outsized TTL (the other seven `--scope-ok` filings are
either TTL-less pre-ADR-032 records or on the 30-day default). The
instrument reads filings, not folded status, so 3650 will report
forever; that is the append-only ledger being honest about history,
not a live liability. What remains is the *policy* judgment only a
human can make — was granting 3650 days ever right, and what is the
honest shelf life for a set-level sentinel re-filed on this lineage —
queued as operator action (a) in
`docs/governance/operator-actions-2026-08.md`, with both command
lines ready.

### Review outcome

Retired: nothing (D5 honored — first review retires nothing).
Probation: ADR-033 (dated, terms above). Recalibrated: nothing (G8
kept at 0.6 on data). New registry-tracked gaps: G6's uncounted
`--single-run`; ADR-038's counterless advisory. Next scheduled read of
this table: the R11 monthly hand-audit due ~2026-08-08.

### Addendum, 2026-08-02 — the registry was incomplete when it shipped

The three independent audits of the P0–P6 migration
(`docs/reviews/migration-audit-2026-08-02.md`) found the table claiming
ADR-047 §1 coverage of "every Tier B blocking gate" while omitting two
hard, override-less refusals — `text-nonempty` (G0) and `class-precheck`
(G4) — because the first pass enumerated *counted overrides* and
silently treated "has an override flag" as the membership rule. Both
rows are added above with the honest metric (refusal count,
unmeasurable from the ledger by construction) rather than an invented
number; the registry now carries 13 rows, not the 11 the v0.9.31
CHANGELOG entry states. One residual gap this surfaced — `text-nonempty`
having no end-to-end behavioral arm, so a regression that dropped the
row's *effect* while leaving its name in place would be caught by
neither pin — **was closed the same day** by canary arms GS7/GS7b
(v0.9.33): empty and whitespace-only text refused with the ledger
unchanged, plus a negative control that ordinary text still files. The
arm was red-proven by gutting `_gate_text_nonempty`'s body, which
reddened GS7 alone (`rc=0/0, lines 8->10`) while the negative control
stayed green. Nothing from this addendum carries to the R11 audit.
