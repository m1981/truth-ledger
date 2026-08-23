# ADR-057: read-time TTL — time is a function of the question, not an event in the log

Status: **PROPOSED** (2026-08-23, agent-authored). Implemented in the same
sitting; not yet independently reviewed. The suites, the canary and the
Tier C instruments are green (numbers below), which this repository has
ruled repeatedly is *not* sufficient evidence — see ADR-056's status line
for the last time that distinction was drawn and why.

Date: 2026-08-23

Amends: **ADR-019** (TTL expiry semantics), frozen at
`docs/archive/adr/019-ttl-expiry-semantics.md`. ADR-019's two decisions are
untouched — the shelf life counts from the claim's own `ts`, and the
boundary is strict — but its *mechanism* is replaced: it ratified
`_ttl_expired` plus `cmd_invalidate_scan` as "the sole clock reader", and
there is now no clock reader at all.

Cites: ADR-015 (fixed-width aware timestamps), ADR-016 (the `(ts, id)`
total order the fold is confluent under), ADR-030 (`reaffirm`, retired in
refactor step 2.6), ADR-032 (`--scope-ok` default decay, which rides the
expiry path), ADR-046 (Tier C), the Reproduce-on-Read refactor steps
2.4–2.6 (which retired the path/anchor invalidators and narrowed
`invalidate-scan` to `ttl-scan`).

## Context

The Reproduce-on-Read refactor removed both syntactic invalidators, and one
writer survived it: `ttl-scan`. The argument for keeping it was sound and
is repeated verbatim in the code it left behind — TTL expiry is the one
thing `truth reproduce` provably cannot detect, because a claim whose shelf
life runs out today reproduces perfectly today.

That argument justifies keeping the *fact*. It was read as justifying the
*record*, and those are different claims. The reason the record existed was
older: ADR-019 held that a fold reading wall-time would destroy purity and
confluence, so the clock had to be materialized by a scan and the fold
would then derive `stale` from the resulting record.

The premise is false, and the code now says so. A clock passed **as an
argument** leaves `fold` a pure function of `(events, now_dt)`: same inputs,
same output, in any input order. Confluence was never threatened by reading
a clock; it was threatened by reading a *hidden* one.

What the materialization actually cost:

* a verb, its argparse entry, and its place in `WRITE_VERBS`;
* a CI job step holding `permissions: contents: write` — an L1 instrument
  with commit access to the branch it measures, which is the L1/L2 leak
  this whole layer exists to refuse;
* a bot identity, its commit, its push, a `[skip ci]` marker and an actor
  guard, all of which existed solely to stop that one write looping;
* a claim's status depending on whether anyone had run a scan, so that
  "is this fact still current" had the answer *it depends who asked and
  when they last swept* rather than *arithmetic*.

## Decision

1. **`fold(events, now_dt=None)`.** When `now_dt` is given, every claim in
   `ACTIVE_STATUSES` whose `ts + ttl_days` has strictly passed derives
   `stale`. When it is `None`, TTL is not evaluated at all.
2. **`kernel.ttl_expiry(claim_record, now_dt)`** is the single place the
   arithmetic lives — successor to `policy._ttl_expired`, with ADR-019's
   two decisions preserved verbatim.
3. **The `invalidation` record kind is wholly inert for status.** Step 2.5
   had already made the path arm inert; the TTL arm joins it. The ~1997
   existing records stay in the ledger and stay readable (EPI-501, J-012).
4. **`ttl-scan`, `INVALIDATORS`, `decide_invalidation` and `_ttl_expired`
   are removed.** The strategy seam is removed too, rather than left empty:
   an empty tuple advertises a seat for exactly the design this record
   rejects.
5. **`status_ts` for a derived `stale` is the expiry instant**
   (`claim ts + ttl_days`), never `now`. It is therefore derived from the
   record, so two readers asking at different times agree on it, and
   `age_days`/`queue_rows` price the queue from when the fact expired
   rather than reporting a long-dead claim as zero days old.
6. **`baseline_snapshot` and `blast_report` stay clockless.** A baseline
   whose whole contract is byte-identical output for one ledger must not
   diff against itself overnight.

## Consequences

**Wanted.** Expiry is visible on every read with no scan, no record, no
commit and no bot. `truth-scan.yml` drops to `permissions: contents: read`.
A replayed or forged expiry record can no longer stale a claim the clock
says is fresh.

**Accepted.** `override_report.decay_expiries` becomes a HISTORICAL figure:
the ADR-032 judgment still expires — the fold says so — but nothing counts
the event of it expiring, because there is no event. `evidence.ttl_staleness`
becomes a historical reader and is labelled as one in its docstring; it had
no production consumer, its only one (`reaffirm`) having gone in step 2.6.

**Guarded.** `fold` is now on every read path *and* on `truth validate`'s
path, so a malformed `ttl_days` or a tz-naive `ts` must not raise from
inside it — the sensor that reports a malformation may not be the one the
malformation silences. `ttl_expiry` abstains on exactly the shapes
`validate_events` already refuses.

**Breaking for consumers — but less than it looks, and the measurement
matters.** `ttl-scan` never shipped in a tagged release. The newest tag is
`v0.9.38`, whose CLI registers `invalidate-scan` and `reaffirm`; step 2.6
narrowed the first to `ttl-scan` and retired the second in `c0ff7f3`, which
is unreleased. So `ttl-scan` was born and died entirely inside the
unreleased window, and **no consumer has ever been able to call it.**

What a consumer upgrading from `v0.9.38` actually sees is step 2.6's
break, not this record's: `invalidate-scan` and `reaffirm` are gone, and
nothing replaced the first. This record removes a verb that existed only
between two commits.

No alias is offered for any of them. An alias would keep alive the idea
that expiry is something you trigger, which is the idea being retired.

## Evidence

    python3 template/scripts/test-truth-core.py          # 538 tests, OK
    python3 template/scripts/test-truth-v04.py           # 13 tests, OK
    python3 template/scripts/test-integrations.py        # 29 tests, OK
    bash template/scripts/truth-canary.sh                # 290 caught, 0 missed

Canary arms re-pointed rather than deleted: FAULT D's second half asserted
"the fold reads no clock" and now asserts the two properties that survive —
the expiry is visible, and **the ledger does not grow** across reads; FAULT
SD4 proved *which* mechanism staled a claim by grepping the emitted record's
`reason_code`, and now proves it from the other side (no invalidation record
exists for the claim, and the negative control rules out "everything went
stale").

`TestReadTimeTTL` replaces `TestInvalidation` arm for arm, including a
positive pin on the removal itself (`decide_invalidation`, `INVALIDATORS`,
`_ttl_expired` and the `ttl-scan` verb must all be absent).

## Residual

**The version was bumped to v0.10.0 by operator ruling (2026-08-23).**
All six ADR-026 lockstep surfaces state `v0.10.0`; the schema `$id` is
untouched at `truth-ledger-record.v0.18`, because no record SHAPE changed.

Checking what the last version actually was turned up the real state:
`v0.9.38` is the newest tag and 122 commits sit between it and this work,
of which 23 touch code a consumer receives. The delta is not this record --
it carries the Reproduce-on-Read refactor's later steps, ADR-041, FAZA 3
and FAZA 4.

The CHANGELOG entry for v0.10.0 now covers them, written from the commit
messages and ADRs of the people who did the work rather than from a code
read, with every figure quoted from its source. The two changes left
undescribed are named there rather than omitted.

**Cutting the tag is still an operator act**, and one thing argues for
doing it deliberately rather than promptly: none of the work in this
release except ADR-054/055/056 has an accepted decision record, and this
record plus ADR-058 and ADR-059 are all PROPOSED, none independently
reviewed. The release battery WARNs while the stated version has no tag,
which is the correct state to sit in until someone decides those three
statuses.
