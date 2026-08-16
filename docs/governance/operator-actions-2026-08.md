# Operator actions — 2026-08 (post-migration handoff)

> Reader: the human operator, before or with the ~2026-08-08 R11
> monthly hand-audit | Enables: clearing every queued action that only
> a human may take — retraction is human-only (ADR-011), and two of
> the items below are policy judgments no agent may make | Meta-repo
> operational state, never templated.

Every id below was pulled from this ledger on 2026-08-02
(`scripts/truth queue --json`, `list --stale --json`, and the raw
ledger). Retraction commands are written, **not executed** — run them
yourself; `TRUTH_HUMAN=1` plus the id-typed `TRUTH_HUMAN_ACK` is the
ADR-011 gate, and exporting either variable ambiently is the
enforcement deleted (ops guide §4). Preflight every retraction with
`truth citations` (ADR-036): a `clean` id retracts without `--orphan-ok`.

## (a) The 3650-day scope-TTL — re-justify or re-file honestly

The registry's first-review minutes
(`docs/governance/gate-metrics.md`, item 3) traced
`max_scope_ttl_days: 3650` to a single claim, **already retracted**
2026-07-29 in the ADR-namespace re-anchor:

```
tr-ebac6513  "the ADR series is a dense record set: 33 decision records
             numbered 001 through 033 ..."  (ttl_days: 3650, RETRACTED)
```

No live claim carries an outsized TTL, so there is nothing to demote —
but the *policy* judgment is still yours and still open: was a 10-year
TTL on a set-level sentinel ever honest, given the sentence staled
eight days after filing? Pick one:

**Re-justify** (you judge long TTLs acceptable for by-construction
complete scopes): record the ruling on the ledger as reasoning, so the
next audit reads a decision instead of an anomaly:

```sh
scripts/truth claim "operator ruling 2026-08: the 3650-day TTL on the retracted 2026-07-21 ADR-series sentinel was misjudged shelf life, not misjudged scope -- set-level count sentinels stale structurally within days, so scope-ok TTLs on this lineage are capped at the ADR-032 30-day default from here on" \
  --class INFERRED --tier P2 \
  --basis "gate-metrics first review 2026-08-02: the claim staled 8 days after filing and was retracted in the v0.9.18 re-anchor; the instrument's max_scope_ttl_days will report the historical 3650 forever, which is append-only honesty, not a live liability"
```

**Re-file** (you want a set-level ADR-series sentinel again): the live
lineage descendant already exists without any scope override
(the ADR-series count sentinel, retired 2026-08-16 with the corpus), so a re-file is only needed
if that one is retired; the honest shape is the default 30-day decay:

```sh
scripts/truth claim "the machinery ADR series under docs/adr/truth/ is a dense record set: <N> decision files numbered 001 through 0<N> with both endpoints present and every file carrying a Status line" \
  --class VERIFIED --tier P2 \
  --evidence-cmd "ls template/docs/adr/truth/[0-9]*.md | grep -c '\.md$'" \
  --paths "template/docs/adr/truth/*.md" \
  --scope-ok "the evidence glob is exactly the whole numbered series, so the count reaches every file the sentence quantifies" \
  --ttl-days 30
```

## (b) Retract the stale blast-stamping claim

This claim asserts the `blast_forecast` payload stamping that P5
(ADR-046, v0.9.30) deliberately removed — intake no longer stamps, so
the sentence describes retired behavior and has no successor (the
replacement surface is `instruments/blast-report.py`, already claimed
by the migration's own filings):

```
tr-bf6f5b3d  "truth v0.9.25 ships the ADR-039 blast forecast and churn
             report: path filings stamp blast_forecast ..."  (stale)
```

Preflight (run today: reports `clean`, so no `--orphan-ok` needed),
then the human-gated retraction:

```sh
scripts/truth citations tr-bf6f5b3d
TRUTH_HUMAN=1 TRUTH_HUMAN_ACK=tr-bf6f5b3d scripts/truth verdict tr-bf6f5b3d retracted \
  --basis "asserts the blast_forecast intake stamping ADR-046 (v0.9.30, P5) removed; the report surface lives on as instruments/blast-report.py under its own migration claims -- superseded machinery, no successor filing needed"
```

## (c) The superseded-predecessor pool — 31 stale claims with live successors

The migration re-filed the surviving surface claims as explicit
successors ("successor to tr-XXXXXXXX" in the live text). Each
predecessor below is therefore **resolved by succession** — the fact
lives on under a live id — and sits in `truth queue` only because
retraction is human-only: reaffirm may not bury it, a verifier may not
retract it, and until you act it inflates the queue (31 of today's 55
entries). Review the pairs and run selectively; all 31 predecessors were
preflighted today and every one reported `clean` — run `citations`
first regardless, the corpus moves.

```sh
# predecessor -> live successor          retraction (one per line pair)
scripts/truth citations tr-dca73f8a   # -> tr-6c6506fb
TRUTH_HUMAN=1 TRUTH_HUMAN_ACK=tr-dca73f8a scripts/truth verdict tr-dca73f8a retracted --basis "resolved by succession: superseded by tr-6c6506fb"
scripts/truth citations tr-b0f44818   # -> tr-d6ce1dd9
TRUTH_HUMAN=1 TRUTH_HUMAN_ACK=tr-b0f44818 scripts/truth verdict tr-b0f44818 retracted --basis "resolved by succession: superseded by tr-d6ce1dd9"
scripts/truth citations tr-5ad5f3c0   # -> tr-965c10bb
TRUTH_HUMAN=1 TRUTH_HUMAN_ACK=tr-5ad5f3c0 scripts/truth verdict tr-5ad5f3c0 retracted --basis "resolved by succession: superseded by tr-965c10bb"
scripts/truth citations tr-fcdd4af2   # -> tr-ab10b5eb
TRUTH_HUMAN=1 TRUTH_HUMAN_ACK=tr-fcdd4af2 scripts/truth verdict tr-fcdd4af2 retracted --basis "resolved by succession: superseded by tr-ab10b5eb"
scripts/truth citations tr-020b62d3   # -> tr-66b04399
TRUTH_HUMAN=1 TRUTH_HUMAN_ACK=tr-020b62d3 scripts/truth verdict tr-020b62d3 retracted --basis "resolved by succession: superseded by tr-66b04399"
scripts/truth citations tr-aec1bec3   # -> tr-d8c45705
TRUTH_HUMAN=1 TRUTH_HUMAN_ACK=tr-aec1bec3 scripts/truth verdict tr-aec1bec3 retracted --basis "resolved by succession: superseded by tr-d8c45705"
scripts/truth citations tr-96379e50   # -> tr-ce35e9fe
TRUTH_HUMAN=1 TRUTH_HUMAN_ACK=tr-96379e50 scripts/truth verdict tr-96379e50 retracted --basis "resolved by succession: superseded by tr-ce35e9fe"
scripts/truth citations tr-e5ab67c3   # -> tr-8cc1f340
TRUTH_HUMAN=1 TRUTH_HUMAN_ACK=tr-e5ab67c3 scripts/truth verdict tr-e5ab67c3 retracted --basis "resolved by succession: superseded by tr-8cc1f340"
scripts/truth citations tr-8d246eb3   # -> tr-f7617bde
TRUTH_HUMAN=1 TRUTH_HUMAN_ACK=tr-8d246eb3 scripts/truth verdict tr-8d246eb3 retracted --basis "resolved by succession: superseded by tr-f7617bde"
scripts/truth citations tr-f8e509c3   # -> tr-d0191e65
TRUTH_HUMAN=1 TRUTH_HUMAN_ACK=tr-f8e509c3 scripts/truth verdict tr-f8e509c3 retracted --basis "resolved by succession: superseded by tr-d0191e65"
scripts/truth citations tr-eb6f5f11   # -> tr-63c0e422
TRUTH_HUMAN=1 TRUTH_HUMAN_ACK=tr-eb6f5f11 scripts/truth verdict tr-eb6f5f11 retracted --basis "resolved by succession: superseded by tr-63c0e422"
scripts/truth citations tr-401625d8   # -> tr-552d0fb0
TRUTH_HUMAN=1 TRUTH_HUMAN_ACK=tr-401625d8 scripts/truth verdict tr-401625d8 retracted --basis "resolved by succession: superseded by tr-552d0fb0"
scripts/truth citations tr-51963fa1   # -> tr-c0771c5c
TRUTH_HUMAN=1 TRUTH_HUMAN_ACK=tr-51963fa1 scripts/truth verdict tr-51963fa1 retracted --basis "resolved by succession: superseded by tr-c0771c5c"
scripts/truth citations tr-f4c6ec38   # -> tr-fc03d886
TRUTH_HUMAN=1 TRUTH_HUMAN_ACK=tr-f4c6ec38 scripts/truth verdict tr-f4c6ec38 retracted --basis "resolved by succession: superseded by tr-fc03d886"
scripts/truth citations tr-7ef593f7   # -> tr-e70240c3
TRUTH_HUMAN=1 TRUTH_HUMAN_ACK=tr-7ef593f7 scripts/truth verdict tr-7ef593f7 retracted --basis "resolved by succession: superseded by tr-e70240c3"
scripts/truth citations tr-cad78a9c   # -> tr-b7cd7180
TRUTH_HUMAN=1 TRUTH_HUMAN_ACK=tr-cad78a9c scripts/truth verdict tr-cad78a9c retracted --basis "resolved by succession: superseded by tr-b7cd7180"
scripts/truth citations tr-7b6a3866   # -> tr-5a268dd5
TRUTH_HUMAN=1 TRUTH_HUMAN_ACK=tr-7b6a3866 scripts/truth verdict tr-7b6a3866 retracted --basis "resolved by succession: superseded by tr-5a268dd5"
scripts/truth citations tr-aa435dc2   # -> tr-37d2a885
TRUTH_HUMAN=1 TRUTH_HUMAN_ACK=tr-aa435dc2 scripts/truth verdict tr-aa435dc2 retracted --basis "resolved by succession: superseded by tr-37d2a885"
scripts/truth citations tr-cebb1b13   # -> tr-384e8dc6
TRUTH_HUMAN=1 TRUTH_HUMAN_ACK=tr-cebb1b13 scripts/truth verdict tr-cebb1b13 retracted --basis "resolved by succession: superseded by tr-384e8dc6"
scripts/truth citations tr-2a7719d5   # -> tr-f0c0c569
TRUTH_HUMAN=1 TRUTH_HUMAN_ACK=tr-2a7719d5 scripts/truth verdict tr-2a7719d5 retracted --basis "resolved by succession: superseded by tr-f0c0c569"
scripts/truth citations tr-d0cfbf59   # -> tr-ae42c16d
TRUTH_HUMAN=1 TRUTH_HUMAN_ACK=tr-d0cfbf59 scripts/truth verdict tr-d0cfbf59 retracted --basis "resolved by succession: superseded by tr-ae42c16d"
scripts/truth citations tr-5abcd0ed   # -> tr-a4eefbf1
TRUTH_HUMAN=1 TRUTH_HUMAN_ACK=tr-5abcd0ed scripts/truth verdict tr-5abcd0ed retracted --basis "resolved by succession: superseded by tr-a4eefbf1"
scripts/truth citations tr-175ed9ff   # -> tr-c37d86f2
TRUTH_HUMAN=1 TRUTH_HUMAN_ACK=tr-175ed9ff scripts/truth verdict tr-175ed9ff retracted --basis "resolved by succession: superseded by tr-c37d86f2"
scripts/truth citations tr-571c4d75   # -> tr-9738a41c
TRUTH_HUMAN=1 TRUTH_HUMAN_ACK=tr-571c4d75 scripts/truth verdict tr-571c4d75 retracted --basis "resolved by succession: superseded by tr-9738a41c"
scripts/truth citations tr-99113e85   # -> tr-b350781e
TRUTH_HUMAN=1 TRUTH_HUMAN_ACK=tr-99113e85 scripts/truth verdict tr-99113e85 retracted --basis "resolved by succession: superseded by tr-b350781e"
scripts/truth citations tr-4f48fd51   # -> tr-b350781e (same successor: the battery claim absorbed both)
TRUTH_HUMAN=1 TRUTH_HUMAN_ACK=tr-4f48fd51 scripts/truth verdict tr-4f48fd51 retracted --basis "resolved by succession: superseded by tr-b350781e"
scripts/truth citations tr-4884ad97   # -> tr-7a10f167
TRUTH_HUMAN=1 TRUTH_HUMAN_ACK=tr-4884ad97 scripts/truth verdict tr-4884ad97 retracted --basis "resolved by succession: superseded by tr-7a10f167"
scripts/truth citations tr-36d503e6   # -> tr-9dd3323b
TRUTH_HUMAN=1 TRUTH_HUMAN_ACK=tr-36d503e6 scripts/truth verdict tr-36d503e6 retracted --basis "resolved by succession: superseded by tr-9dd3323b"
scripts/truth citations tr-5fe1899a   # -> tr-9dd3323b (same successor: the check-truth claim absorbed both)
TRUTH_HUMAN=1 TRUTH_HUMAN_ACK=tr-5fe1899a scripts/truth verdict tr-5fe1899a retracted --basis "resolved by succession: superseded by tr-9dd3323b"
scripts/truth citations tr-efad36a4   # -> tr-126f0629
TRUTH_HUMAN=1 TRUTH_HUMAN_ACK=tr-efad36a4 scripts/truth verdict tr-efad36a4 retracted --basis "resolved by succession: superseded by tr-126f0629"
scripts/truth citations tr-84b4bef5   # -> tr-010f7e96
TRUTH_HUMAN=1 TRUTH_HUMAN_ACK=tr-84b4bef5 scripts/truth verdict tr-84b4bef5 retracted --basis "resolved by succession: superseded by tr-010f7e96"
scripts/truth citations tr-7191f5a9   # -> tr-126f0629 (intermediate generation, staled by the P6 commit)
TRUTH_HUMAN=1 TRUTH_HUMAN_ACK=tr-7191f5a9 scripts/truth verdict tr-7191f5a9 retracted --basis "resolved by succession: superseded by tr-126f0629"
scripts/truth citations tr-30512073   # -> tr-010f7e96 (intermediate generation, staled by the P6 commit)
TRUTH_HUMAN=1 TRUTH_HUMAN_ACK=tr-30512073 scripts/truth verdict tr-30512073 retracted --basis "resolved by succession: superseded by tr-010f7e96"
scripts/truth citations tr-4b486c66   # -> tr-9dd3323b (intermediate generation, staled by the P6 commit)
TRUTH_HUMAN=1 TRUTH_HUMAN_ACK=tr-4b486c66 scripts/truth verdict tr-4b486c66 retracted --basis "resolved by succession: superseded by tr-9dd3323b"
```

Eight further stale claims have no *named* successor edge but the same
rolling-sentinel character (superseded generations of the explainer
Scope-header, ADR-count, fact-health scope-rule, and check-truth
sentinels, whose current generation is live under a different id):

```
tr-d20436c9  tr-d3b14d8f  tr-9381684d  tr-35cb26a5
tr-3a6e778f  tr-9e779082  tr-609d8ac8  tr-a62d0760
```

These merit the same treatment (retract as superseded-in-substance) or
a dispatch if you want a verifier to confirm the mapping first; they
are listed separately because no live text names them, so the succession
is a judgment, not a mechanical read.

## (d) The pre-existing diverged pool — 27 claims, dispatch-or-retire

All 27 diverged entries in today's queue predate this migration: they
are version- and count-sentinels (the "N decision files" ADR-series
generations, the explainer version-sync generations, the pilot's
v0.6.4 sync claim, the canary arm-set snapshots) whose recheck diverged
between 2026-07-31 and 2026-08-02 as the migration's releases marched
the counts and versions past them:

```
tr-e98e1ec5  tr-58e5fce2  tr-56682235  tr-f49a00ee  tr-4387f0ea
tr-258cef92  tr-b1802f6d  tr-f7b750de  tr-1089dc18  tr-e933009d
tr-e0de52a6  tr-44dafee6  tr-69f2bbea  tr-b4b70b98  tr-329f0a1b
tr-d1d7b77a  tr-05d0cfb5  tr-a2c242c7  tr-56e810de  tr-3fb81974
tr-25152203  tr-06726841  tr-1ee2b698  tr-6ebfedce  tr-14394281
tr-f788e062  tr-88f20f3f
```

Divergence triage is a judgment (ops guide §4): reaffirm files nothing
on a mismatch, so each needs either a dispatch (if you suspect the
*claim* was right and the world wrong) or a human retraction (if the
claim is simply a superseded snapshot — the likely verdict for most of
this pool, same "resolved by succession" shape as (c)). Nothing here
was caused by the migration; it inherited them.

## (e) The R11 monthly hand-audit (~2026-08-08) — new first item

The audit due around 2026-08-08 (roadmap-v3 R11, first window) now
opens with `docs/governance/gate-metrics.md`: read the registry table,
re-pull the instrument values, and append minutes. The 2026-08-02
first-review minutes there are the baseline to diff against. Zero other
ceremony changes (ADR-047 decision 3).

## Post-commit note — RESOLVED 2026-08-02 by the closing session

The P6 release bump did stale the previous sentinel generation as this
note predicted; the closing session filed and citation-swapped the
successors the same day, and an independent verifier session
(s-verifier-p6-pins) agreed all three: the ADR-series sentinel then
counting 001–047 (that chain ended 2026-08-16 when the corpus was archived),
tr-010f7e96 (explainer Scope at v0.9.31), and the check-truth gate
sentinel then pinned at the v0.9.31 lockstep line (current link in that
chain: tr-84a9a3e3). The three staled intermediates were appended
to the (c) retraction block above. Nothing further is owed here; the
standing rule stays: every release bump re-runs this succession
ceremony from the committing session.
