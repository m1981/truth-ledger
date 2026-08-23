# ADR-059: asynchronous semantic audit — extract the justifications, judge them outside

Status: **PROPOSED** (2026-08-23, agent-authored). Implemented in the same
sitting; not yet independently reviewed. Only the L1 half — the extractor —
is built. The L2 half (the CI job that reads the sentences and the criteria
it judges them by) is deliberately not in this repository, and is not
specified by this record.

Date: 2026-08-23

Cites: ADR-007 (`--scope-ok`), ADR-035 (`--exit-ok`), ADR-036
(`--orphan-ok`), ADR-037 (`--generated-ok`), ADR-046 (Tier C), ADR-051
(`--refresh-evidence`), ADR-057 (read-time TTL — the extractor folds with a
clock so an expired override is not extracted as load-bearing), FAZA 3
(`--paths-ok`).

## Context

Every override in this system is admitted on a **sentence**. `--scope-ok`
says why a quantifier may stand. `--paths-ok` says why a freehand watch set
may exceed the budget. `--generated-ok` says why a generated artifact may be
watched, `--exit-ok` why a failing probe still proves something,
`--orphan-ok` why citations may be left dangling, and ADR-051's
`--refresh-evidence` why a moved output is still the same fact.

The gates check that a sentence **exists** and is non-empty. Nothing in this
repository has ever checked whether it **means** anything. To every mechanism
here, `"reviewed"`, `"ok"`, `"see above"` and a genuine argument are the same
value: a non-empty string.

That check needs a reader. EPI-305 says the machine measures and the human
judges — and a language model asked to rule on an argument is a judge, not a
measurement. A "semantic gate" running a model inside the CLI and refusing a
filing on its output would be L1 grading meaning, which is the one thing L1
cannot do honestly, and would make every intake depend on a non-deterministic
remote service.

## Decision

Split it. `instruments/semantic-audit.py` is the L1 half and its entire job
is to hand L2 the text.

1. **Extract, never judge.** Emits justification sentences as a flat JSON
   array on stdout. Six types: `scope_basis`, `paths_basis`,
   `generated_ok_basis`, `evidence_exit_basis` (claim payload);
   `evidence_refresh` and `orphan_basis` (verdict payload). Which claims
   they are read from is decision 3, and it is not one rule for all six.
2. **NO NETWORK I/O.** Not `requests`, not `http.client`, not `urllib`, not
   `socket`. This is a hard contract with a structural pin, not a
   preference: `TestTierCInstruments` fails if the module names a transport
   outside its own docstring. An extractor that grew a `requests.post`
   would pass every behavioural assertion while shipping this repository's
   justification text to a third party, and nothing else would notice.
   The send lives in CI, where a human wrote the workflow and can see what
   leaves the machine.
3. **Two scopes, by operator ruling.** ACTIVE claims (`live`,
   `unverified`) for the sentences that defend a fact still in use — a
   diverged or retracted claim's `scope_basis` is history, and asking an
   LLM to judge it spends tokens on a finding no one can act on. **Plus
   RETRACTED claims, for `orphan_basis` alone.**

   That one sentence is different in kind from the other five, which is
   why it survives its subject's death. The others defend a FACT that is
   still being relied on. `orphan_basis` defends a deliberate ACT —
   leaving citations dangling at the moment of retraction. The act is
   permanent, the dangling references are still in the corpus, and *"why
   was it acceptable to orphan them"* only becomes answerable after the
   retraction has happened. It is also unauditable under any active-only
   scope: `validate_events` refuses the field on a non-retracted verdict,
   so the field could never appear on a live claim at all.

   The branch is keyed on the claim's **status**, not on the field being
   present. A raw-appended `orphan_basis` on a claim nobody retracted is
   an argument about an act that never happened, and must not reach L2.
4. **Rows carry `id`, `record`, `type`, `basis`.** `id` is the claim the
   sentence defends — what an auditor acts on. `record` is added beyond the
   minimum because a claim can carry several verdicts, and without it two
   `evidence_refresh` sentences on one claim are indistinguishable.
5. **Deterministic.** Sorted by `(id, type, record)`, so a CI diff means the
   ledger moved, not that a dict iterated differently.
6. **Census on stderr.** Per-type counts, including the types reading zero.
   The battery's law — every arm reports what it examined — applies to an
   extractor, and a type that yields 0 rows forever is a dark arm nobody
   sees unless the number is printed.

## Consequences

**A dark type, found and then fixed rather than shipped.** The first cut
of this extractor read active claims only, which made `orphan_basis` a
**guaranteed zero on every ledger** — a field wired to nothing, invisible
because nothing prints it. The census was what made it visible; the
operator then ruled the scope widened rather than the field dropped, which
is decision 3 above. The census is also how that ruling stays checkable:
if this number returns to a permanent 0, the retracted branch has stopped
firing.

**Measured on this ledger** (2026-08-23): 11 sentences — `scope_basis=5`,
`evidence_refresh=3`, `paths_basis=2`, `orphan_basis=1`,
`generated_ok_basis=0`, `evidence_exit_basis=0`. The two remaining zeros
are honest: no active claim currently carries a `--generated-ok` or
`--exit-ok` override.

**Not specified here.** What L2 asks the model, what counts as a failing
sentence, and whether the result blocks anything. Those are L2's, and
writing them into this repository would be L1 specifying its own examiner.

## Evidence

    python3 instruments/semantic-audit.py                 # 11 rows, exit 0
    python3 template/scripts/test-integrations.py         # 29 tests, OK

The gate arm was verified by seeding faults and watching each go red before
it was kept (*do not add an arm you have not seen fail*):

| seeded fault | caught by |
|---|---|
| `import urllib.request` smuggled in | the transport pin |
| scope widened to dead claims | the sandbox red proof (a diverged claim's `scope_basis` must disappear) |
| sort removed | the byte-identical-across-runs assertion |
| retracted branch disabled | the orphan red proof (a retraction's `orphan_basis` must be extracted) |
| `ORPHAN_STATUSES` widened to `diverged` | the forgery proof: a raw-appended `orphan_basis` on a non-retracted claim must not reach the audit |

The last two are the arms that did not exist in the first cut. The fifth
was added because the extractor's own comment claimed the status guard was
load-bearing, and nothing exercised it — the seeded widening passed a green
suite until the forgery fixture was added.
