# Measurement: fixture coupling in truth-canary.sh

Static measurement of how canary arms obtain their preconditions. Produced by a
subagent given the file and a measurement spec only — no hypotheses, no fix
suggestions — so the numbers are not a second pass by the same reader.

## Numbers

```
3797 lines · 128 families · 618 assertions · 5 sandboxes (TMP1..TMP5)

  22 families (17.2%) establish their own state (mkrepo / cd "$TMP...")
 106 families (82.8%) INHERIT whatever the previous family left

  19 shell variables assigned in one family and read in a later one
  86 families run with cwd=$TMP1   (counting by variable name suggests 2)
```

Variable leakage, sample: `CID_O` FAULT O→P · `CID_DEAD` B→J · `CID_H` H→K ·
`H64` B6→AN1 · `CID_R` L→R3 · `WK_STALE` R3→R9. Longest chains: FAULT C2 and
FAULT C4, three inherited variables each.

**The deepest coupling is not cwd.** No arm re-initialises the ledger it
inherits, so a family's precondition includes every prior family's writes to
`.truth/*.jsonl` — the state of the system under test accumulates across the
suite.

## What the suite already says about itself

The coupling is known and locally compensated, not overlooked:

- L626: *"The sandbox list has drifted by now (FAULT G appended `date`, FAULT
  E5 `sort`), so AL runs against a PRISTINE copy of the shipped default."*
- L373: *"The entry persists for the rest of the sandbox … so FAULT AL (the
  only later arm that runs doctor here) deliberately re-installs a pristine
  shipped allowlist."*
- L369: *"an inherited attestation records nothing … which is also what keeps
  the FAULT PA arms below honest."*

So inheritance is load-bearing in places and paid for by hand in others. That
distinction is nowhere declared.

## Consequence for IV&V

| property | state |
|---|---|
| test-case independence | absent for 82.8% of families |
| failure localisation | a red arm may be an earlier arm's residue |
| selective execution | not possible without changing what an arm means |
| coupling made explicit | file order **is** the dependency graph, undeclared |

## What follows — and what does not

**Blanket isolation would be wrong.** Union-merge, duplicate-id and
fold-confluence arms *require* accumulated history; restoring a pristine
checkpoint would destroy their subject. An earlier draft of this
recommendation proposed checkpoint/restore for all families and is withdrawn.

**Declare the fixture instead.** A family header states `[fixture: pristine]`
or `[fixture: accumulated]`; `arm-index` enforces the declaration exactly as it
already enforces the subject. Only that declaration says which families may be
isolated at all.

**An arm selector must come after the declaration, never before.** Applied to
82.8% inheriting families, `--arm` produces false green: an arm run alone
receives a different precondition than the same arm run in sequence.

## Method limits

- Static and lexical, therefore a **lower bound**. Coupling through global git
  config, `TRUTH_*` variables or the working directory is invisible to it.
- The dynamic measurement — each family alone versus in-suite — **cannot be run
  today**, because it needs the arm selector whose absence is the finding.
- Counting sandbox residency by variable name understates it badly; the figure
  above comes from a cwd-tracking pass the measuring agent added on its own
  initiative after noticing the specified measure was near-meaningless.
