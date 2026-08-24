# Registers — the index of this repository's administered lists

> Reader: anyone asking "where is X recorded, and what would tell me the
> record has gone stale?" | Enables: finding the register that owns a kind
> of item, and naming the mechanism that measures its currency | Update-trigger:
> a register is added, moved or retired, or the mechanism that measures a
> register's currency changes (then re-run `instruments/register-index.py`)

## The index is itself an administered item

ISO/IEC 11179 makes one move this file borrows wholesale: **the registry is
registered**. A metadata registry is not a privileged vantage point outside
the corpus it describes — it is another administered item, with an owner, a
status, and a decay mode of its own. An index that lists nine registers and
is itself swept by nothing is a tenth register, unadministered, and it is
the one most likely to rot: it is read at the start of a session and edited
at the end of a different one.

So this file carries a row for itself, and `instruments/register-index.py`
sweeps it like any other register — every location below must exist on disk,
and every live document under `docs/` must fall inside some register's
location or be recorded as a known gap.

## What the last column is, and is not

**"Currency evidence" is not a claim that a register is fresh.** It names
what freshness is *measured by* — the gate, sweep, hash file or review slot
that would notice staleness, and where its finding surfaces. A register whose
currency evidence is "none" is not thereby stale; it is a register whose
staleness nothing would report, which is the strictly worse condition and the
reason this column exists at all.

## The registers

| register | purpose | location | status | currency evidence |
|----------|---------|----------|--------|-------------------|
| index | the registers themselves (ISO/IEC 11179: the registry is registered) | `docs/registers.md` | live | `instruments/register-index.py` — check (a) fails on a location that vanished, check (c) fails on live prose no register claims; baseline `.truth/register-index-baseline` |
| ADR | decisions | `docs/decisions` (live, 054+) and `docs/archive/adr` (frozen, 001–053) | live + frozen archive | `instruments/register-index.py` check (b): highest ADR file number vs. highest ADR cited in the roadmap; per-citation drift by `instruments/arm-index.py` prose pass against `.truth/arm-index-prose-hashes` (ADR-060) |
| INV | safety properties | Appendix A of `docs/truth-ledger-paper-v3.md` | live | `instruments/arm-index.py` reconciliation pass: a row naming no arm, an arm that does not exist, or an arm that does not point back, against `.truth/arm-index-paper-baseline`; link targets hashed in `.truth/arm-index-link-hashes` |
| arms | seeded faults | `template/scripts/truth-canary.sh` | live, ENFORCED species | `instruments/arm-index.py` subject rule (a canary family without a declared subject fails), exemptions in `.truth/arm-subject-opt-out` |
| roadmap | the plan | `docs/roadmap-v3.md` | living document | `instruments/register-index.py` check (b): the ADR gap between what the roadmap cites and what the decision register holds. Deliberately excluded from `.truth/citation-scope` — it is a history log and correctly cites ids that were live then |
| briefs | analyses | `docs/reviews` | dated records, never revised | filename date is the record; excluded from `.truth/citation-scope` on the same ruling as the roadmap, so a retraction is never blocked by a past review |
| ledger | claims | `.truth/claims.jsonl` | append-only, live | `scripts/check-truth.sh` INV-A prefix gate at commit (conditional on the hook actually running, ADR-025); per-claim currency by reproduce-on-read and TTL derived in the fold (ADR-057) |
| gates | Tier B intake gates and counted overrides | `docs/governance/gate-metrics.md` | live | its own per-row next-review date, read as the first item of the R11 monthly hand-audit (ADR-047); a gate enters PROPOSED with a metric or not at all |
| deferred designs | successor designs held behind a named trigger | `docs/growth-gate` | shelved, not built | each design names the trigger that would unshelve it; in `.truth/citation-scope`, so the ids it cites are judged live by `scripts/fact-health.sh` |
| prose corpus | which prose a reader is meant to act on today | `.truth/citation-scope` | live | `scripts/fact-health.sh` expands this file rather than carrying its own list, so the lockstep is structural, not a promise (wk-1d000ad4, 2026-08-23) |

## Three registers were added by the sweep that built this file

`gates`, `deferred designs` and `prose corpus` were not on the list this index
was commissioned from. They were found by asking the question the other way
round — not "what registers do we keep?" but "what live documents does no
register claim?" — which is check (c) below, and which is why check (c) exists
rather than being left to memory.

## What this index does not do

It does not judge whether a register's *contents* are correct, and it does not
promise that the mechanisms in the last column are running. It maps items to
the register that owns them and names the instrument that would report decay.
Whether that instrument is wired into a gate is a separate question, answered
per instrument in `docs/governance/gate-metrics.md` and by
`scripts/gate-reachability.sh`.
