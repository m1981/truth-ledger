# Waivers — every gate in this system that can be lifted, and by what

> Reader: anyone asking "which refusals can be bypassed, on what basis, and how
> many bypasses are on record?" | Enables: reviewing the escape surface as a
> POPULATION rather than as independent flags | Update-trigger: any flag is
> added to or removed from the CLI (then re-run
> `instruments/waiver-index.py`, which will refuse until the new flag is
> classified)

## Why this register exists

Every other register here lists things that were *created*. This one lists the
places where a rule was *set aside*. It is the register whose absence is least
visible, because a waiver leaves a record only where somebody built one to
leave — and one of the ten below leaves nothing at all.

**No count in this file is authoritative.** Read them off
`python3 instruments/waiver-index.py`, which prints the escape surface, the
flag inventory and the population per stamp. Counts restated in prose are
exactly what this repository's one-home-per-fact rule forbids, and the first
draft of this file got three of them wrong.

DO-178C, IEC 61508 and ISO 26262 each require a deviation from a required
objective to be recorded with rationale, scope, owner and expiry, and require
the population of open deviations to be reviewed **as a population**. Before
this file there was no population — only independent flags.

## Two findings this register was built on

**1. "Every override in this system is admitted on a sentence" is false.** It
was the opening claim of ADR-059, repeated in `AGENTS.md` and in
`instruments/semantic-audit.py`. Six of the ten flags below take a `SENTENCE`.
Four take nothing, and they are not a random four:

> The six that carry a sentence lift a **quality-of-justification** gate: a
> quantifier wider than its evidence, a watch set over budget, a generated
> artifact watched, a positive claim on a failing probe, a retraction leaving
> citations dangling, an anchor advanced past a capsule that no longer
> reproduces.
>
> The four that carry nothing lift an **execution** gate: run an unscreened
> evidence command, close a work item without running its unscreened
> acceptance oracle, admit a near-duplicate over G8, skip the determinism
> double-run.

So the overrides with the largest blast radius are the ones admitted on a bare
boolean, and `instruments/semantic-audit.py` — the extractor built to hand
every override's rationale to an outside reader — is structurally blind to
them. Not through an oversight in its field list: there is no rationale to
extract. The L2 reader ADR-059 designs cannot tell "no override happened" from
"an override happened and said nothing", because both produce no row.

**2. `--single-run` is worse than the other three, and nothing had noticed.**
It skips the G6 determinism double-run — the check that catches a
non-deterministic evidence command before its output is frozen into a claim —
"accepting false-divergence risk", and it writes **no field whatsoever** into
the record. The other three at least leave `screened: false` or
`overridden_duplicates`. This one is invisible in the ledger, so its
population cannot be counted at all, by this instrument or any other. The
sweep prints that fact rather than printing a zero.

## The register

`admitted on` is a controlled vocabulary — exactly `SENTENCE` or `nothing` —
and is checked against the parser. See "What is checked" for the columns that
are not.

| flag | verbs | gate it lifts | admitted on | stamp on the record | decays | governing record |
|---|---|---|---|---|---|---|
| `--scope-ok` | claim, done | the quantifier-scope refusal: a sentence claiming more than its evidence covers | SENTENCE | `scope_basis` | yes, 30d (ADR-032 default expiry) | ADR-007 |
| `--paths-ok` | claim, done | the freehand watch budget: a watch set larger than the churn floor allows | SENTENCE | `paths_basis` | yes, 30d (ADR-032) | FAZA 3, ADR-055 |
| `--generated-ok` | claim, done | the refusal to watch a generated artifact | SENTENCE | `generated_ok_basis` | yes, like `--scope-ok` (ADR-032) | ADR-037 |
| `--evidence-exit-ok` | claim, done | the positive-claim exit gate: a positive claim whose probe exits non-zero | SENTENCE | `evidence_exit_basis` | no | ADR-035 |
| `--orphan-ok` | verdict, done | the tombstone citation gate: retracting while citations still point at the id | SENTENCE | `orphan_basis` | no | ADR-036 |
| `--refresh-evidence` | verdict | the ADR-051 refusal to advance a claim's anchor past a capsule that no longer reproduces (`policy.py`: *"Nothing was filed."*) | SENTENCE | `evidence_refresh.basis` | no | ADR-051 |
| `--single-run` | claim, done | **the G6 determinism double-run** — files without re-running the evidence command, "accepting false-divergence risk" | **nothing** | **nothing at all — see below** | no | G6 |
| `--ttl-days` | claim, done | **ADR-032's default override decay** — an explicit value suppresses the 30-day shelf life that would otherwise be stamped on a claim carrying `--scope-ok`, `--paths-ok` or `--generated-ok`, so the override judgement is never re-asked. ADR-032 calls it "the visible opt-out". On a claim with no override basis it lifts nothing; that condition is prose and is not checked | **a value** | `ttl_days`, and the ABSENCE of `ttl_default` | n/a — it is what suppresses a decay | ADR-032, G10 |
| `--duplicate-ok` | claim, done | the G8 near-duplicate refusal | **nothing** | `overridden_duplicates` (the predecessor ids — provenance, not rationale) | no | G8, ADR-031 |
| `--evidence-unsafe-ok` | claim, done | **the evidence screen** — files a claim whose evidence command the screen refused | **nothing** | `evidence.screened = false` | no | ADR-009 |
| `--accept-unsafe-ok` | issue, done | **TWO different refusals, one flag.** On `issue` it lifts the ADR-014 *screen*: an `--accept-cmd` the allowlist rejects is refused, and this files it anyway. On `done` it lifts *execution*: a stored oracle that is unscreened will not be run, and this closes the item without running it. The first admits an unchecked oracle; the second never learns whether the finish line was crossed | **nothing** | `accept.screened = false` on the filing; `accept.executed = false` additionally on the close. Measured 2026-08-25: 5 records and 2 records, and the second set is a strict SUBSET of the first, so the flag's population is 5 — never 7 | no | ADR-014 |

## What is checked, and what is not
 

`instruments/waiver-index.py` sweeps this table against the CLI, and it does
**not** scope itself to a naming convention. It used to, and the scoping was
wrong twice in this one file: `--refresh-evidence` lifts a hard ADR-051
refusal and has no `-ok` suffix, and `--single-run` has neither an `-ok`
suffix nor a sentence. A reverse check that can only see one spelling is a
grep wearing the argument for one.

- **forward** — every flag in a row is accepted by the parser, on the verbs
  the row names, taking the argument the row declares. All three are checked.
- **reverse, and total** — **every** flag the parser accepts on any verb must
  be either a row here or an entry in `.truth/waiver-not-an-override` with a
  reason. A new flag of any shape fails this sweep until somebody has judged
  which side it is on. That judgement is written down, never inferred from a
  name.
- **mirror** — a declaration in the policy file for a flag the parser no
  longer accepts is itself a finding, as is a flag that appears on both sides.

The inventory is harvested by **running** `truth <verb> --help` for every verb
the CLI lists, reading the `options:` section and cross-checking it against
the usage line. A disagreement between the two is a finding: they come from
one parser, so it means this reader is wrong about at least one of them. A
regex over `cli.py` was rejected as a second implementation of the parser,
which drifts silently because both copies look right in isolation.

**Not checked, named rather than left blank:**

- **`gate it lifts`** — free prose. Nothing verifies that the gate named is
  the gate lifted, and the `--accept-unsafe-ok` row covers two different
  refusals on two verbs (`issue` files an unscreened oracle; `done` closes
  without running one).
- **`stamp on the record`** — nothing verifies the kernel writes that field.
- **`decays`** — nothing verifies the decay is implemented. Hand-checked
  2026-08-24: `gates.py` passes exactly `scope_basis`, `paths_basis` and
  `generated_ok_basis` to `override_decay`, and `DEFAULT_OVERRIDE_TTL_DAYS`
  is 30. Note the opt-out the column cannot express: an explicit `--ttl-days`
  suppresses the decay entirely (ADR-032), and this ledger already carries a
  scope override with a **3650-day** shelf life.
- **`governing record`** — nothing verifies the ADR says what the row says.

**The population is a count over HISTORY, not over live claims.** The sweep
parses every ledger record structurally — a dotted path, optionally with a
required value — and reports how many records carry each stamp. It does not
fold, so a retracted or superseded claim counts the same as a live one; the
active figures are roughly half. For sentence-bearing overrides on ACTIVE
claims, ask `instruments/semantic-audit.py`, which folds. For `--single-run`
there is no answer from either, and that is the point of naming it.
