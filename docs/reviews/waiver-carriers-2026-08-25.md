# The waiver register was a mis-scoped partition, and it was mine

Operator finding, 2026-08-25:

> You found that a `<path>#<selector>` entry is exempt from both budgets, and
> that the bypass is carried by PATH SYNTAX, not by a flag — so no row can
> hold it and the sweep cannot see it. You wrote "Recorded". It is not in
> `docs/waivers.md`.

Correct, and worse than stated. The escape was written into
`.truth/waiver-not-an-override` under `--paths` — **the file for things that
are NOT overrides**. A bypass filed in the complement of the register, while
the register's title read *"every gate in this system that can be lifted"*.

A partition whose domain is unstated reads as universal. The register was
total over FLAGS and titled over BYPASSES, one day after it was built to catch
exactly that shape elsewhere.

## The hunt, before the writing

The operator's instruction was to apply the move that found the selector —
grepping help text for bypass language rather than matching names — to
whatever else carries semantics in syntax rather than in a flag. It found more
than the selector.

### The environment is a larger escape surface than the flags

| name | lifts | admitted on | leaves |
|---|---|---|---|
| **`TRUTH_SELF_VERDICT`** | **G11 / ADR-010, the author-is-not-verifier refusal** — `=1` allows `agree` on a claim the same session filed | nothing | **nothing** |
| `TRUTH_BATTERY_NO_META` | **the battery meta-gate**, the gate that guards every other gate | nothing | nothing |
| `TRUTH_BATTERY_SCOPE` | every scope-guarded battery arm | a value | nothing |
| `TRUTH_ALLOW_NO_JSONSCHEMA` | the schema half of the record contract | nothing | nothing |
| `TRUTH_HUMAN` / `TRUTH_HUMAN_ACK` | G12's human-only tombstone gate, and its interactive half | nothing / a value | nothing |
| `TRUTH_NOW` | the clock — TTL expiry and ADR-016 fold order | a value | a `ts` indistinguishable from a real one |
| `TRUTH_SESSION` | not a refusal, the LEVER on one: the separation gate compares this string | a value | a `session` indistinguishable from a real one |

**`TRUTH_SELF_VERDICT` is the sharpest finding of the whole effort.** It lifts
the separation the paper's §8 item 1a calls the property most worth admiring
and cannot settle — and it is a flag nowhere, takes no sentence, stamps
nothing, and is deliberately absent from the refusal text. `shellio.py` says
why, about its sibling: *"an error message that names the bypass is an
instruction to a compliant agent."*

That reasoning is right, and it is precisely the argument that these belong in
a **register**. A register is not a refusal. If a bypass may not be named
where it is refused, the only honest place left is a list — and there was no
list.

Two more, verified rather than asserted:

- `TRUTH_BATTERY_NO_META`'s own comment says it *"is not a skip flag for
  operators"*. Nothing enforces that sentence.
- `TRUTH_BATTERY_SCOPE`'s comment says *"Unknown scope always means MORE
  checking, never less"*. True of the `ALL` fallback, **false of a value set
  deliberately**: `touches()` greps the scope for each pattern, so
  `TRUTH_BATTERY_SCOPE=zzz` matches nothing and every guarded arm skips.
  Reproduced against the real `touches()` in isolation — three patterns, all
  RUN unset, all SKIP with `zzz`.

### `.truth/` is a third carrier, and it includes this register's own excuse file

Every policy, opt-out and baseline file there excuses findings that would
otherwise fail — eleven of the seventeen. Including
**`.truth/waiver-not-an-override`**: adding a line to it removes a carrier
from this register's scope. The escape surface's escape surface, unregistered.

And `.truth/evidence-allow`, `accept-allow`, `generated-paths` and
`citation-scope` are the **standing** forms of `--evidence-unsafe-ok`,
`--accept-unsafe-ok`, `--generated-ok` and the ADR-036 corpus: a line there
lifts the gate for every future filing rather than for one.

## The choice, and why

The operator offered two shapes and asked which and why.

**Chosen: widen the domain to bypasses, with a harvested reverse direction for
every carrier that has one, and the rest declared UNBOUNDED in the register
itself.** Not the cheaper "state the limit and enumerate by hand".

Three reasons, and the first is the only one that would settle it alone:

1. **Two of the new carriers ARE enumerable.** Environment names come from
   every `os.environ` read in the Python tree and every `${NAME:-}` idiom in
   the shell tree; policy files come from a directory listing. Where the
   reverse direction is available, refusing to build it is the same
   mis-scoping again — choosing the domain by what is convenient rather than
   by what exists.
2. **A hand-kept list is the defect, not the fix.** Everything found this week
   came from a list with no reverse check rotting: `--exit-ok` lived in three
   documents, `--refresh-evidence` was missing from a register asserting it
   held them all. Hand-listing fourteen environment names across two languages
   repeats it exactly, and the next `TRUTH_SELF_VERDICT` is invisible.
3. **The cheaper shape satisfies the constraint but buys nothing else.** Both
   shapes stop a reader concluding totality. Only one of them refuses the next
   unclassified carrier.

**What I did NOT do, because it cannot be done:** claim the register is total
over bypasses. `syntax`, `config` and `code` have no source to harvest. Rows
in those carriers are recorded from what somebody happened to find, and the
register says so in its own table, with an empty "reverse direction" cell.

## What satisfies the constraint

> a reader of `docs/waivers.md` ALONE must be unable to conclude that it
> covers every way a gate can be lifted.

Four things in the file itself, not in a commit message:

1. The **title** no longer quantifies over bypasses: *"the gates that can be
   lifted, by the carriers this register can enumerate."*
2. A section headed **"What this register covers, and what it provably
   cannot"**, opening with the literal **THIS REGISTER IS NOT TOTAL**, and a
   table giving each carrier its source and its reverse direction — three of
   which read **none**.
3. The **carrier column** in every row, so an `syntax` or `config` row is
   visibly of a kind the sweep cannot check.
4. The sweep's own output prints `unbounded carriers ... recorded by hand,
   from NO list` on every run.

**The limit statement is gated.** `waiver-index.py` fails if the marker is
absent, because a limit held by nothing is the first thing a redraft deletes —
this same effort lost a finding about six overdue gate-metrics reviews exactly
that way.

## What the register now measures

```
escape surface   32 waiver(s): 13 on a sentence, 5 on a value, 14 on NOTHING
flag inventory   50 harvested: 11 waivers, 39 declared not-an-override, 0 unclassified
env inventory    17 harvested:  8 waivers,  9 declared not-an-override, 0 unclassified
file inventory   17 harvested: 11 waivers,  6 declared not-an-override, 0 unclassified
unbounded        2 recorded by hand, from NO list: <path>#<selector>, core.hooksPath
population       NOT COUNTABLE (23 of 32)
```

**Twenty-three of thirty-two waivers leave no countable trace.** Nine are
visible in the ledger. That is the honest shape of the escape surface, and it
is why every population figure in ADR-059 is a lower bound.

### A defect I introduced and caught in my own output

The first version counted every backticked field in the `stamp` column. It
reported **`ttl_days` 268** on a ledger of 268 claims, and `evidence_paths`
268 — measuring the ledger and calling it the escape surface. `session` and
`ts` the same. A wrong population is worse than a missing one, because it
reads as a measurement. Rows whose stamp cannot separate the waiver's use from
ordinary traffic now carry the literal `NOT COUNTABLE` and no number is
printed for them.

A second one, same class, caught by the sweep on itself: the per-row FAIL mark
was a substring search over every failure line, so the row for
`.truth/waiver-not-an-override` showed FAIL whenever any message merely
*named* that file. Name-scoped now — the same defect as reading the
`admitted on` column by substring, which an adversarial review had already
found once.

## Gate

Eleven new checks, each disabled in turn with an arm going red, the instrument
restored byte-identically (`a91b1eff…`):

| check disabled | arm |
|---|---|
| env harvest, Python reads | `harvests_every_carrier_it_claims_to` |
| env harvest, shell reads | `harvests_every_carrier_it_claims_to` |
| the shell-local filter | `harvests_every_carrier_it_claims_to` |
| policy-file harvest | every waiver arm |
| forward: a row naming an env name nothing reads | `harvests_every_carrier_it_claims_to` |
| the LIMIT_MARKER gate | `requires_the_register_to_state_its_own_limit` |
| carrier validity (a typo bought the exemption) | `records_unbounded_carriers_without_checking_them` |
| namespaced policy keys | `policy_keys_name_their_carrier` |
| unbounded carrier used as an excuse namespace | `policy_keys_name_their_carrier` |
| the NOT COUNTABLE convention | `refuses_to_print_a_population_it_cannot_take` |

**One probe was mis-aimed and reported STILL GREEN**, and the fixture was the
reason: my throwaway `--ttl-days` row had a stamp cell with no backticked
field, so disabling the convention changed nothing. The real shape is a marker
*and* a field (`NOT COUNTABLE — \`ttl_days\` is on every claim`). With the
fixture corrected, the check goes red. An arm whose fixture cannot express the
defect is not an arm.

The harvest **over-reports rather than under-reports**, which is the direction
a safety reading must fail in: three shell locals and two test-fixture string
literals are classified by hand as not-inherited, and the policy file says why.

## Standing state

```
python3 instruments/waiver-index.py     exit 0   32 waivers over 6 carriers
python3 instruments/register-index.py   exit 1   the standing ADR-062 ruling
python3 instruments/arm-index.py        exit 0
bash scripts/fact-health.sh             exit 0
bash template/scripts/doc-health.sh     exit 0
bash scripts/gate-reachability.sh       exit 0
.venv/bin/python .../test-integrations.py   Ran 55 -- OK
.venv/bin/python .../test-truth-core.py     Ran 538 -- OK
```

Item 0b stays **DECLARED**. This change widens what membership covers; it does
not touch the four content columns, which are still held by reading.

## What is still not covered, stated so nobody reads silence as coverage

- **`syntax`, `config`, `code` are unbounded.** Two instances are recorded.
  There is no reason to believe they are the only two.
- **The shell env harvest is one idiom.** `${NAME:-}`, `${NAME:?}` and
  `env NAME=`. A bare `$NAME` read of an inherited variable is missed.
- **Non-`.truth/` policy files are not harvested** — `.claude/settings.json`,
  `.githooks/`, `copier.yml` all carry behaviour that can be turned off.
- **`--single-run` still writes nothing**, and now so do seven environment
  carriers. More than two thirds of the escape surface is invisible in the
  ledger by construction, not by oversight.
