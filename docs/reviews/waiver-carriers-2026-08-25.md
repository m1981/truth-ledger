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

**No figure here is authoritative.** Read them off
`python3 instruments/waiver-index.py`; this section is dated, and the counts
below were true on 2026-08-26 after the operator round that followed the
adversarial review.

```
escape surface   36 waiver(s): 13 on a sentence, 6 on a value, 17 on NOTHING
flag inventory   50 harvested: 11 waivers, 39 declared not-an-override, 0 unclassified
env  inventory   17 harvested:  9 waivers,  8 declared not-an-override, 0 unclassified
file inventory   17 harvested: 11 waivers,  6 declared not-an-override, 0 unclassified
unbounded         5 recorded by hand, from NO list
population       NOT COUNTABLE (15 of 36)
```

**The first version of this record said 32 waivers and 23 not-countable**, and
it stayed on disk while the register moved to 36 and 15. That divergence — a
record describing a register it no longer matched — is the class ADR-060
exists for, found by the operator against this file. It is corrected here and
the counts now carry the date and the pointer, rather than standing as facts.

**The flag half specifically**: eleven flag waivers, six on a sentence, one on
a value, four on nothing. ADR-059 said "SIX of the ten" and the six is right;
the ten became eleven when `--ttl-days` moved into the register.

**The ledger figures did NOT move**: 23 records carry an override sentence, 28
carry an override with none, the two sets disjoint. Re-measured 2026-08-26 by
ADR-059's counting rule. Those count records in the LEDGER, and the carriers
added since — environment, files, syntax, config — write nothing there, which
is why the register grew by 20 rows while these two numbers did not change at
all. That is the finding, not a discrepancy.

## The assertion audit, and what it did not touch

The operator named a defect class from a single instance: an **inverted arm**,
whose signature is that the assertion message describes an OBSERVATION rather
than a REQUIREMENT. `assertEqual(local.returncode, 0, "a shell local was
reported as inherited")` is a sentence about what is; the requirement would
read "an inherited variable must not be classified as local".

Their instruction was that assuming it is the only one is the generalisation
this repository has already fallen for. It was, and the sweep found something
worse than a second instance.

**Measured 2026-08-26** over the 34 methods this work added
(`test_register_index_*`, `test_waiver_index_*`,
`test_every_instrument_is_classified`), counting assertions that demand a PASS
— `returncode, 0`, `assertNotIn`, `assertNotRegex` — because a strict
assertion that fires wrongly is loud while a permissive one that pins a defect
is silent:

| | permissive assertions | stating a requirement |
|---|---|---|
| this work's arms | **47** | **46** |
| pre-existing arms in the same file | **48** | **0** |

**Only one genuine inversion was found**, the one the operator named, already
fixed. The sweep's real yield is that the requirement was UNSTATED in most of
them — and an assertion with no stated requirement cannot be audited for
inversion at all, so "it is the only one" was not provable. That is why the
answer was to state all of them rather than to search harder.

**I first reported this number to the operator as 61. It is 47.** The 61 came
from a range that swept in pre-existing tests around it. The corrected
measurement is above; the wrong one existed only in a chat message, which is
the second half of the same defect — see below.

### The 47th, and the 48 not touched — neither is a silent limit

- **One of 47 has no "must" sentence**: `assertIn("path(s) checked across", …)`
  and its siblings assert a substring of expected output rather than a pass
  condition. The requirement is carried by the string itself. Left as is.
- **The 48 pre-existing permissive assertions in `test-integrations.py` were
  NOT touched.** They are outside this work's arms, and rewriting another
  change's assertions would put unreviewed edits into a diff about waivers.
  They are a **backlog with a number**, not an omission: any one of them may
  be inverted and none of them says what it requires. That is the honest state
  and it is written here because a limit nobody states is exactly what this
  work spent two rounds removing.

**No mechanism enforces requirement-form messages.** The signature is
detectable by reading and by nothing else; a lint over assertion prose was
considered and rejected as grading English, which is the ADR-059 line between
L1 and L2. So this is DECLARED, and the number above is the measurement a
later reader can check it against.

## ADR-062 rule 4, broken again, by me, one layer further out

The rule says a finding that lives only in a task notification cannot be
cited, because there is nothing for a later reader to check it against. It was
written in this session, after a phantom citation in `AGENTS.md`.

**The assertion measurement lived only in a chat message for a full round.**
`grep -c permissive docs/reviews/waiver-carriers-2026-08-25.md` returned 0
while the number was being reported and acted on — and the number was wrong.
The operator caught it with that grep.

The lesson is not "persist more". It is that **a measurement reported in prose
and not written to disk is not merely unverifiable — it decays before anyone
can check it**, and the wrongness here was of exactly the kind a written
record would have exposed: a range that quietly included files it should not.

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

## Standing state, 2026-08-26

```
python3 instruments/waiver-index.py     exit 0   36 waivers over 6 carriers
python3 instruments/register-index.py   exit 0   ALL THREE failures resolved
python3 instruments/arm-index.py        exit 0
python3 instruments/semantic-audit.py   exit 0
bash scripts/fact-health.sh             exit 0
bash template/scripts/doc-health.sh     exit 0
bash scripts/gate-reachability.sh       exit 0
bash .githooks/pre-commit               exit 0
.venv/bin/python .../test-integrations.py   Ran 63 -- OK
.venv/bin/python .../test-truth-core.py     Ran 538 -- OK
```

`register-index` reached exit 0 for the first time in this effort. All three
of its failures were this work's own, and all three were rulings an agent
made — recorded with their actor and their reversal condition in
`docs/governance/operator-actions-2026-08.md`, because a resolved failure that
does not say who resolved it reads as if the repository had always been clean.

Item 0b stays **DECLARED**. This change widened what membership covers; it did
not touch the four content columns, which are still held by reading, and the
operator round added a fifth thing held by reading: nothing enforces that an
assertion states a requirement.

## What is still not covered, stated so nobody reads silence as coverage

- **`syntax`, `config`, `code` are unbounded.** FIVE instances are recorded —
  `<path>#<selector>`, `core.hooksPath`, `git push --no-verify`,
  `.claude/settings.json`, `scripts/truth-whisper.deny`. There is no reason to
  believe five is what exists.
- **The shell env harvest is three idioms**: `${NAME:-}`, `${NAME:?}` and
  `env NAME=`. A bare `$NAME` read of an inherited variable is missed.
  Extensionless files are read by shebang, so the CLI entry point is covered;
  a Python file with neither shebang nor suffix is not.
- **The `file` carrier is scoped to `.truth/`.** Policy files elsewhere are
  recorded under `config`, which has no reverse direction.
- **Assertion messages are not enforced** — 48 pre-existing permissive
  assertions in the same file state no requirement, and any of them may be
  inverted. Counted, named, untouched.
- **`--single-run` writes nothing**, and neither do the environment and config
  carriers: **15 of 36 waivers leave no countable trace**. Two thirds of the
  escape surface used to be reported that way; the criterion above cut it to
  15 by counting file entries and refining one predicate. What remains is
  invisible by construction, not by oversight.
