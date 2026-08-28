# Operator actions — rulings of 2026-08-28: cut the ritual, keep the mechanics

> Reader: anyone deciding whether to dispatch a verifier, extend the whisper,
> or add apparatus about the apparatus | Enables: acting on the ceremony-cut
> rulings without re-litigating them, and measuring whether the cut worked |
> Update-trigger: an execution item below lands, or the 2026-09-28 re-reading
> of the prose-tail metric

The operator accepted, verbatim, a six-point recommendation set drafted in
session on 2026-08-28 ("jestem za 1-5" plus the three follow-ups 6-8), and
directed execution without pausing between steps. The recommendations rest on
readings this repository itself produced; each is quoted below with its date
and the command that regenerates it, per the AGENTS.md quoting rule.

## The readings these rulings stand on

- **Verification hit rate ~1.5%** (9 finding verdicts / 606 filed), window 2
  of the paper, 2026-07-20. Regenerate:
  `python3 scripts/truth stats --json` (verdicts section), against
  `docs/paper-data/stats-snapshot-2026-07-20.json` for the historical figure.
- **22.6 claims named per edit** by the whisper, J-040 recount, 2026-08-18,
  recorded in `.truth/watch-policies` header. Regenerate: the J-040 procedure
  (per-CLAIM line count over the last 200 commits).
- **Prose-only decision tail**: 7 of the 10 newest decision records carry
  zero ledger records at HEAD, 2026-08-28. Regenerate:

```
for a in ADR-054 ADR-055 ADR-056 ADR-057 ADR-058 ADR-059 ADR-060 ADR-061 ADR-062 ADR-063; do
  printf "%s: %s\n" "$a" "$(grep -c "$a" .truth/claims.jsonl)"; done
```

  Reading of 2026-08-28: 054=0, 055=0, 056=0, **057=2**, 058=0, 059=0,
  060=0, 061=0, **062=4**, **063=4**. The external labels-deps scan
  (commit `74e8aab`, 2026-08) first surfaced this as "50 declared labels no
  ledger record names"; the figure above is the HEAD re-verification of its
  load-bearing subset.

## Ruling 1 — routine verifier dispatches END

`scripts/truth reproduce` (and the `truth health` projection) is the standing
recheck. A fresh-context verifier is dispatched in exactly three situations:

1. the claim is **P0**;
2. the claim just went **diverged** and the queue needs triage;
3. a decision is about to be taken **on** the claim (verify at point of use —
   the AGENTS.md line "file what you verify" already implies its dual:
   verify what you are about to rely on).

Everything else: file, let `reproduce` watch it, and stop. Basis: at a 1.5%
hit rate, roughly 98.5% of verdict labor re-confirms what was already
believed; v0.10.0 already removed `invalidate-scan`/`reaffirm` on the same
argument — this ruling finishes that line for the human/agent half.

## Ruling 2 — P2 claims carry NO verdict ceremony

A P2 claim is a record with a recipe. It is born unverified, `reproduce`
guards its capsule, and that is its whole lifecycle unless it diverges or
someone is about to rely on it (ruling 1 cases). Dispatching a verifier for a
fresh self-filed P2 is the documented anti-pattern now.

## Ruling 3 — whisper: P0 speaks, P1/P2 are one aggregate line

The PreToolUse whisper (`scripts/truth-whisper.py`, meta-repo policy per
ADR-005/ADR-003) prints full WATCHED-BY lines **only for P0 claims**; P1 and
P2 hits collapse into a single aggregate line with counts and a pointer to
`scripts/truth impact <path>` for the full view. The deny stage is untouched
— it is a gate, not a notice.

This ruling **closes the fatigue half of the ADR-005 adoption gate**
(work item `wk-5473af07`): the gate asked for evidence that the whisper "is
read, not tuned out"; at 22.6 claims named per edit (J-040) it cannot be
read, so the answer is structural, not a further measurement. The trial's
S1-S3 behavioral arms had already passed (2026-07-12).

## Ruling 4 — meta-apparatus freeze

No new registers, instruments, or gates **about the apparatus itself** are
built. The ADR-047 deletion criterion in `docs/governance/gate-metrics.md`
applies as written and is to be applied aggressively at the monthly review:
a gate or instrument that has caught nothing by its review date is a removal
candidate, not a keepsake. Existing probation dates stand. The evidential
core — capsules, tripwires, intake gates, the fold, `reproduce`, the commit
gate — is explicitly outside this freeze and outside any cut.

## Ruling 5 — selective backfill of the prose tail

One claim per **shipped** mechanism among ADR-054..061 — a mechanism with
code in the tree and a gate that exercises it. Where nothing mechanical
shipped (doctrine-only records), no claim is owed and none is filed; a
forced claim about prose would be the ADR-060 recital problem in a costume.
Filed at P1/P2 under rulings 1-2: recipe + `reproduce`, no dispatch.

## Ruling 6 — labels-deps is the orientation layer, and never a gate

Agent orientation ("what neighbors what") goes through the external
labels-deps scan artifact (`brief`/`impact`/`find`), pull-based, on demand.
Fact checking ("is this still true") stays with `scripts/truth`. labels-deps
output is wired into **no** gate — its own ADR-002 refuses verdicts, and
ruling 4 refuses the temptation from this side.

## The success metric

The prose-tail reading above is the baseline. Re-run the fenced command at
the 2026-09-28 review: decisions accepted after 2026-08-28 should carry at
least one ledger record each within a week of acceptance. If the tail is
still growing, the ceremony cut was insufficient and the next cut goes
deeper (candidates: intake advisory volume, the per-claim override
sentences).

## Execution log (this session, 2026-08-28)

- [x] Ruling 3: whisper aggregation shipped in `scripts/truth-whisper.py`;
      red-then-green demonstrated in `TestClaudeWhisperHook` (ADR-061 form:
      the failing run's message shows the old verbatim injection).
- [x] Ruling 3: `wk-5473af07` closed with claim-at-death (the claim id is
      in the closing ledger records of 2026-08-28).
- [x] Rulings 1-2: dispatch policy recorded here; AGENTS.md points at this
      file instead of restating it.
- [x] Ruling 5: recon over ADR-054..061 (seven read-only agents; capsules
      re-run by the filing session before filing). Seven claims filed:
      054/055/056/059/060 as shipped-mechanism claims, 058 as a dark-gate
      claim (the script is wired to nothing — itself a finding), 061 as a
      NORM-status claim (doctrine-only, no gate of its own, and none owed).
- [x] Ruling 6: orientation line added beside the AGENTS.md fact-checking
      line.

A box above is checked only after the thing it names exists on disk or in
the ledger; this file was created with every box empty and the boxes were
checked in the same session, after each landing.
