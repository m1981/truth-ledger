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
every row must name a location the sweep can actually read, and every live
document under `docs/` must fall inside some register's location or be
recorded as a known gap.

**That sweep is now gated**, which it was not when this file was written:
`template/scripts/test-integrations.py` (`TestTierCInstruments`) runs it
against this repository and against throwaway trees that seed each failure
condition. Until that landed, this section asserted a sweep whose own
docstring said `Gate: NONE yet` — an index claiming administration it did
not have, which is the exact decay it exists to report.

**Every check runs in both directions.** The instrument was defeated twice
by the same shape — a check that walks from A to B and never walks back —
so the rule is now stated in its docstring and each check states its
reverse: a location named with nothing there AND a row naming nothing; a
filed decision the plan never mentions AND an id the plan names that has no
record; an uncovered document AND a baseline entry whose finding has gone.

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
| index | the registers themselves (ISO/IEC 11179: the registry is registered) | `docs/registers.md` | live | `instruments/register-index.py`, gated by `template/scripts/test-integrations.py` — check (a) fails on a location that vanished, on a row naming no readable location, on a location that is absolute or escapes the repo, and on a `currency evidence` cell that is empty or names a path that is not there; check (c) fails on live prose no register claims; baseline `.truth/register-index-baseline` |
| ADR | decisions | `docs/decisions` (live, 054+) and `docs/archive/adr` (frozen, 001–053) | live + frozen archive | `instruments/register-index.py` check (b), in three directions: every id with a file here is mentioned somewhere in the roadmap (`adr-unaccounted:`), every id the roadmap names has a file (`adr-phantom:`), and the number space has no holes (`adr-gap:` — the space is never restarted and a superseded record is superseded in place, so a hole is a record that vanished). A markdown file here whose name does not parse as `nnn-slug.md`, and a missing ADR directory, are each findings rather than a silently smaller reading. Baselined in `.truth/register-index-baseline`; per-citation drift by `instruments/arm-index.py` prose pass against `.truth/arm-index-prose-hashes` (ADR-060) |
| INV | safety properties | Appendix A of `docs/truth-ledger-paper-v3.md` | live | `instruments/arm-index.py` reconciliation pass: a row naming no arm, an arm that does not exist, or an arm that does not point back, against `.truth/arm-index-paper-baseline`; link targets hashed in `.truth/arm-index-link-hashes` |
| arms | seeded faults | `template/scripts/truth-canary.sh` | live, ENFORCED species | `instruments/arm-index.py` subject rule (a canary family without a declared subject fails), exemptions in `.truth/arm-subject-opt-out` |
| roadmap | the plan | `docs/roadmap-v3.md` | living document | `instruments/register-index.py` check (b): ADR ACCOUNTING — which filed decisions this plan mentions nowhere, in any tense, AND which ids it names that have no record. Not recency: the ids it cites are not required to be the newest, because it is a history log and correctly cites ids that were live then, which is also why it is deliberately excluded from `.truth/citation-scope`. Today's backlog is frozen in `.truth/register-index-baseline` so the NEXT divergence fails. The mirror rule distinguishes the two ways a baselined entry can stop being a finding: the roadmap now mentions it (resolved — drop the line) versus the decision record no longer exists (a REGRESSION — restore it). Reporting the second as the first made the prescribed remedy the regression itself |
| briefs | analyses | `docs/reviews` | dated records, never revised | filename date is the record; excluded from `.truth/citation-scope` on the same ruling as the roadmap, so a retraction is never blocked by a past review |
| ledger | claims | `.truth/claims.jsonl` | append-only, live | `scripts/check-truth.sh` INV-A prefix gate at commit (conditional on the hook actually running, ADR-025); per-claim currency by reproduce-on-read and TTL derived in the fold (ADR-057) |
| gates | Tier B intake gates and counted overrides | `docs/governance/gate-metrics.md` | live | its own per-row next-review date, read as the first item of the R11 monthly hand-audit (ADR-047); a gate enters PROPOSED with a metric or not at all |
| deferred designs | successor designs held behind a named trigger | `docs/growth-gate` | shelved, not built | each design names the trigger that would unshelve it; in `.truth/citation-scope`, so the ids it cites are judged live by `scripts/fact-health.sh` |
| waivers | the gates that can be lifted, by the carriers that register can enumerate — **NOT TOTAL**, and it says so in its own first section | `docs/waivers.md` | live; membership gated per carrier, contents DECLARED | `instruments/waiver-index.py`, gated by `template/scripts/test-integrations.py`. Membership is checked BOTH ways and is total **per harvested carrier** — every CLI flag, every environment name any source reads, and every file in `.truth/` must be a waiver row or an entry in `.truth/waiver-not-an-override` with a finished reason. It is **NOT** total over bypasses: `syntax`, `config` and `code` carry waivers no source enumerates, are recorded by hand, and are checked in neither direction. The four content columns (gate lifted, stamp, decays, governing record) are held by reading; item 0b is DECLARED, not DONE. No baseline — anything unclassified fails rather than waiting |
| scope | the boundary this system declares for itself | `docs/scope.md` | **ACCEPTED** 2026-08-26 by operator ruling; drafted by an agent 2026-08-25 | **none, and deliberately none.** This is the only document here that no measurement produced: a boundary cannot be measured from inside, so it is declared. Gating it would make the sweep enforce a proposal nobody has ruled on, and would let this register's own scope be set by an unreviewed file. Its currency is the operator's ruling, which landed 2026-08-26; the Status line carries it, and a later change to the refusals needs a new ruling on the same line rather than an edit under the old one. It has a ROW rather than a baseline entry on purpose — a baseline is for a finding nobody has got to yet, and hiding the document that states this system's limits inside an excuse file would be an irony with no room here |
| assurance | the claim every instrument is evidence FOR, and the defeat condition of each leaf | `docs/assurance.md` | **PROPOSED** 2026-08-28, agent-authored | **none yet, and the gap is named rather than excused.** The check this row wants is a two-way sweep in the shape `waiver-index` already uses: every DETECTOR in the `docs/governance/catch-log.md` census must appear as evidence under some leaf of `docs/assurance.md`, and every leaf must name a detector that exists -- an instrument serving no claim and a claim resting on no instrument are the two failures this register is for. Reporters are excluded by construction: the census classifies them from their own docstrings and a reporter is not evidence for anything. Until that sweep exists the case is held by reading, which is exactly the state `docs/waivers.md` item 0b is in, and it is DECLARED here for the same reason. Currency is the operator's ruling on the Status line |
| architect's crib | the reasoning procedure, its one failure shape, and what this system is missing | `docs/governance/architects-crib.md` | **PROPOSED** 2026-08-26, operator-side | **none, and deliberately none.** Orientation is not a finding: no measurement produced this file and none can refute it, so a gate would be measuring nothing (ADR-042 rule 2). It sits beside `docs/scope.md` in kind — both are declared rather than harvested — but where scope states the boundary, this states the reasoning order used to work inside it, and the practice this system is compared against. Its currency is an operator ruling on the Status line, the same convention scope uses. A ROW rather than a baseline entry, for the same reason: a baseline is for a finding nobody has got to yet |
| catches | what a mechanism stopped, and what it did not | `docs/governance/catch-log.md` | live, operator-side | **none, deliberately.** This is the operator's instrument and it answers a VALIDATION question — did the apparatus pay — which paper §0 places outside what the ledger can decide. It has no gate, no baseline and no instrument by design: rule 1 forbids deleting entries, so the mirror rule that governs every `.truth/` baseline must not be imported here. Its currency is that somebody adds an entry the day it happens; rule 5 marks a late one as testimony rather than evidence |
| prose corpus | which prose a reader is meant to act on today | `.truth/citation-scope` | live | `scripts/fact-health.sh` expands this file rather than carrying its own list, so the lockstep is structural, not a promise (wk-1d000ad4, 2026-08-23) |

## Three registers were added by the sweep that built this file

`gates`, `deferred designs` and `prose corpus` were not on the list this index
was commissioned from. They were found by asking the question the other way
round — not "what registers do we keep?" but "what live documents does no
register claim?" — which is check (c) below, and which is why check (c) exists
rather than being left to memory.

## What this index does not do

It does not judge whether a register's *contents* are correct. It maps items
to the register that owns them and names the instrument that would report
decay.

The last column is checked as far as it can be and no further, and the line
is worth stating because the column's whole subject is what is and is not
measured. **Checked:** the cell is not empty, and every backticked token in
it containing a slash is a path that exists. **Not checked:** whether the
mechanism a cell names is wired into any gate, or ran, or would report what
the cell says it reports. That is a separate question, answered per
instrument in `docs/governance/gate-metrics.md` and by
`scripts/gate-reachability.sh`. A cell can therefore name a live path and
still be a promise nobody keeps — which is why the paragraph above says
which of these registers' sweeps is itself gated.
