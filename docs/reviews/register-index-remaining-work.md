# Register index — what is left to finish

The change is **uncommitted, in the working tree**, with its adversarial review
beside it in `register-index-review-2026-08-24.md`. Two of the ten defects that
review found are fixed; **eight remain**. Read the review first — it carries the
reproduction command for each.

## Fixed, and demonstrated

| # | defect | proof |
|---|---|---|
| 1 | a malformed table row was silently dropped, un-administering its register — the same nine-sources-four-read shape this instrument exists to catch | a sixth column on the `arms` row now yields `exit 1` and `the index row for 'arms' has 6 columns, not the five its header declares`; restored byte-identically |
| 3 | `--record-baseline` fail-opened over a broken index, blessing the whole corpus at exit 0 having read no register | the ADR-042 guards now precede the record branch; mangling every row and recording gives **exit 8**, `read ZERO register rows` |

At rest the sweep now exits 1 with exactly one failure: the true roadmap
currency gap. `doc-health` and `pre-commit` still pass.

## Remaining, in the order I would take them

**First, because it decides the shape of the rest**

- **#5 — check (b) is the wrong measure, not a buggy one.** It fails the
  roadmap for something `docs/registers.md` itself documents as correct: the
  roadmap is a history log citing ids that were live when written. The only
  green path is gameable — appending `ADR-061` to the roadmap turns it green
  with no review. Baselining the 28-gap would freeze a wrong measure and is
  **not** the fix. Two real options, both already argued in the item-0 section
  of `mechanism-layers-brief-2026-08-24.md`: measure currency by something
  other than a cited token, or stop checking the roadmap and **generate** it
  from the ADRs, as consolidated law is generated from its amending acts.

**Then the fail-open family — the same class as #1 and #3**

- **#2** a location cell with no backticks yields zero locations and prints `OK`.
- **#4** `highest_adr_file` degrades silently when a directory is missing, so
  the currency gap *shrinks* after a real regression.
- **#7** absolute and `../` paths are accepted; check (a) is satisfiable by any
  path on the machine.
- **#9** an unreadable input raises a traceback and exits 1, conflated with
  findings.

**Then the honesty gaps**

- **#6** column 5, `currency evidence` — the file's stated reason to exist — is
  asserted and never swept. It names ten backticked paths nothing verifies.
- **#8** the index sits outside every sweep it describes: absent from
  doc-health, `.truth/citation-scope`, `gate-metrics.md`,
  `gate-reachability.sh`. Its docstring says `Gate: NONE yet` while the
  markdown asserts it "is swept like any other register" — **the ISO/IEC 11179
  claim is false as shipped** and must either become true or be removed.
- **#10** `sweep(baseline)` never uses its parameter.

## Two operator rulings the sweep cannot make

- Whether the 25 baselined documents genuinely belong to no register.
- Whether a threshold of 5 means anything, given #5.

## The rule this work is judged by

ADR-061: an item is DONE when a gate exists that can go red for its named
reason **and someone has demonstrated it going red**. Both fixes above were
demonstrated. Nothing here is DONE until the same is true of it.
