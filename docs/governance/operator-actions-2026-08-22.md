# Operator actions — rulings of 2026-08-22

> Reader: the human operator executing the G12 half of the rulings | Enables: running the retractions and cancellations agents may not run, in an order that will not refuse | Update-trigger: an action here is executed, or a ruling changes

Every id below sits inside a fenced block on purpose. `scripts/fact-health.sh`
does not read fenced content as a citation, so this page can name ids that are
about to die without the ADR-036 tombstone gate refusing their retraction and
without the sweep turning red afterwards.

Agents executed rulings 2, 5, 7, 8a and 8b. What remains is G12: retraction and
issue cancellation are human-only and no agent flag opens them.

## Order matters

ADR-049 refuses `--cause restated` without `--successor`, so successors must
exist before their predecessors die. They do: filed 2026-08-21/22, listed under
ruling 8 below. Run **8 before 4** if you want the ledger consistent at every
intermediate step.

## Ruling 3 — cancel the mis-framed issue

Replaced by `wk-5cbbc965`, which asks the scope question this one mis-attributed
to a single instrument.

```
TRUTH_HUMAN=1 TRUTH_HUMAN_ACK=wk-1bbb48c2 \
  python3 template/scripts/truth done wk-1bbb48c2 --cancel \
  --basis "operator ruling 2026-08-22: mis-framed -- blamed field-consumers for a gap that was systemic; replaced by wk-5cbbc965, which asks whether the ADR-047 registry covers battery arms at all"
```

## Ruling 8 (final part) — retract the count-literal claim

Its successors are already filed and reproduce: `tr-7f8d4a83` (the arm set,
with no count literal and a form-complete capsule) and `tr-d2aa8783` (the
fail-closed guard, positive form).

```
TRUTH_HUMAN=1 TRUTH_HUMAN_ACK=tr-38d32bc7 \
  python3 template/scripts/truth verdict tr-38d32bc7 retracted \
  --cause restated --successor tr-7f8d4a83 \
  --basis "operator ruling 2026-08-22: sentence carried a count literal (TEN) and its capsule was blind to the Nb naming form introduced after filing, so it reproduced green for four days while false"
```

An earlier guard attempt, self-diverged by its author minutes after filing
because its capsule exited 1 in its own healthy state, can die with it:

```
TRUTH_HUMAN=1 TRUTH_HUMAN_ACK=tr-858be922 \
  python3 template/scripts/truth verdict tr-858be922 retracted \
  --cause restated --successor tr-d2aa8783 \
  --basis "operator ruling 2026-08-22: complement-emitting form exits 1 when conforming, so the healthy reading was indistinguishable from an unreadable file; replaced by the positive wc -l form"
```

## Ruling 4 — the retraction backlog

### Three pilot pairs, both halves live

Successors are independently verified; predecessors were never retracted, so
the ledger currently holds three live duplicate pairs.

```
TRUTH_HUMAN=1 TRUTH_HUMAN_ACK=tr-f9318142 python3 template/scripts/truth verdict tr-f9318142 retracted --cause restated --successor tr-99d9b476 --basis "operator ruling 2026-08-22: pilot pair closed, successor independently verified"
TRUTH_HUMAN=1 TRUTH_HUMAN_ACK=tr-7c4966ad python3 template/scripts/truth verdict tr-7c4966ad retracted --cause restated --successor tr-bc8bb5c8 --basis "operator ruling 2026-08-22: pilot pair closed, successor independently verified"
TRUTH_HUMAN=1 TRUTH_HUMAN_ACK=tr-66b04399 python3 template/scripts/truth verdict tr-66b04399 retracted --cause restated --successor tr-a3a63432 --basis "operator ruling 2026-08-22: pilot pair closed, successor independently verified"
```

### Ten orphans naming a path that no longer exists

Their subject, `docs/adr/truth/`, moved to `docs/archive/adr/` in step 1.3.
They cannot be re-judged, because what they describe is gone. `--cause expired`
per the ruling; no successor, and none is owed — the world moved, the claim did
not become wrong so much as unanswerable.

```
for id in tr-58e5fce2 tr-b1802f6d tr-1089dc18 tr-44dafee6 tr-d1d7b77a \
          tr-3fb81974 tr-1ee2b698 tr-14394281 tr-88f20f3f tr-126f0629; do
  TRUTH_HUMAN=1 TRUTH_HUMAN_ACK=$id \
    python3 template/scripts/truth verdict $id retracted --cause expired \
    --basis "operator ruling 2026-08-22: subject path docs/adr/truth/ was archived to docs/archive/adr/ in step 1.3, so this claim is unanswerable rather than false"
done
```

Verify the loop before trusting it — the human gate wants an id-specific ack per
record, and a loop that silently skipped one would leave the backlog looking
shorter than it is:

```
python3 template/scripts/truth list --json | python3 -c "import json,sys; print(sum(1 for r in json.load(sys.stdin) if r['status']=='diverged' and 'docs/adr/truth/' in r.get('text','')))"
```

Ten before, zero after.

### The whisper sentinel and its file

Retract together, per the ruling. The claim is a `sha256sum` sentinel over
`.pi/extensions/truth-whisper.ts`, whose harness the operator has said is
unused; killing the claim alone leaves an unwatched file, killing the file
alone leaves a sentinel over nothing.

```
TRUTH_HUMAN=1 TRUTH_HUMAN_ACK=tr-599e7561 python3 template/scripts/truth verdict tr-599e7561 retracted --cause expired --basis "operator ruling 2026-08-22: the pi harness is not in use; sentinel retired together with the file it watched"
TRUTH_HUMAN=1 TRUTH_HUMAN_ACK=tr-c5ff452c python3 template/scripts/truth verdict tr-c5ff452c retracted --cause expired --basis "operator ruling 2026-08-22: retired alongside the pi harness"
git rm .pi/extensions/truth-whisper.ts
```

`tr-599e7561` is `unverified`, not `live` — it never had a verifier. Retracting
an unverified claim is legitimate and the fold accepts it; noted only so the
status in the output is not a surprise.

## After the batch

```
python3 template/scripts/truth validate
python3 template/scripts/truth reproduce
bash scripts/fact-health.sh
make battery
```

`reproduce` should examine fewer live claims than before and still report zero
capsule-stale. `fact-health` should stay at zero failures: every id retracted
here was checked against the citation scope first, and the two that were cited
in living prose are not in this batch.
